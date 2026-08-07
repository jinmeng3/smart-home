import { onScopeDispose, ref } from "vue";

export const useLatestRequest = () => {
    const loading = ref(false);
    let requestId = 0;

    const invalidate = () => {
        requestId += 1;
        loading.value = false;
    };

    const run = async <T>(
        request: () => Promise<T>,
        onSuccess: (result: T) => void,
        onError?: (error: unknown) => void,
    ) => {
        const currentRequest = ++requestId;
        loading.value = true;

        try {
            const result = await request();
            if (currentRequest === requestId) onSuccess(result);
        } catch (error) {
            if (currentRequest === requestId) onError?.(error);
        } finally {
            if (currentRequest === requestId) loading.value = false;
        }
    };

    onScopeDispose(invalidate);

    return { invalidate, loading, run };
};
