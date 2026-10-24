#!/usr/bin/env bash
# 同时启动后端 (uvicorn) 与前端 (vite)，按 Ctrl+C 一起退出。
# 用法：在项目根目录执行 ./scripts/dev.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/smarthome-api"
WEB_DIR="$ROOT_DIR/smarthome-web"

if [[ ! -d "$API_DIR/.venv" ]]; then
  echo "[dev.sh] 未检测到 $API_DIR/.venv，先创建并安装依赖..."
  python3 -m venv "$API_DIR/.venv"
  # shellcheck disable=SC1091
  source "$API_DIR/.venv/bin/activate"
  pip install -r "$API_DIR/requirements.txt"
fi

# shellcheck disable=SC1091
source "$API_DIR/.venv/bin/activate"

cleanup() {
  echo ""
  echo "[dev.sh] 收到退出信号，正在终止子进程..."
  if [[ -n "${BACKEND_PID:-}" ]]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [[ -n "${FRONTEND_PID:-}" ]]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "[dev.sh] 启动后端: uvicorn app.main:app --reload --port 8000"
(
  cd "$API_DIR"
  uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "[dev.sh] 启动前端: npm run dev (smarthome-web)"
(
  cd "$WEB_DIR"
  npm run dev
) &
FRONTEND_PID=$!

echo "[dev.sh] 后端 PID=$BACKEND_PID  前端 PID=$FRONTEND_PID"
echo "[dev.sh] 按 Ctrl+C 一起停止"

wait