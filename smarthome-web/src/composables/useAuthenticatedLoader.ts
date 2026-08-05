import { onMounted, watch } from "vue";
import { useAuthStore } from "../stores/auth";

/**
 * 在挂载时以及用户变为已登录时执行加载函数。
 * loader 需自行处理未登录分支（如静默返回或打开登录弹窗）。
 */
export const useAuthenticatedLoader = (loader: () => void) => {
    const authStore = useAuthStore();

    onMounted(loader);

    watch(
        () => authStore.isAuthenticated,
        (authenticated) => {
            if (authenticated) loader();
        },
    );
};
