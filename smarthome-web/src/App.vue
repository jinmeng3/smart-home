<script setup lang="ts">
import { computed, markRaw, onMounted, onUnmounted, ref, shallowRef, watchEffect, nextTick } from "vue";
import { useRouter } from "vue-router";
import Sidebar from "./components/layout/Sidebar.vue";
import ModalTransition from "./components/common/ModalTransition.vue";
import SvgCore from "./components/common/SvgCore.vue";
import { useAuthStore } from "./stores/auth";
import { useHomeStore } from "./stores/home";
import { useSettingsStore } from "./stores/settings";
import { defineAsyncDialog } from "./utils/asyncDialog";

const LoginDialog = defineAsyncDialog(
    () => import("./components/account/LoginDialog.vue"),
);

const store = useHomeStore();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const router = useRouter();

const SvgSprite = shallowRef();
const extrasLoaded = ref(false);
let spritePromise: Promise<void> | null = null;
let isInitialNavigation = true;

router.beforeEach(async () => {
    if (isInitialNavigation) {
        isInitialNavigation = false;
        if (!extrasLoaded.value) {
            spritePromise = import("./components/common/SvgSprite.vue").then(
                (mod) => {
                    SvgSprite.value = markRaw(mod.default);
                    extrasLoaded.value = true;
                    return nextTick();
                },
            );
        }
        return;
    }

    if (!extrasLoaded.value && spritePromise) {
        await spritePromise;
        await nextTick();
    }
});

const systemDark = ref(
    window.matchMedia("(prefers-color-scheme: dark)").matches,
);

const activeTheme = computed(() => {
    const themeMode = settingsStore.settings.appearance.themeMode;

    if (themeMode !== "system") {
        return themeMode;
    }

    return systemDark.value ? "dark" : "light";
});

watchEffect(() => {
    document.documentElement.dataset.theme = activeTheme.value;
    document.documentElement.dataset.fontSize =
        settingsStore.settings.appearance.fontSize;
    document.documentElement.dataset.motion = settingsStore.settings.appearance
        .animationsEnabled
        ? "on"
        : "off";
    document.documentElement.dataset.performance = settingsStore.settings
        .appearance.performanceMode
        ? "lite"
        : "full";
});

const systemThemeHandler = () => {
    systemDark.value = window.matchMedia("(prefers-color-scheme: dark)").matches;
};

let systemThemeQuery: MediaQueryList | null = null;

onMounted(() => {
    systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    systemThemeQuery.addEventListener("change", systemThemeHandler);

    if (authStore.isAuthenticated) {
        void settingsStore.loadAccountHome().catch(() => undefined);
    }
});

onUnmounted(() => {
    systemThemeQuery?.removeEventListener("change", systemThemeHandler);
    systemThemeQuery = null;
});
</script>

<template>
    <main
        class="h-screen overflow-hidden bg-[var(--color-page-background)] text-[var(--color-text-primary)]"
    >
        <SvgCore />
        <component :is="SvgSprite" v-if="extrasLoaded" />
        <div
            class="app-shell grid h-full gap-2 bg-[radial-gradient(circle_at_20%_10%,var(--color-brand-glow),transparent_28%),linear-gradient(135deg,var(--color-page-bg)_0%,var(--color-sidebar-bg)_100%)] p-2 transition-[grid-template-columns] duration-500 ease-out"
            :class="
                store.sidebarCollapsed
                    ? 'grid-cols-[72px_minmax(0,1fr)_330px]'
                    : 'grid-cols-[240px_minmax(0,1fr)_330px]'
            "
        >
            <Sidebar />
            <RouterView v-slot="{ Component, route }">
                <ModalTransition name="slide-up" mode="out-in">
                    <component :is="Component" :key="route.path" />
                </ModalTransition>
            </RouterView>
            <LoginDialog v-if="authStore.loginVisible" />
        </div>
    </main>
</template>
