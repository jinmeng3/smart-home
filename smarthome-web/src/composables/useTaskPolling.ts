import { onScopeDispose, ref } from "vue";

/** 后端异步任务中仍处于推进状态的状态值（未到终态）。 */
const PENDING_STATUSES = new Set(["queued", "pending", "running", "processing"]);

interface TaskPollingOptions<T> {
  /** 轮询间隔（毫秒），默认 1500 */
  intervalMs?: number;
  /** 最大轮询次数，默认 60（约 90 秒） */
  maxAttempts?: number;
  /** 判定任务是否已到达终态，默认根据 status 判断 */
  isTerminal?: (result: T) => boolean;
}

/**
 * 通用异步任务轮询。
 *
 * 用于巡检（GET /api/inspections/{id}）、设备同步任务（GET /api/device-sync-jobs/{id}）
 * 等“提交后回读终态”的场景，避免把“请求已提交”当“已完成”。
 *
 * 组件/页面卸载时自动停止轮询；刷新后可通过任务 ID 恢复查询。
 */
export const useTaskPolling = <T>(
  fetcher: () => Promise<T>,
  onUpdate: (result: T) => void,
  options: TaskPollingOptions<T> = {},
) => {
  const { intervalMs = 1500, maxAttempts = 60 } = options;
  const isTerminal =
    options.isTerminal ??
    ((result: T) => {
      const status = (result as { status?: unknown })?.status;
      return typeof status !== "string" || !PENDING_STATUSES.has(status);
    });

  const polling = ref(false);
  const attempts = ref(0);
  const error = ref<string | null>(null);
  let timer = 0;
  let stopped = false;

  const stop = () => {
    stopped = true;
    polling.value = false;
    if (timer) {
      window.clearTimeout(timer);
      timer = 0;
    }
  };

  const tick = async () => {
    if (stopped) return;
    try {
      const result = await fetcher();
      if (stopped) return;
      onUpdate(result);
      attempts.value += 1;
      if (isTerminal(result) || attempts.value >= maxAttempts) {
        stop();
        return;
      }
      timer = window.setTimeout(() => void tick(), intervalMs);
    } catch (cause) {
      if (stopped) return;
      error.value =
        cause instanceof Error ? cause.message : "任务状态查询失败";
      attempts.value += 1;
      if (attempts.value >= maxAttempts) {
        stop();
        return;
      }
      timer = window.setTimeout(() => void tick(), intervalMs);
    }
  };

  const start = async () => {
    stop();
    stopped = false;
    polling.value = true;
    attempts.value = 0;
    error.value = null;
    await tick();
  };

  onScopeDispose(stop);

  return { attempts, error, polling, start, stop };
};