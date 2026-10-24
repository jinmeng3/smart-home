"""前端 → 后端 API 端到端探测（in-process 版，不依赖外部 uvicorn）。

策略：
  1. 在同一进程内用内存 SQLite + 内存 FastAPI（TestClient）启动后端
  2. 注册 probe 用户，建家庭/房间/设备/AI 模型（fixture）
  3. 解析前端 src/api/*.ts 调用的所有 (method, path)
  4. 用前端代码相同的 URL + 同样的最小 body 调用，验证每个端点响应

运行：smart-home-web/.venv/Scripts/python scripts/probe-api-routes.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# 复用 serve_for_probe.py 的 fixture 准备流程
ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
API_DIR = ROOT / "src" / "api"

# 必须先于 import app.* 设置环境变量
os.environ.setdefault("PRODUCTION_MODE", "false")
os.environ.setdefault("FUNNEL_SEMANTIC_ENABLED", "false")
os.environ.setdefault("UPLOAD_DIR", "app/uploads-probe2")
os.environ.setdefault("AUDIT_DIR", "agent_audit-probe2")

# 把 smarthome-api 加进 sys.path
sys.path.insert(0, str(PROJECT_ROOT / "smarthome-api"))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import session as db_session  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.api import deps as api_deps  # noqa: E402
from app.core import config as config_mod  # noqa: E402


def setup_backend():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session.engine = engine
    db_session.SessionLocal = factory

    def _get_db_override():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    api_deps.get_db = _get_db_override

    Path("app/uploads-probe2").mkdir(parents=True, exist_ok=True)
    Path("agent_audit-probe2").mkdir(parents=True, exist_ok=True)

    settings = config_mod.Settings()
    settings.upload_dir = "app/uploads-probe2"
    settings.audit_dir = "agent_audit-probe2"
    app.dependency_overrides[config_mod.get_settings] = lambda: settings
    try:
        config_mod.get_settings.cache_clear()
    except AttributeError:
        pass

    # 触发一次路由解析
    with TestClient(app) as c:
        c.get("/openapi.json")

    return engine


def make_fixture(client: TestClient):
    """在测试库里预创建用户/家庭/房间/设备/AI 模型/会话。"""
    c = client
    # 注册
    c.post("/api/auth/register", json={"username": "probe", "email": "probe@example.com", "password": "ProbeP@ss1"})
    # 登录（生成 SecurityDevice）
    r = c.post("/api/auth/login", json={"account": "probe@example.com", "password": "ProbeP@ss1"})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    user_id = r.json()["data"]["user"]["id"]
    h = {"Authorization": f"Bearer {token}"}

    hh = c.post("/api/households", headers=h, json={"name": "Probe Home", "timezone": "Asia/Shanghai"})
    household_id = hh.json()["data"]["id"]

    room = c.post("/api/rooms", headers=h, json={"name": "Probe Room", "floor": "1F", "room_type": "living_room"})
    room_id = room.json()["data"]["id"]

    device = c.post("/api/devices", headers=h, json={"name": "Probe Lamp", "room": "Probe Room", "type": "light", "brand": "p", "connection": "MQTT", "device_id": "p1"})
    device_id = device.json()["data"]["id"]

    ai = c.post("/api/ai_model/model", headers=h, json={"name": "probe-model", "provider": "openai", "api": "openai-completions", "apiEndpoint": "https://api.openai.com/v1", "apiKey": "sk", "parameters": {"model": "gpt-4o-mini"}})
    ai_model_id = ai.json()["data"]["id"] if ai.status_code in (200, 201) else None

    chat = c.post("/api/chat/sessions", headers=h, json={"title": "probe"})
    chat_session_id = chat.json()["data"]["id"] if chat.status_code in (200, 201) else None

    return {
        "base_url": "http://test",
        "user": {"id": user_id, "email": "probe@example.com", "password": "ProbeP@ss1"},
        "token": token,
        "headers": h,
        "household_id": household_id,
        "room_id": room_id,
        "device_id": device_id,
        "ai_model_id": ai_model_id,
        "chat_session_id": chat_session_id,
    }


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def extract_backend_endpoints(spec):
    out = {}
    for path, methods in (spec.get("paths") or {}).items():
        m = {}
        for method, op in (methods or {}).items():
            if method.lower() not in HTTP_METHODS:
                continue
            params = [p["name"] for p in (op.get("parameters") or []) if p.get("in") == "path"]
            m[method.upper()] = {"params": params}
        out[path] = m
    return out


def path_to_regex(template: str) -> re.Pattern:
    # 手写转义：只转义 regex 特殊字符，保留 { 和 }
    sanitized = re.sub(r"\{[^}]+\}", "___PARAM___", template)
    escaped_chars = r"\.+*?()|^$"
    escaped = "".join("" if c == " " else ("\\" + c if c in escaped_chars else c) for c in sanitized)
    escaped = escaped.replace("___PARAM___", "[^/]+")
    return re.compile("^" + escaped + "$")


def extract_frontend_calls():
    files = sorted(API_DIR.glob("*.ts"))
    files = [f for f in files if f.name != "client.ts" and not f.name.startswith("generated")]
    path_re = re.compile(r"""["'`](\/api\/[^"'`]+)["'`]""")
    method_re = re.compile(r"""method:\s*["'`](GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)["'`]""", re.I)
    calls = []
    for f in files:
        raw = f.read_text(encoding="utf-8")
        sanitized = re.sub(r"\$\{[^}]*\?[\s\S]*?\}", "", raw)
        sanitized = re.sub(r"\$\{[\s\S]*?\}", "{*}", sanitized)
        method_positions = [(m.start(), m.group(1).upper()) for m in method_re.finditer(sanitized)]
        for m in path_re.finditer(sanitized):
            raw_path = m.group(1).split("?")[0]
            ctx_after = sanitized[m.end(): m.end() + 300]
            hint = method_re.search(ctx_after)
            method = hint.group(1).upper() if hint else None
            if not method:
                nearest = None
                for pos, meth in method_positions:
                    if pos > m.start():
                        break
                    nearest = meth
                method = nearest or "GET"
            calls.append({"file": f.name, "path": raw_path, "method": method})
    return calls


def fill_path(template: str, fixture: dict) -> str:
    p = template
    subs = {
        "household_id": fixture["household_id"], "householdId": fixture["household_id"],
        "room_id": fixture["room_id"], "roomId": fixture["room_id"],
        "device_id": fixture["device_id"], "deviceId": fixture["device_id"],
        "session_id": fixture["chat_session_id"] or 1, "sessionId": fixture["chat_session_id"] or 1,
        "model_id": fixture["ai_model_id"] or 1, "scene_id": 1, "sceneId": 1,
        "automation_id": 1, "membership_id": 1, "approval_id": "appr_test_001",
        "task_id": "task_test_001", "inspection_id": 1, "job_id": 1,
        "execution_id": 1, "template_id": 1, "schedule_date": "2026-09-02", "id": 1,
    }
    def repl(m):
        return str(subs.get(m.group(1), 1))
    p = re.sub(r"\{([^}]+)\}", repl, p)
    p = re.sub(r"\{\*[^}]*\}", "1", p)
    return p


def build_body(path: str, method: str, fixture: dict):
    if method in ("GET", "DELETE", "HEAD"):
        return None
    if path == "/api/auth/login":
        return {"account": fixture["user"]["email"], "password": fixture["user"]["password"]}
    if path == "/api/auth/register":
        return {"username": "probe2", "email": "probe2@example.com", "password": "ProbeP@ss1"}
    if path.endswith("/decisions"):
        return {"householdId": fixture["household_id"], "approvalId": "appr_test", "decision": "approve"}
    if path == "/api/chat/sessions" and method == "POST":
        return {"title": "probe"}
    if path.endswith("/mode"):
        return {"mode": "chat"}
    if path.endswith("/model"):
        return {"modelName": "probe-model"}
    if path == "/api/ai_model/ping":
        return {"name": "p", "provider": "openai", "api": "openai-completions", "apiEndpoint": "https://api.openai.com/v1", "apiKey": "sk", "parameters": {"model": "gpt-4o-mini"}}
    if path == "/api/ai_model/model" and method == "POST":
        return {"name": "p", "provider": "openai", "api": "openai-completions", "apiEndpoint": "https://api.openai.com/v1", "apiKey": "sk", "parameters": {"model": "gpt-4o-mini"}}
    if path == "/api/rooms" and method == "POST":
        return {"name": "p2", "floor": "1F", "room_type": "bedroom"}
    if re.search(r"^/api/rooms/[^/]+$", path) and method == "PATCH":
        return {"name": f"r-{int(time.time()*1000)%100000}"}
    if path.endswith("/quick-action"):
        return {"action": "toggle"}
    if path == "/api/devices" and method == "POST":
        return {"name": "p2", "room": "Probe Room", "type": "light", "brand": "p", "connection": "MQTT", "device_id": "p2"}
    if path == "/api/devices/sync":
        return {"platform": "mock"}
    if path == "/api/devices/groups/assign":
        return {"group": "g", "deviceIds": [1]}
    if path == "/api/households" and method == "POST":
        return {"name": "p2", "timezone": "Asia/Shanghai"}
    if path in ("/api/scenes", "/api/scenes/drafts") and method == "POST":
        return {"name": "p2", "triggerType": "manual"}
    if path.endswith("/order") and method == "PATCH":
        return {"items": [{"id": 1, "sortOrder": 1}]}
    if path.endswith("/enabled") and method == "PATCH":
        return {"enabled": True}
    if path.endswith("/execute") and method == "POST" and "/scenes" in path:
        return {"confirmHighRisk": False, "source": "manual"}
    if path.endswith("/copy") and method == "POST":
        return {"name": "p2-copy"}
    if path.endswith("/preview") and method == "POST":
        return {"source": "manual"}
    if path == "/api/scenes/batch/enabled":
        return {"sceneIds": [1], "enabled": True}
    if path == "/api/scenes/batch/schedule":
        return {"sceneIds": [1], "triggerType": "manual", "triggerLabel": "p"}
    if re.search(r"/api/scenes/templates/[^/]+/use$", path):
        return {"name": "p", "enabled": True, "deviceMapping": {"t1": 1}}
    if path == "/api/scenes" and method == "PUT":
        return {"name": "p2", "triggerType": "manual"}
    if re.search(r"^/api/households/[^/]+/automations$", path) and method == "POST":
        return {"name": "p", "triggers": [], "actions": []}
    if path.endswith("/enabled") and method == "PATCH" and "/automations/" in path:
        return {"enabled": True}
    if path.endswith("/execute") and method == "POST" and "/automations/" in path:
        return {"source": "manual"}
    if path == "/api/automations/batch-enable":
        return {"ruleIds": [1]}
    if path == "/api/automations/schedules/batch":
        return {"ruleIds": [1], "timezone": "Asia/Shanghai", "time": "08:00", "weekdays": [1, 2, 3]}
    if path == "/api/automations/templates/ai":
        return {"deviceSummary": {"online": 1, "offline": 0, "byType": {}}, "count": 1}
    if re.search(r"^/api/households/[^/]+/members$", path) and method == "POST":
        return {"email": "p3@example.com", "role": "member"}
    if re.search(r"/members/[^/]+$", path) and method == "PATCH":
        return {"role": "member"}
    if re.search(r"^/api/rooms/[^/]+/devices$", path) and method == "PUT":
        return {"devices": [{"deviceId": 1, "group": "g", "favorite": False, "sortOrder": 0}]}
    if re.search(r"/devices/[^/]+$", path) and method == "PATCH" and not path.endswith("/device"):
        return {"group": "g", "favorite": False, "sortOrder": 0}
    if path.endswith("/device") and method == "PATCH":
        return {"device_id": 1, "status": "online"}
    if re.search(r"/scenes/[^/]+/execute$", path) and method == "POST":
        return {"scope": "room"}
    if re.search(r"/scenes/[^/]+/preview$", path) and method == "POST":
        return None
    if path == "/api/overview/modes/execute":
        return {"mode": "home", "roomIds": [], "runAutomations": False, "idempotencyKey": "k1"}
    if path == "/api/inspections" and method == "POST":
        return {"scope": "all", "checks": []}
    if re.search(r"^/api/schedules/", path):
        return {"enabled": True, "repeatDays": [1, 2, 3], "targets": {}, "items": [], "version": 1}
    if path == "/api/device-sync-jobs" and method == "POST":
        return {"scope": "all", "sources": ["mock"], "options": {"force": False}, "idempotencyKey": "k1"}
    if path == "/api/settings/suggestions/ai":
        return {"snapshot": {"appearance": {}, "aiAssistant": {}}}
    if path == "/api/agent/runs":
        return {"sessionId": fixture["chat_session_id"] or 1, "householdId": fixture["household_id"], "message": "ping"}
    if path.endswith("/regenerate"):
        return {"householdId": fixture["household_id"], "targetMessageId": 1}
    if path.endswith("/cancel-pending"):
        return {"household_id": fixture["household_id"], "approval_id": "appr_test"}
    if path == "/api/chat/completions":
        return {"model": "probe-model", "messages": [{"role": "user", "content": "hi"}]}
    if path == "/api/account/me" and method == "PATCH":
        return {"name": "p2"}
    if path == "/api/account/me/preferences" and method == "PUT":
        return {"appearance": {}, "aiAssistant": {}, "notifications": {}, "security": {}, "backup": {}}
    if path == "/api/account/me/security/logs":
        return {"title": "p", "detail": "p"}
    if re.search(r"/security/devices/[^/]+$", path) and method == "PATCH":
        return {"trusted": True}
    return {}


def main():
    print("[probe] 启动 in-process 后端 ...")
    setup_backend()
    # 强制从干净状态建 fixture
    with TestClient(app) as c:
        fixture = make_fixture(c)
    print(f"[probe] fixture: user={fixture['user']['id']} household={fixture['household_id']} room={fixture['room_id']} device={fixture['device_id']} ai_model={fixture['ai_model_id']} chat={fixture['chat_session_id']}")

    # 拿到 OpenAPI（用 app.openapi() 直接拿）
    spec = app.openapi()
    backend = extract_backend_endpoints(spec)
    print(f"[probe] 后端 OpenAPI paths: {len(backend)}  累计端点: {sum(len(v) for v in backend.values())}")

    frontend = extract_frontend_calls()
    print(f"[probe] 前端调用点: {len(frontend)}")

    # ===== [1] 路径覆盖 =====
    print("\n[1] 路径覆盖（前端 vs 后端 OpenAPI）")
    orphan = []
    for c in frontend:
        matched = any(path_to_regex(bp).match(c["path"]) for bp in backend)
        if not matched:
            orphan.append(c)
    if not orphan:
        print(f"  [OK] 全部命中（{len(frontend)} 个调用）")
    else:
        print(f"  [ERR] 前端调用但后端无对应 ({len(orphan)}):")
        for c in orphan[:20]:
            print(f"     - {c['method']} {c['path']}  ({c['file']})")

    # ===== [2] 真实探测 =====
    print("\n[2] 真实请求探测（去重后调后端）")
    uniq = {}
    for c in frontend:
        k = f"{c['method']} {c['path']}"
        if k not in uniq:
            uniq[k] = c
    print(f"  前端去重后端点数: {len(uniq)}")

    results = []
    with TestClient(app) as c:
        # 重新登录拿 token（因为新 TestClient 实例可能丢了 session，fixture 里的 token 仍是合法 JWT）
        for call in uniq.values():
            url = fill_path(call["path"], fixture)
            body = build_body(call["path"], call["method"], fixture)
            t0 = time.time()
            try:
                if call["method"] == "GET":
                    r = c.get(url, headers=fixture["headers"])
                elif call["method"] == "POST":
                    r = c.post(url, headers=fixture["headers"], json=body) if body is not None else c.post(url, headers=fixture["headers"])
                elif call["method"] == "PUT":
                    r = c.put(url, headers=fixture["headers"], json=body)
                elif call["method"] == "PATCH":
                    r = c.patch(url, headers=fixture["headers"], json=body)
                elif call["method"] == "DELETE":
                    r = c.delete(url, headers=fixture["headers"])
                else:
                    results.append({**call, "url": url, "status": 0, "ms": 0, "err": "unsupported method"})
                    continue
                status = r.status_code
                err = None
            except Exception as e:
                status = 0
                err = str(e)[:80]
            ms = int((time.time() - t0) * 1000)
            results.append({**call, "url": url, "status": status, "ms": ms, "err": err})
            tag = "OK" if status and status < 500 else ("5xx" if status and status >= 500 else ("4xx" if status else "ERR"))
            status_str = str(status) if status else (err or "?")
            print(f"  {tag:4} {call['method']:6} {url:80}  {status_str}  {ms}ms")

    ok = sum(1 for r in results if r["status"] and r["status"] < 500)
    e4 = sum(1 for r in results if r["status"] and 400 <= r["status"] < 500)
    e5 = sum(1 for r in results if r["status"] and r["status"] >= 500)
    ne = sum(1 for r in results if not r["status"])
    print(f"\n  [OK] 成功（< 500）: {ok}")
    if e4: print(f"  [4xx] 鉴权/校验失败（预期内）: {e4}")
    if e5:
        print(f"  [5xx] 后端错误: {e5}")
        for r in results:
            if r["status"] and r["status"] >= 500:
                print(f"     {r['method']} {r['url']}  -> {r['status']}  ({r['file']})")
    if ne:
        print(f"  [ERR] 网络/异常: {ne}")
        for r in results:
            if not r["status"]:
                print(f"     {r['method']} {r['url']}  -> {r['err']}  ({r['file']})")

    print("\n[总结]")
    print(f"  路径覆盖: {'OK' if not orphan else 'FAIL'}")
    print(f"  真实请求: {'OK' if (e5 + ne) == 0 else 'FAIL'}  (5xx/网络错误 = {e5 + ne})")
    print(f"  4xx 通常是鉴权/参数校验失败，需要单独 review")

    sys.exit(0 if (not orphan and e5 == 0 and ne == 0) else 1)


if __name__ == "__main__":
    main()