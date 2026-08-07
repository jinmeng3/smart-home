import { defineAsyncComponent, type Component } from "vue";
import AsyncDialogLoading from "../components/common/AsyncDialogLoading.vue";

type DialogLoader = () => Promise<Component>;

export const defineAsyncDialog = (loader: DialogLoader) =>
    defineAsyncComponent({
        loader,
        loadingComponent: AsyncDialogLoading,
        delay: 100,
        timeout: 15_000,
        suspensible: false,
    });

export const preloadDialog = (loader: DialogLoader) => {
    void loader();
};
