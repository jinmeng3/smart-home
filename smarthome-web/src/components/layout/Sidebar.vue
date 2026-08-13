<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import { useHomeStore } from "../../stores/home";
import { useSettingsStore } from "../../stores/settings";
import {
    navigationItems,
    type NavigationItem,
} from "../../router/navigation";
import type { RecentConversation } from "../../types/chat";
import SvgIcon from "../common/SvgIcon.vue";

const props = withDefaults(
    defineProps<{
        mode?: "full" | "compact" | "drawer";
        phase?: "expanded" | "collapsing" | "collapsed" | "expanding";
    }>(),
    {
        mode: "full",
        phase: "expanded",
    },
);

const emit = defineEmits<{
    close: [];
}>();

const store = useHomeStore();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const avatarLoadError = ref(false);

const menuItems = navigationItems;
const primaryMenuItem = menuItems[0]!;
const secondaryMenuItems = menuItems.slice(1);
const activeLabel = computed(
    () =>
        menuItems.find((item) => item.path === route.path)?.label ??
        "智能对话",
);

const account = computed(() => settingsStore.settings.account);
const accountInitial = computed(() =>
    authStore.isAuthenticated
        ? account.value.username.trim().slice(0, 1).toUpperCase()
        : "访",
);

/* ── 最近会话分组：今天 / 昨天 / 更早 ─────────────────────────── */
const conversationGroups = computed(() => {
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfYesterday = new Date(startOfToday);
    startOfYesterday.setDate(startOfYesterday.getDate() - 1);

    const groups: { key: string; label: string; conversations: RecentConversation[] }[] = [
        { key: "today", label: "今天", conversations: [] },
        { key: "yesterday", label: "昨天", conversations: [] },
        { key: "earlier", label: "更早", conversations: [] },
    ];

    for (const conversation of store.recentConversations) {
        const date = new Date(conversation.updatedAt);
        if (Number.isNaN(date.getTime())) {
            groups[2]!.conversations.push(conversation);
            continue;
        }
        if (date >= startOfToday) groups[0]!.conversations.push(conversation);
        else if (date >= startOfYesterday) groups[1]!.conversations.push(conversation);
        else groups[2]!.conversations.push(conversation);
    }

    return groups.filter((group) => group.conversations.length > 0);
});

/** 当前会话（淡蓝背景 + 左侧高亮条） */
const isActiveConversation = (id: string) => store.activeSessionId === id;

/* ── 滚动渐隐提示 ─────────────────────────────────────────────── */
const scrollGroupRef = ref<HTMLElement | null>(null);
const scrollAtTop = ref(true);
const scrollAtBottom = ref(true);
const updateScrollState = () => {
    const el = scrollGroupRef.value;
    if (!el) return;
    const { scrollTop, scrollHeight, clientHeight } = el;
    scrollAtTop.value = scrollTop <= 4;
    scrollAtBottom.value = scrollTop + clientHeight >= scrollHeight - 4;
};

// 路由切换后重新计算渐隐状态（侧边栏本身不销毁，滚动位置天然保留）
watch(
    () => route.path,
    () => {
        void nextTick(updateScrollState);
    },
);

watch(
    () => store.recentConversations.length,
    () => {
        void nextTick(updateScrollState);
    },
);

/* ── 紧凑模式会话浮层 ─────────────────────────────────────────── */
const compactPanelOpen = ref(false);
const toggleChatFromCompact = async () => {
    if (props.mode !== "compact") return;
    compactPanelOpen.value = !compactPanelOpen.value;
};

/* ── 交互 ─────────────────────────────────────────────────────── */
const selectMenu = async (item: NavigationItem) => {
    store.setActiveMenu(item.label);

    if (item.path === "/" && !authStore.isAuthenticated) {
        authStore.openLogin();
        return;
    }

    if (item.path && item.path !== route.path) {
        if (!authStore.isAuthenticated) {
            authStore.openLogin();
            return;
        }

        await router.push(item.path);
    }

    if (props.mode === "drawer") emit("close");
};

const preloadMenu = (item: NavigationItem) => {
    if (item.path !== route.path) {
        void item.loadComponent();
    }
};

const startConversation = async () => {
    if (!authStore.isAuthenticated) {
        authStore.openLogin();
        return;
    }

    if (route.path !== "/") {
        await router.push("/");
    }

    await store.startNewConversation();
    compactPanelOpen.value = false;
    if (props.mode === "drawer") emit("close");
};

const openConversation = async (sessionId: string) => {
    if (!authStore.isAuthenticated) {
        authStore.openLogin();
        return;
    }

    if (route.path !== "/") {
        await router.push("/");
    }

    await store.loadConversation(sessionId);
    compactPanelOpen.value = false;
    if (props.mode === "drawer") emit("close");
};

const deleteConversation = async (sessionId: string) => {
    if (!authStore.isAuthenticated) return;
    await store.deleteConversation(sessionId);
};
</script>

<template>
    <aside
        :class="[
            `is-${mode}`,
            `phase-${props.phase}`,
            { 'is-collapsed': store.sidebarCollapsed && mode === 'full' },
            store.sidebarCollapsed && mode === 'full' ? 'px-2' : 'px-4',
        ]"
        class="page-enter-stagger relative flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-sidebar-bg)] py-5 shadow-soft transition-[width] duration-300 ease-out"
        :style="{ width: store.sidebarCollapsed && mode === 'full' ? '76px' : '240px' }"
    >
        <button
            v-if="mode === 'drawer'"
            class="drawer-close"
            type="button"
            aria-label="关闭导航"
            @click="emit('close')"
        >
            <SvgIcon name="close" size="sm" />
        </button>

        <!-- 品牌区 -->
        <div
            class="mb-6 flex shrink-0 items-center"
            :class="store.sidebarCollapsed && mode === 'full' ? 'justify-center' : 'gap-3'"
        >
            <button
                class="brand-logo motion-button grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-full bg-[var(--color-primary-50)] ring-1 ring-[var(--color-primary-100)] transition-transform duration-200 hover:scale-105"
                type="button"
                title="Orion Home"
                @click="store.sidebarCollapsed && store.toggleSidebar()"
            >
                <img
                    class="h-full w-full object-cover"
                    src="/orion-sidebar-icon.svg"
                    alt="Orion Home"
                />
            </button>
            <div
                v-show="!store.sidebarCollapsed || mode !== 'full'"
                class="min-w-0 sidebar-detail"
            >
                <strong
                    class="block truncate text-lg font-extrabold text-[var(--color-primary-700)]"
                >
                    Orion
                </strong>
                <span
                    class="block truncate text-[11px] font-semibold text-[var(--color-text-tertiary)]"
                >
                    Home Assistant
                </span>
            </div>
            <button
                v-show="!store.sidebarCollapsed || mode !== 'full'"
                class="motion-button ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[var(--color-text-tertiary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary-700)] sidebar-detail"
                type="button"
                title="折叠菜单"
                @click="store.toggleSidebar"
            >
                ‹
            </button>
        </div>

        <div class="sidebar-content flex min-h-0 flex-1 flex-col">
            <!-- 智能对话：固定 -->
            <nav class="primary-navigation grid shrink-0 gap-1">
                <button
                    :key="primaryMenuItem.label"
                    class="motion-button relative flex h-11 items-center rounded-lg text-sm font-bold text-[var(--color-text-secondary)] transition-all duration-150 hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary-700)]"
                    :class="activeLabel === primaryMenuItem.label ? 'gap-3 bg-[var(--color-primary-100)] px-3 text-[var(--color-primary-700)]' : 'gap-3 px-3'"
                    type="button"
                    :title="primaryMenuItem.label"
                    @focus="preloadMenu(primaryMenuItem)"
                    @mouseenter="preloadMenu(primaryMenuItem)"
                    @click="mode === 'compact' ? toggleChatFromCompact() : selectMenu(primaryMenuItem)"
                >
                    <span
                        v-if="activeLabel === primaryMenuItem.label && (!store.sidebarCollapsed || mode !== 'full')"
                        class="active-indicator absolute left-0 h-6 w-1 rounded-full bg-[var(--color-primary-600)]"
                    ></span>
                    <span
                        class="menu-icon"
                        :class="{ 'is-active': activeLabel === primaryMenuItem.label }"
                        :style="
                            activeLabel === primaryMenuItem.label
                                ? { background: primaryMenuItem.soft, color: primaryMenuItem.tone }
                                : {}
                        "
                    >
                        <SvgIcon :name="primaryMenuItem.icon" />
                    </span>
                    <span
                        v-show="!store.sidebarCollapsed || mode !== 'full'"
                        class="truncate sidebar-detail"
                    >
                        {{ primaryMenuItem.label }}
                    </span>
                    <span
                        v-if="mode === 'compact'"
                        class="compact-panel-trigger"
                        :class="{ 'is-open': compactPanelOpen }"
                        aria-hidden="true"
                    ></span>
                </button>
            </nav>

            <!-- 共同滚动区：其他导航 + 最近会话 -->
            <div class="scroll-region">
                <div
                    ref="scrollGroupRef"
                    class="sidebar-scroll-group min-h-0 flex-1 overflow-y-auto"
                    @scroll.passive="updateScrollState"
                >
                    <nav class="secondary-navigation grid gap-1">
                        <button
                            v-for="item in secondaryMenuItems"
                            :key="item.label"
                            class="motion-button relative flex h-11 items-center rounded-lg text-sm font-bold text-[var(--color-text-secondary)] transition-all duration-150 hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary-700)]"
                            :class="activeLabel === item.label ? 'gap-3 bg-[var(--color-primary-100)] px-3 text-[var(--color-primary-700)]' : 'gap-3 px-3'"
                            type="button"
                            :title="item.label"
                            @focus="preloadMenu(item)"
                            @mouseenter="preloadMenu(item)"
                            @click="selectMenu(item)"
                        >
                            <span
                                v-if="activeLabel === item.label && (!store.sidebarCollapsed || mode !== 'full')"
                                class="active-indicator absolute left-0 h-6 w-1 rounded-full bg-[var(--color-primary-600)]"
                            ></span>
                            <span
                                class="menu-icon"
                                :class="{ 'is-active': activeLabel === item.label }"
                                :style="activeLabel === item.label ? { background: item.soft, color: item.tone } : {}"
                            >
                                <SvgIcon :name="item.icon" />
                            </span>
                            <span
                                v-show="!store.sidebarCollapsed || mode !== 'full'"
                                class="truncate sidebar-detail"
                            >{{ item.label }}</span>
                        </button>
                    </nav>

                    <!-- 最近会话（今天的会话分组） -->
                    <section
                        v-show="route.path === '/' && !compactPanelOpen"
                        class="conversation-panel"
                    >
                        <div class="conversation-heading">
                            <span>最近会话</span>
                            <button type="button" @click="startConversation">
                                <SvgIcon name="plus" size="sm" />
                                新建
                            </button>
                        </div>

                        <template v-if="store.recentConversations.length">
                            <div
                                v-for="group in conversationGroups"
                                :key="group.key"
                                class="conversation-group"
                            >
                                <p class="conversation-group-label">
                                    {{ group.label }}
                                </p>
                                <div
                                    class="conversation-list"
                                >
                                    <div
                                        v-for="conversation in group.conversations"
                                        :key="conversation.id"
                                        class="conversation-item"
                                        :class="{ 'is-active': isActiveConversation(conversation.id) }"
                                        @click="openConversation(conversation.id)"
                                    >
                                        <span>{{ conversation.title }}</span>
                                        <small>{{ conversation.time }}</small>
                                        <button
                                            class="conversation-delete"
                                            type="button"
                                            title="删除会话"
                                            @click.stop="deleteConversation(conversation.id)"
                                        >
                                            <svg
                                                viewBox="0 0 24 24"
                                                aria-hidden="true"
                                            >
                                                <path
                                                    d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"
                                                />
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </template>
                        <p v-else class="conversation-empty">暂无会话</p>
                    </section>
                </div>

                <!-- 滚动渐隐遮罩 -->
                <div
                    class="scroll-fade scroll-fade-top"
                    :class="{ 'is-visible': !scrollAtTop }"
                    aria-hidden="true"
                ></div>
                <div
                    class="scroll-fade scroll-fade-bottom"
                    :class="{ 'is-visible': !scrollAtBottom }"
                    aria-hidden="true"
                ></div>
            </div>
        </div>

        <!-- 紧凑模式临时会话浮层 -->
        <Transition name="pop">
            <div
                v-if="mode === 'compact' && compactPanelOpen"
                class="compact-sessions absolute bottom-24 left-14 z-30 w-64 overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] shadow-lg"
            >
                <div class="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-3 py-2.5">
                    <span class="text-xs font-black text-[var(--color-text-tertiary)]">
                        最近会话
                    </span>
                    <button
                        class="grid h-6 w-6 place-items-center rounded-md text-[var(--color-primary-700)] transition-colors duration-150 hover:bg-[var(--color-primary-50)]"
                        type="button"
                        title="新建会话"
                        @click="startConversation"
                    >
                        <SvgIcon name="plus" size="sm" />
                    </button>
                </div>
                <div class="max-h-72 overflow-y-auto p-1.5">
                    <button
                        v-for="conversation in store.recentConversations"
                        :key="conversation.id"
                        class="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-bold text-[var(--color-text-secondary)] transition-colors duration-150 hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary-700)]"
                        :class="{
                            'bg-[var(--color-primary-50)] text-[var(--color-primary-700)]':
                                isActiveConversation(conversation.id),
                        }"
                        type="button"
                        @click="openConversation(conversation.id)"
                    >
                        <span class="truncate">{{ conversation.title }}</span>
                        <small class="ml-auto shrink-0 text-[11px] font-bold text-[var(--color-text-tertiary)]">
                            {{ conversation.time }}
                        </small>
                    </button>
                    <p
                        v-if="store.recentConversations.length === 0"
                        class="px-2.5 py-3 text-center text-xs font-bold text-[var(--color-text-tertiary)]"
                    >
                        暂无会话
                    </p>
                </div>
            </div>
        </Transition>

        <!-- 账户区 -->
        <button
            class="mt-auto flex h-[70px] w-full shrink-0 items-center justify-start gap-3 overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-3 transition-all duration-150 hover:border-[var(--color-primary-200)]"
            :class="store.sidebarCollapsed && mode === 'full' ? 'justify-center px-0' : ''"
            type="button"
            @click="authStore.openLogin"
        >
            <img
                v-if="
                    authStore.isAuthenticated &&
                    account.avatarUrl &&
                    !avatarLoadError
                "
                class="h-10 w-10 shrink-0 rounded-full object-cover ring-2 ring-[var(--color-primary-100)]"
                :src="account.avatarUrl"
                alt=""
                @error="avatarLoadError = true"
            />
            <div
                v-else
                class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-100 to-blue-700 text-sm font-extrabold text-white"
            >
                {{ accountInitial }}
            </div>
            <div
                v-show="!store.sidebarCollapsed || mode !== 'full'"
                class="min-w-0 sidebar-detail"
            >
                <strong class="block truncate text-sm">
                    {{
                        authStore.isAuthenticated
                            ? account.username
                            : "访客用户"
                    }}
                </strong>
                <span class="flex items-center gap-1.5 truncate text-xs text-[var(--color-text-tertiary)]">
                    <i
                        class="account-dot"
                        :class="authStore.isAuthenticated ? 'is-online' : ''"
                    ></i>
                    {{
                        authStore.isAuthenticated
                            ? account.email
                            : "登录后同步个人信息"
                    }}
                </span>
            </div>
            <span
                v-show="!store.sidebarCollapsed || mode !== 'full'"
                class="ml-auto text-[var(--color-text-muted)] transition-transform duration-150 sidebar-detail"
            >
                <svg viewBox="0 0 24 24" class="h-4 w-4 fill-none stroke-current" stroke-linecap="round" stroke-linejoin="round" stroke-width="2">
                    <path d="M9 18l6-6-6-6" />
                </svg>
            </span>
        </button>
    </aside>
</template>

<style scoped>
.is-compact > div:first-of-type {
    justify-content: center;
    margin-bottom: 16px;
}

.is-compact .brand-logo {
    width: 48px;
    height: 48px;
    border: 1px solid var(--color-primary-300);
    background: linear-gradient(
        145deg,
        var(--color-primary-50),
        var(--color-primary-100)
    );
    padding: 7px;
    box-shadow:
        0 8px 18px color-mix(in srgb, var(--color-primary-600) 18%, transparent),
        inset 0 1px 0 rgb(255 255 255 / 80%);
}

.is-compact .brand-logo img {
    border-radius: 50%;
    filter: saturate(1.2) contrast(1.12);
}

.is-compact {
    padding: 14px 10px;
}

.is-compact > div:first-of-type {
    justify-content: center;
    margin-bottom: 16px;
}

.is-compact > div:first-of-type > div,
.is-compact nav button > span:last-child,
.is-compact .conversation-panel,
.is-compact > button:last-of-type > div:last-of-type,
.is-compact > button:last-of-type > span:last-child {
    display: none;
}

.is-compact nav button {
    justify-content: center;
    gap: 0;
    padding: 0;
}

.is-compact nav button > span:first-child {
    left: -10px;
}

.is-compact .compact-panel-trigger {
    display: block;
}

.is-compact > button:last-of-type {
    height: 52px;
    justify-content: center;
    padding: 6px;
}

/* 桌面端手动折叠（is-collapsed 复用 compact 样式） */
.is-collapsed {
    padding: 14px 10px;
}

.is-collapsed nav button {
    justify-content: center;
    gap: 0;
    padding: 0;
}

.is-collapsed nav button > span:first-child {
    left: -10px;
}

.is-collapsed .conversation-panel {
    display: none;
}

.is-compact .secondary-navigation,
.is-collapsed .secondary-navigation {
    align-content: start;
}

.is-compact .sidebar-scroll-group,
.is-collapsed .sidebar-scroll-group {
    margin-top: 8px;
}

.is-collapsed > button:last-of-type {
    height: 52px;
    justify-content: center;
    padding: 6px;
}

/* 侧边栏本体：进入动画 + 性能提示 */
aside {
    will-change: transform, opacity;
    transition: padding 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

@media (prefers-reduced-motion: reduce) {
    aside,
    .brand-logo,
    .menu-icon,
    .primary-navigation button,
    .secondary-navigation button,
    aside > button:last-of-type {
        transition-duration: 1ms;
    }
}

.brand-logo,
.menu-icon,
.primary-navigation button,
.secondary-navigation button,
aside > button:last-of-type {
    transition-duration: 300ms;
    transition-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
}

/* 菜单项入场错落动画 */
.primary-navigation,
.secondary-navigation {
    animation: sidebar-nav-enter 360ms var(--motion-ease) both;
}

.primary-navigation {
    animation-delay: 60ms;
}

.secondary-navigation {
    animation-delay: 110ms;
}

@keyframes sidebar-nav-enter {
    from {
        opacity: 0;
        transform: translateX(-8px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.conversation-panel {
    animation: conversation-panel-enter 360ms var(--motion-ease) both;
    animation-delay: 160ms;
}

@keyframes conversation-panel-enter {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* 已激活菜单项指示条动画 */
nav button .active-indicator {
    animation: active-stripe 300ms var(--motion-ease) both;
    transform-origin: left center;
}

@keyframes active-stripe {
    from {
        transform: scaleY(0.4);
        opacity: 0;
    }
    to {
        transform: scaleY(1);
        opacity: 1;
    }
}

/* 菜单图标微动：选中后轻微放大一次，悬停时图标右移 1-2px */
.menu-icon svg {
    transition: transform 160ms var(--motion-ease);
}

nav button:hover .menu-icon svg {
    transform: translateX(1.5px);
}

.menu-icon.is-active svg {
    animation: icon-pop 280ms var(--motion-ease) both;
}

@keyframes icon-pop {
    0% {
        transform: scale(0.86);
    }
    100% {
        transform: scale(1);
    }
}

.drawer-close {
    position: absolute;
    z-index: 1;
    top: 14px;
    right: 14px;
    display: grid;
    width: 34px;
    height: 34px;
    place-items: center;
    border-radius: 9px;
    background: var(--color-surface-subtle);
    color: var(--color-text-secondary);
}

.menu-icon {
    display: grid;
    width: 28px;
    height: 28px;
    flex: 0 0 auto;
    place-items: center;
    border-radius: 8px;
    color: inherit;
    will-change: transform, background, color;
    transition:
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.menu-icon.is-active {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, currentColor 18%, transparent);
}

/* ── 共同滚动区 ─────────────────────────────────────────────── */
.scroll-region {
    position: relative;
    display: flex;
    min-height: 0;
    flex: 1;
    flex-direction: column;
}

.scroll-region > .sidebar-scroll-group {
    margin-top: 4px;
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
}

/* 边栏滚动条：默认弱化，悬停时增强 */
.sidebar-scroll-group::-webkit-scrollbar {
    width: 4px;
}

.sidebar-scroll-group::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: transparent;
    transition: background 180ms ease;
}

.sidebar-scroll-group:hover::-webkit-scrollbar-thumb {
    background: var(--color-border);
}

.sidebar-scroll-group:hover::-webkit-scrollbar-thumb:hover {
    background: var(--color-border-strong);
}

/* 顶部/底部渐隐遮罩 */
.scroll-fade {
    position: absolute;
    right: 0;
    left: 0;
    z-index: 2;
    height: 22px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 200ms ease;
}

.scroll-fade-top {
    top: 0;
    background: linear-gradient(
        to bottom,
        var(--color-sidebar-bg),
        transparent
    );
}

.scroll-fade-bottom {
    bottom: 0;
    background: linear-gradient(
        to top,
        var(--color-sidebar-bg),
        transparent
    );
}

.scroll-fade.is-visible {
    opacity: 1;
}

/* 紧凑模式：智能对话按钮上的折叠标记 */
.compact-panel-trigger {
    position: absolute;
    right: 6px;
    top: 50%;
    display: none;
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: var(--color-primary-400);
    transform: translateY(-50%);
    transition: transform 200ms var(--motion-ease);
}

.compact-panel-trigger.is-open {
    transform: translateY(-50%) rotate(45deg);
    background: var(--color-primary-600);
}

.conversation-panel {
    display: flex;
    flex-direction: column;
    margin-top: 14px;
    margin-bottom: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--color-border-subtle);
}

.conversation-heading {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 900;
}

.conversation-heading button {
    display: inline-flex;
    height: 30px;
    align-items: center;
    gap: 5px;
    border-radius: 8px;
    padding: 0 10px;
    color: var(--color-primary-700);
    font-size: 14px;
    font-weight: 900;
    transition:
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.conversation-heading button:hover {
    background: var(--color-primary-50);
}

/* 会话分组 */
.conversation-group {
    margin-top: 8px;
}

.conversation-group:first-of-type {
    margin-top: 0;
}

.conversation-group-label {
    margin: 0 0 4px;
    padding: 0 9px;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 0.3px;
}

.conversation-list {
    display: grid;
    gap: 3px;
}

/* 会话项：当前会话淡蓝背景 + 左侧高亮条 */
.conversation-item {
    position: relative;
    display: grid;
    min-width: 0;
    grid-template-columns: minmax(0, 1fr) auto auto;
    align-items: center;
    gap: 6px;
    border-radius: 8px;
    padding: 8px 9px 8px 12px;
    text-align: left;
    cursor: pointer;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
    transition:
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.conversation-item:hover {
    background: var(--color-surface-hover);
    color: var(--color-primary-700);
}

.conversation-item.is-active {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.conversation-item.is-active::before {
    content: "";
    position: absolute;
    left: 0;
    top: 50%;
    width: 3px;
    height: 16px;
    border-radius: 999px;
    background: var(--color-primary-600);
    transform: translateY(-50%);
}

.conversation-item span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.conversation-item small {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.conversation-delete {
    display: grid;
    width: 20px;
    height: 20px;
    place-items: center;
    border-radius: 4px;
    color: var(--color-text-tertiary);
    opacity: 0;
    transition:
        opacity 160ms var(--motion-ease),
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.conversation-delete svg {
    width: 13px;
    height: 13px;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 1.6;
}

.conversation-item:hover .conversation-delete,
.conversation-item.is-active .conversation-delete {
    opacity: 1;
}

.conversation-delete:hover {
    color: var(--color-text-secondary);
    background: var(--color-surface-hover);
}

.conversation-empty {
    margin: 10px 0 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

/* 账户区在线状态圆点 */
.account-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    flex: 0 0 6px;
    border-radius: 999px;
    background: var(--color-border-strong);
}

.account-dot.is-online {
    background: var(--color-success);
}

/* ── 三阶段折叠动画 ─────────────────────────────────────── */
/* 收起：内容先淡出，宽度再收缩 */
aside.phase-collapsing {
    overflow: hidden;
}

aside.phase-collapsing .sidebar-detail,
aside.phase-collapsed .sidebar-detail {
    opacity: 0;
    transform: translateX(-4px);
    transition:
        opacity 120ms ease,
        transform 160ms var(--motion-ease);
    pointer-events: none;
}

/* 展开：宽度先展开，内容再淡入 */
aside.phase-expanding {
    overflow: hidden;
}

aside.phase-expanding .sidebar-detail {
    opacity: 1;
    transform: translateX(0);
    transition:
        opacity 180ms ease,
        transform 180ms var(--motion-ease);
}

/* 紧凑模式下隐藏文字（v-show 兜底） */
aside.phase-collapsed .sidebar-detail {
    display: none;
}
</style>
