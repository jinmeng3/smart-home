<script setup lang="ts">
import { computed, onMounted, onUnmounted, watchEffect } from "vue";
import Sidebar from "./components/layout/Sidebar.vue";
import LoginDialog from "./components/account/LoginDialog.vue";
import ModalTransition from "./components/common/ModalTransition.vue";
import { useAuthStore } from "./stores/auth";
import { useHomeStore } from "./stores/home";
import { useSettingsStore } from "./stores/settings";

const store = useHomeStore();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
let systemThemeQuery: MediaQueryList | null = null;
const updateSystemTheme = () => {
    document.documentElement.dataset.theme = activeTheme.value;
};

const activeTheme = computed(() => {
    const themeMode = settingsStore.settings.appearance.themeMode;

    if (themeMode !== "system") {
        return themeMode;
    }

    return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
});

watchEffect(() => {
    document.documentElement.dataset.theme = activeTheme.value;
    document.documentElement.dataset.fontSize =
        settingsStore.settings.appearance.fontSize;
    document.documentElement.dataset.motion = settingsStore.settings.appearance
        .animationsEnabled
        ? "on"
        : "off";
});

onMounted(() => {
    systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    systemThemeQuery.addEventListener("change", updateSystemTheme);

    if (authStore.isAuthenticated) {
        void settingsStore.loadAccountHome().catch(() => undefined);
    }
});

onUnmounted(() => {
    systemThemeQuery?.removeEventListener("change", updateSystemTheme);
    systemThemeQuery = null;
});
</script>

<template>
    <main
        class="h-screen overflow-hidden bg-[var(--color-page-background)] text-[var(--color-text-primary)]"
    >
        <div
            class="grid h-full gap-2 bg-[radial-gradient(circle_at_20%_10%,rgba(37,99,235,0.08),transparent_28%),linear-gradient(135deg,var(--color-page-background)_0%,var(--color-sidebar-background)_100%)] p-2 transition-[grid-template-columns] duration-500 ease-out"
            :class="
                store.sidebarCollapsed
                    ? 'grid-cols-[72px_minmax(0,1fr)_330px]'
                    : 'grid-cols-[240px_minmax(0,1fr)_330px]'
            "
        >
            <Sidebar />
            <RouterView v-slot="{ Component }">
                <ModalTransition name="slide-up" mode="out-in">
                    <component :is="Component" />
                </ModalTransition>
            </RouterView>
            <LoginDialog />
        </div>
    </main>
</template>
