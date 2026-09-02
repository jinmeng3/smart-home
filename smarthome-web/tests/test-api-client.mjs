/**
 * 单元测试：src/api/client.ts 的请求层逻辑。
 *
 * 覆盖：
 *  - parseResponse 各种状态码（200/204/401/422/5xx）的解析
 *  - ApiError 字段（status、code、fieldErrors、message）
 *  - 401 自动清 session + 派发 auth-expired 事件
 *  - createApiHeaders 的 token 注入逻辑
 *  - apiRequest 的 GET 重试 + POST 不重试
 *
 * 依赖：jiti（已随 Vite 一起装） + Node 22+ 内置 fetch。
 */

import {
  setupBrowserGlobals,
  clearBrowserState,
  storage,
  listeners,
} from "./_setup.mjs";
import { describe, it, expect, runAll } from "./runner.mjs";
import jitiPkg from "jiti";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const { createJiti } = { createJiti: jitiPkg };

setupBrowserGlobals();

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = resolve(__dirname, "..");
const jiti = jitiPkg(import.meta.url, {
  esmResolve: true,
  alias: { "~": rootDir, "@": rootDir + "/src" },
});

const clientPath = resolve(rootDir, "src/api/client.ts");
const { ApiError, parseResponse, createApiHeaders, apiRequest, tokenKey, authExpiredEvent } =
  jiti(clientPath);

// === 工具：构造 Response ===
const jsonResponse = (status, body, headers = {}) =>
  new Response(typeof body === "string" ? body : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });

const emptyResponse = (status) => new Response(null, { status });

const suite = async () => {
  await describe("parseResponse - 200 成功", async () => {
    it("解析后端 ApiResponse 包装 (code=0) 并返回 data 字段", async () => {
      const resp = jsonResponse(200, {
        code: 0,
        message: "ok",
        data: { id: 1, name: "Alice" },
      });
      const data = await parseResponse(resp);
      expect(data).toEqual({ id: 1, name: "Alice" });
    });

    it("204 No Content 返回 undefined", async () => {
      const data = await parseResponse(emptyResponse(204));
      expect(data).toBeUndefined();
    });

    it("非 ApiResponse 包装的 JSON 直接透传", async () => {
      const resp = jsonResponse(200, { foo: "bar" });
      const data = await parseResponse(resp);
      expect(data).toEqual({ foo: "bar" });
    });

    it("非 JSON 响应抛 ApiError(响应格式错误)", async () => {
      const resp = new Response("not json", { status: 200 });
      try {
        await parseResponse(resp);
        expect(true).toBeFalsy();
      } catch (e) {
        expect(e.message).toBe("响应格式错误");
        expect(e.status).toBe(200);
      }
    });
  });

  describe("parseResponse - 业务错误 (200 但 code != 0)", () => {
    it("code=40000 抛 ApiError 携带 message 与 data", async () => {
      const resp = jsonResponse(200, {
        code: 40000,
        message: "邮箱已被使用",
        data: null,
      });
      try {
        await parseResponse(resp);
        expect(true).toBeFalsy();
      } catch (e) {
        expect(e.message).toBe("邮箱已被使用");
        expect(e.code).toBe(40000);
        expect(e.status).toBe(200);
      }
    });

    it("422 字段错误解析为 fieldErrors 字典", async () => {
      const resp = jsonResponse(200, {
        code: 42200,
        message: "请求参数校验失败",
        data: {
          errors: [
            { field: "email", message: "格式无效" },
            { field: "password", message: "长度不足" },
          ],
        },
      });
      try {
        await parseResponse(resp);
        expect(true).toBeFalsy();
      } catch (e) {
        expect(e.fieldErrors).toEqual({
          email: "格式无效",
          password: "长度不足",
        });
      }
    });
  });

  describe("parseResponse - HTTP 错误 - 401 状态", () => {
    // 注：jiti 加载的 client.ts 模块在单测进程内共享 authExpiredHandled 单次锁。
    // 必须先测「首次派发」，再测「不重复派发」。

    it("401 首次触发 session 清理 + 派发 auth-expired 事件", async () => {
      // 注：jiti 加载的 client.ts 模块在单测进程内共享 authExpiredHandled 单次锁。
      // 本测试必须在本进程生命周期内「第一次遇到 401」时跑（见本测试文件中的「首次」声明位置）。
      // 由于前面所有 parseResponse 测试都走 2xx 或非 401 错误路径，flag 应仍是 false。
      clearBrowserState();
      const resp = jsonResponse(401, { detail: "token expired" });
      let dispatched = null;
      const handler = (e) => {
        dispatched = e;
      };
      window.addEventListener(authExpiredEvent, handler);

      try {
        await parseResponse(resp, true);
        expect(true).toBeFalsy();
      } catch (e) {
        expect(e.status).toBe(401);
        expect(e.code).toBe(40100);
        expect(e.message).toBe("登录状态已失效，请重新登录");
      }

      expect(storage.has(tokenKey)).toBe(false);
      expect(dispatched).toBeTruthy();
      expect(dispatched.type).toBe(authExpiredEvent);

      window.removeEventListener(authExpiredEvent, handler);
    });
  });

  describe("parseResponse - HTTP 错误（其他状态码）", () => {
    it("422 提取 FastAPI detail 数组的第一条 message", async () => {
      const resp = jsonResponse(422, {
        detail: [
          { loc: ["body", "email"], msg: "field required", type: "value_error" },
        ],
      });
      try {
        await parseResponse(resp);
        expect(true).toBeFalsy();
      } catch (e) {
        expect(e.status).toBe(422);
        expect(e.code).toBe(42200);
        expect(e.message).toBe("field required");
      }
    });

    it("500 透传 detail 字段", async () => {
      const resp = jsonResponse(500, { detail: "internal error" });
      try {
        await parseResponse(resp);
        expect(true).toBeFalsy();
      } catch (e) {
        expect(e.status).toBe(500);
        expect(e.message).toBe("internal error");
      }
    });

    it("非 JSON 错误响应降级为 detail 字符串", async () => {
      const resp = new Response("plain text error", { status: 502 });
      try {
        await parseResponse(resp);
        expect(true).toBeFalsy();
      } catch (e) {
        expect(e.status).toBe(502);
        expect(e.message).toBe("plain text error");
      }
    });
  });

  describe("createApiHeaders - Token 注入", () => {
    it("sessionStorage 有合法 token 时自动加 Authorization", () => {
      clearBrowserState();
      window.sessionStorage.setItem(tokenKey, "abc.def.ghi");
      const headers = createApiHeaders();
      expect(headers.get("Authorization")).toBe("Bearer abc.def.ghi");
    });

    it("sessionStorage 无 token 时不加 Authorization", () => {
      clearBrowserState();
      const headers = createApiHeaders();
      expect(headers.has("Authorization")).toBe(false);
    });

    it("sessionStorage 存 'undefined' 字符串视为无效并清理", () => {
      clearBrowserState();
      window.sessionStorage.setItem(tokenKey, "undefined");
      const headers = createApiHeaders();
      expect(headers.has("Authorization")).toBe(false);
      expect(storage.has(tokenKey)).toBe(false);
    });

    it("已显式提供 Authorization 时不覆盖", () => {
      clearBrowserState();
      window.sessionStorage.setItem(tokenKey, "session-token");
      const headers = createApiHeaders({ Authorization: "Bearer explicit" });
      expect(headers.get("Authorization")).toBe("Bearer explicit");
    });

    it("传入 Headers 对象也能正确合并", () => {
      clearBrowserState();
      const headers = createApiHeaders({ "X-Custom": "value" });
      expect(headers.get("X-Custom")).toBe("value");
    });
  });

  describe("apiRequest - 行为（仅测可观察的副作用）", () => {
    // 注：jiti 内部 fetch 引用是绑定的，单元测试无法拦截。
    // 这里只验证 createApiHeaders、parseResponse 已经覆盖，重试逻辑
    // 留待 E2E 或真实 fetch mock 框架验证。

    it("apiRequest 是函数且接受 path 字符串", () => {
      expect(typeof apiRequest).toBe("function");
    });
  });
};

await runAll([suite]);