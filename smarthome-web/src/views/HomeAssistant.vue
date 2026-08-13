<script setup lang="ts">
import { onBeforeUnmount, watch } from "vue";
import ChatWindow from "../components/chat/ChatWindow.vue";
import Header from "../components/layout/Header.vue";
import AssistantRail from "../components/dashboard/AssistantRail.vue";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { useCollapsePhase } from "../composables/useCollapsePhase";
import { useAuthStore } from "../stores/auth";
import { useHomeStore } from "../stores/home";

const store = useHomeStore();
const authStore = useAuthStore();

const refreshHomeData = () => {
    return Promise.all([
        store.loadDevices(),
        store.refreshRecentConversations(),
    ]).then(() => undefined);
};

useAuthenticatedLoader(refreshHomeData);

/* ── 右侧栏折叠状态 + 三阶段动画 ──────────────────────────────── */
const RAIL_STORAGE_KEY = "orion.assistant-rail-collapsed";
const isMediumScreen = () =>
    window.matchMedia("(min-width: 1024px) and (max-width: 1279px)").matches;

const {
    collapsed: railCollapsed,
    phase: railPhase,
    toggle: toggleRail,
    skipAnimation: skipRailAnimation,
} = useCollapsePhase(
    (() => {
        const saved = localStorage.getItem(RAIL_STORAGE_KEY);
        if (saved !== null) return saved === "true";
        return isMediumScreen();
    })(),
    (value) => {
        localStorage.setItem(RAIL_STORAGE_KEY, String(value));
    },
);

skipRailAnimation();

const mediaQuery = window.matchMedia(
    "(min-width: 1024px) and (max-width: 1279px)",
);
const handleMediumChange = (event: MediaQueryListEvent) => {
    if (event.matches && localStorage.getItem(RAIL_STORAGE_KEY) === null) {
        railCollapsed.value = true;
    }
};
mediaQuery.addEventListener("change", handleMediumChange);
onBeforeUnmount(() => {
    mediaQuery.removeEventListener("change", handleMediumChange);
});
</script>

<template>
    <div
        class="app-page-layout"
        :class="{ 'rail-collapsed-layout': railCollapsed }"
    >
        <section
            :inert="!authStore.isAuthenticated"
            :aria-disabled="!authStore.isAuthenticated"
            class="page-enter chat-section flex min-h-0 flex-col rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] shadow-soft"
        >
            <Header :compact="store.messages.length > 0" />
            <ChatWindow />
        </section>
        <AssistantRail
            :collapsed="railCollapsed"
            :phase="railPhase"
            @toggle="toggleRail"
        />
    </div>
</template>

<style scoped>
/* 与 components.css 的 .app-page-layout 保持一致，便于收起时切换列宽。
   仅桌面端（≥1024px）为双栏；移动端保持 components.css 的单栏布局。
   使用 auto 列 + rail 自身 width 过渡实现平滑动画。 */
@media (min-width: 1024px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }

    .app-page-layout.rail-collapsed-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

.chat-section {
    overflow: hidden;
    min-width: 0;
}

@media (min-width: 1024px) and (max-width: 1279px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }

    .app-page-layout.rail-collapsed-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

@media (prefers-reduced-motion: reduce) {
    .app-page-layout {
        transition: none;
    }
}
</style>