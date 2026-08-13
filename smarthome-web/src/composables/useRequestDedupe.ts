import { onScopeDispose } from "vue";

/**
 * 请求去重——相同 key 的并发请求复用同一个 Promise。
 *
 * 适用于：相同参数同时发起的多个请求（如页面初始化时多个组件同时请求同一接口）。
 * 不适用于参数不同、需要各自响应的场景。
 *
 * @example
 * const fetchWithDedupe = useRequestDedupe(fetchUser);
 * const user1 = await fetchWithDedupe("user-1"); // 发起请求
 * const user2 = await fetchWithDedupe("user-1"); // 复用上次未完成的 Promise
 */
export const useRequestDedupe = <TArgs extends unknown[], TResult>(
    fetcher: (...args: TArgs) => Promise<TResult>,
    /**
     * 生成去重 key。默认使用 JSON.stringify(args)，调用方可自定义。
     * 返回 falsy 值时跳过去重（每次独立请求）。
     */
    keyFn?: (...args: TArgs) => string | undefined,
) => {
    const inflight = new Map<string, Promise<TResult>>();

    const deduped = async (...args: TArgs): Promise<TResult> => {
        const key = keyFn?.(...args) ?? JSON.stringify(args);
        if (!key) {
            return fetcher(...args);
        }

        const existing = inflight.get(key);
        if (existing) return existing;

        const promise = fetcher(...args);
        inflight.set(key, promise);

        try {
            const result = await promise;
            return result;
        } finally {
            inflight.delete(key);
        }
    };

    const cancel = () => {
        inflight.clear();
    };

    onScopeDispose(cancel);

    return { deduped, cancel };
};