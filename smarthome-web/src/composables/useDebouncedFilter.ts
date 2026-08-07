import { onScopeDispose, ref } from "vue";

/**
 * 筛选条件防抖请求（SRP + 低端机性能）。
 * 满足「低端设备性能优化方案」的验收口径：
 *  - 合并连续筛选变化：输入停止 delay 后才真正发起请求；
 *  - 用 AbortSignal 取消上一个未完成请求，避免旧响应覆盖新数据；
 *  - 仅最新一次发起能写入状态（loading 状态以 requestId 兜底）。
 */
export const useDebouncedFilter = (
  request: (signal: AbortSignal) => Promise<void>,
  delay = 250,
) => {
  const loading = ref(false);
  let timerId = 0;
  let requestId = 0;
  let controller: AbortController | null = null;

  const run = () => {
    window.clearTimeout(timerId);
    timerId = window.setTimeout(() => {
      controller?.abort();
      const nextController = new AbortController();
      controller = nextController;
      const currentRequest = ++requestId;
      loading.value = true;
      void (async () => {
        try {
          await request(nextController.signal);
        } finally {
          if (currentRequest === requestId) {
            loading.value = false;
          }
        }
      })();
    }, delay);
  };

  /** 立即发起，跳过防抖（用于分页、首次加载等需要即时反馈的场景）。 */
  const flush = () => {
    window.clearTimeout(timerId);
    controller?.abort();
    const nextController = new AbortController();
    controller = nextController;
    const currentRequest = ++requestId;
    loading.value = true;
    void (async () => {
      try {
        await request(nextController.signal);
      } finally {
        if (currentRequest === requestId) {
          loading.value = false;
        }
      }
    })();
  };

  const cancel = () => {
    window.clearTimeout(timerId);
    controller?.abort();
    controller = null;
    loading.value = false;
  };

  onScopeDispose(cancel);

  return { cancel, flush, loading, run };
};