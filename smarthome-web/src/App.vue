<script setup lang="ts">
import {
    computed,
    markRaw,
    nextTick,
    onMounted,
    onUnmounted,
    ref,
    shallowRef,
    watch,
    watchEffect,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import Sidebar from "./components/layout/Sidebar.vue";
import ModalTransition from "./components/common/ModalTransition.vue";
import SvgCore from "./components/common/SvgCore.vue";
import { useAuthStore } from "./stores/auth";
import { useHomeStore } from "./stores/home";
import { useSettingsStore } from "./stores/settings";
import { defineAsyncDialog } from "./utils/asyncDialog";
import { navigationItems } from "./router/navigation";

const LoginDialog = defineAsyncDialog(
    () => import("./components/account/LoginDialog.vue"),
);

const store = useHomeStore();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const mobileNavigationOpen = ref(false);
const activePageTitle = computed(
    () =>
        navigationItems.find((item) => item.path === route.path)?.label ??
        "Orion Home",
);

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

const closeMobileNavigation = () => {
    mobileNavigationOpen.value = false;
};

const handleGlobalKeydown = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
        closeMobileNavigation();
    }
};

watch(
    () => route.path,
    closeMobileNavigation,
);

watch(mobileNavigationOpen, (open) => {
    document.body.style.overflow = open ? "hidden" : "";
});

let systemThemeQuery: MediaQueryList | null = null;

onMounted(() => {
    systemThemeQuery = window.matchMedia("(prefers-color-scheme: dark)");
    systemThemeQuery.addEventListener("change", systemThemeHandler);
    window.addEventListener("keydown", handleGlobalKeydown);

    if (authStore.isAuthenticated) {
        void Promise.all([
            settingsStore.loadAccountHome(),
            settingsStore.loadUserPreferences(),
        ]).catch(() => undefined);
    }
});

onUnmounted(() => {
    systemThemeQuery?.removeEventListener("change", systemThemeHandler);
    window.removeEventListener("keydown", handleGlobalKeydown);
    document.body.style.overflow = "";
    systemThemeQuery = null;
});
</script>

<template>
    <main class="app-viewport">
        <SvgCore />
        <component :is="SvgSprite" v-if="extrasLoaded" />
        <div class="app-shell">
            <Sidebar class="desktop-sidebar" mode="full" />
            <Sidebar class="tablet-sidebar" mode="compact" />
            <header class="mobile-app-header">
                <button
                    class="mobile-menu-button"
                    type="button"
                    aria-label="打开导航"
                    :aria-expanded="mobileNavigationOpen"
                    @click="mobileNavigationOpen = true"
                >
                    <span></span><span></span><span></span>
                </button>
                <strong>{{ activePageTitle }}</strong>
                <img src="/orion-sidebar-icon.svg" alt="" />
            </header>
            <RouterView v-slot="{ Component, route }">
                <ModalTransition name="slide-up" mode="out-in">
                    <component :is="Component" :key="route.path" />
                </ModalTransition>
            </RouterView>
            <Transition name="nav-fade">
                <button
                    v-if="mobileNavigationOpen"
                    class="mobile-nav-backdrop"
                    type="button"
                    aria-label="关闭导航"
                    @click="closeMobileNavigation"
                ></button>
            </Transition>
            <Transition name="nav-slide">
                <Sidebar
                    v-if="mobileNavigationOpen"
                    class="mobile-sidebar"
                    mode="drawer"
                    @close="closeMobileNavigation"
                />
            </Transition>
            <LoginDialog v-if="authStore.loginVisible" />
        </div>
    </main>
</template>

<style scoped>
.app-viewport {
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
    background: var(--color-page-background);
    color: var(--color-text-primary);
}

.app-shell {
    display: grid;
    width: 100%;
    height: 100%;
    min-width: 0;
    grid-template-columns: 240px minmax(0, 1fr) 330px;
    gap: 8px;
    padding: 8px;
    background:
        radial-gradient(circle at 20% 10%, var(--color-brand-glow), transparent 28%),
        linear-gradient(135deg, var(--color-page-bg) 0%, var(--color-sidebar-bg) 100%);
}

.tablet-sidebar,
.mobile-app-header,
.mobile-sidebar,
.mobile-nav-backdrop {
    display: none;
}

@media (max-width: 1279px) {
    .app-shell {
        grid-template-columns: 76px minmax(0, 1fr);
    }

    .desktop-sidebar {
        display: none;
    }

    .tablet-sidebar {
        display: flex;
    }
}

@media (max-width: 767px) {
    .app-shell {
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 6px;
    }

    .tablet-sidebar {
        display: none;
    }

    .mobile-app-header {
        display: flex;
        height: 52px;
        flex: 0 0 52px;
        align-items: center;
        justify-content: space-between;
        border: 1px solid var(--color-border);
        border-radius: 14px;
        background: var(--color-sidebar-bg);
        padding: 0 12px;
        box-shadow: var(--shadow-soft);
    }

    .mobile-app-header strong {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 15px;
        font-weight: 900;
    }

    .mobile-app-header img,
    .mobile-menu-button {
        width: 34px;
        height: 34px;
        flex: 0 0 34px;
        border-radius: 10px;
    }

    .mobile-menu-button {
        display: grid;
        place-content: center;
        gap: 4px;
        background: var(--color-primary-50);
    }

    .mobile-menu-button span {
        width: 17px;
        height: 2px;
        border-radius: 999px;
        background: var(--color-primary-700);
    }

    .mobile-nav-backdrop {
        position: fixed;
        z-index: 80;
        inset: 0;
        display: block;
        border: 0;
        border-radius: 0;
        background: rgb(15 23 42 / 46%);
        cursor: default;
    }

    .mobile-sidebar {
        position: fixed;
        z-index: 81;
        inset: 6px auto 6px 6px;
        display: flex;
        width: min(292px, calc(100vw - 32px));
    }
}

.nav-fade-enter-active,
.nav-fade-leave-active,
.nav-slide-enter-active,
.nav-slide-leave-active {
    transition: opacity 180ms var(--motion-ease), transform 180ms var(--motion-ease);
}

.nav-fade-enter-from,
.nav-fade-leave-to {
    opacity: 0;
}

.nav-slide-enter-from,
.nav-slide-leave-to {
    opacity: 0;
    transform: translateX(-24px);
}

@media (prefers-reduced-motion: reduce) {
    .nav-fade-enter-active,
    .nav-fade-leave-active,
    .nav-slide-enter-active,
    .nav-slide-leave-active {
        transition-duration: 1ms;
    }
}
</style>
