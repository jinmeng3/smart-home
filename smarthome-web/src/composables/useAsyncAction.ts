import { ref } from "vue";

interface AsyncActionOptions {
    onSuccess?: () => void;
    onError?: (error: unknown) => void;
    onFinally?: () => void;
}

/**
 * 通用异步操作状态管理
 *
 * 防止重复提交，自动处理 loading/error 状态。
 * 适用于保存、删除、添加成员等需要防重复的异步场景。
 *
 * @example
 * const { pending, execute } = useAsyncAction(async () => {
 *     await api.saveSettings(data);
 * });
 */
export const useAsyncAction = <T = void>(
    action: () => Promise<T>,
    options: AsyncActionOptions = {},
) => {
    const pending = ref(false);
    const error = ref<unknown>(null);

    const execute = async (): Promise<T | undefined> => {
        if (pending.value) return;

        pending.value = true;
        error.value = null;

        try {
            const result = await action();
            options.onSuccess?.();
            return result;
        } catch (err) {
            error.value = err;
            options.onError?.(err);
            throw err;
        } finally {
            pending.value = false;
            options.onFinally?.();
        }
    };

    const reset = () => {
        pending.value = false;
        error.value = null;
    };

    return { pending, error, execute, reset };
};