import { ref } from "vue";

interface AsyncActionOptions {
    onSuccess?: () => void;
    onError?: (error: unknown) => void;
    onFinally?: () => void;
}

/**
 * 通用异步操作状态管理
 *
 * 防止重复提交，自动处理 pending/error 状态。
 * 适用于保存、删除、添加成员等需要防重复的异步场景。
 *
 * 统一命名：`pending`（进行中状态）、`execute`（执行函数），
 * 不再保留 `loading/run` 别名，避免新调用者混淆。
 *
 * @example
 * const { pending, execute } = useAsyncAction(async () => {
 *     await api.saveSettings(data);
 * });
 */
export const useAsyncAction = <Args extends unknown[] = [], T = void>(
    action: (...args: Args) => Promise<T>,
    options: AsyncActionOptions = {},
) => {
    const pending = ref(false);
    const error = ref<unknown>(null);

    const execute = async (...args: Args): Promise<T | undefined> => {
        if (pending.value) return;

        pending.value = true;
        error.value = null;

        try {
            const result = await action(...args);
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

    return {
        pending,
        error,
        execute,
        reset,
    };
};
