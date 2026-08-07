import { onScopeDispose, ref } from "vue";

interface UseAsyncActionOptions<TResult> {
    /** 失败回调（默认行为：把错误写入 error 并吞掉，避免 unhandled rejection） */
    onError?: (error: unknown) => void;
    /** 成功回调 */
    onSuccess?: (result: TResult) => void;
    /** 无论成败都执行（清理/刷新等） */
    onFinally?: () => void;
    /** 失败时是否重新抛出（默认 false；需要上层继续处理时置 true） */
    rethrow?: boolean;
}

/**
 * 统一异步操作的 loading / 防重复提交 / 错误处理（低端机性能 + 代码复用）。
 * 满足「低端设备性能优化方案」验收口径：
 *  - 防重复提交：同一时刻只允许一次进行中的调用，后续 run 直接忽略；
 *  - loading 自动管理：替代手写的 `xxxing.value = true/false` 样板；
 *  - error 统一收集：默认吞掉错误（可配 onError 弹提示），也可 rethrow。
 */
export const useAsyncAction = <TArgs extends unknown[], TResult>(
    action: (...args: TArgs) => Promise<TResult>,
    options: UseAsyncActionOptions<TResult> = {},
) => {
    const loading = ref(false);
    const error = ref<unknown>(null);
    let inFlight = false;

    const run = async (...args: TArgs): Promise<TResult | undefined> => {
        if (inFlight) {
            return undefined;
        }

        inFlight = true;
        loading.value = true;
        error.value = null;

        try {
            const result = await action(...args);
            options.onSuccess?.(result);
            return result;
        } catch (err) {
            error.value = err;
            options.onError?.(err);
            if (options.rethrow) {
                throw err;
            }
            return undefined;
        } finally {
            inFlight = false;
            loading.value = false;
            options.onFinally?.();
        }
    };

    const reset = () => {
        error.value = null;
    };

    onScopeDispose(() => {
        inFlight = false;
    });

    return { error, loading, reset, run };
};