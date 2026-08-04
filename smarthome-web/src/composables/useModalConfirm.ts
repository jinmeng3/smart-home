import { ref } from "vue";
import { sleep } from "../utils/async";

interface ModalConfirmOptions {
  /** 最小展示时长（毫秒），用于避免按钮一闪而过 */
  minDuration?: number;
  /** 确认前执行的异步准备，可在其中进行校验或调用外部接口 */
  prepare?: () => void | Promise<void>;
}

/**
 * 封装弹窗「点击确认 → loading → 关闭」的通用流程。
 * 用法：传入需要触发的事件回调与提示文案，返回 { loading, confirm }。
 */
export const useModalConfirm = (
  onConfirm: () => void | Promise<void>,
  options: ModalConfirmOptions = {},
) => {
  const loading = ref(false);
  const minDuration = options.minDuration ?? 450;

  const confirm = async () => {
    if (loading.value) {
      return;
    }

    try {
      loading.value = true;
      await options.prepare?.();
      await sleep(minDuration);
      await onConfirm();
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    confirm,
  };
};
