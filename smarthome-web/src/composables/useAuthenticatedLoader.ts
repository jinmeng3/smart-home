import { onMounted, watch } from "vue";
import { useAuthStore } from "../stores/auth";

interface AuthenticatedLoaderOptions {
    immediate?: boolean;
    promptLogin?: boolean;
}

export const useAuthenticatedLoader = (
    loader: () => void | Promise<void>,
    options: AuthenticatedLoaderOptions = {},
) => {
    const authStore = useAuthStore();
    const immediate = options.immediate ?? true;
    const promptLogin = options.promptLogin ?? true;

    const run = async () => {
        if (!authStore.isAuthenticated) {
            if (promptLogin) authStore.openLogin();
            return;
        }

        await loader();
    };

    if (immediate) onMounted(() => void run());

    watch(
        () => authStore.isAuthenticated,
        (authenticated) => {
            if (authenticated) void run();
        },
    );

    return run;
};
