<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import { useHomeStore } from "../../stores/home";
import { useSettingsStore } from "../../stores/settings";
import { useHouseholdStore } from "../../stores/households";
import {
    navigationItems,
    navigationGroups,
    type NavigationItem,
    type NavigationGroup,
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
const householdStore = useHouseholdStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const avatarLoadError = ref(false);

const menuItems = navigationItems;
const activeLabel = computed(
    () =>
        menuItems.find((item) => item.path === route.path)?.label ??
        "智能对话",
);

const isCollapsed = computed(
    () => store.sidebarCollapsed && props.mode === "full",
);

const account = computed(() => settingsStore.settings.account);
const accountInitial = computed(() =>
    authStore.isAuthenticated
        ? account.value.username.trim().slice(0, 1).toUpperCase()
        : "访",
);
const accountSubline = computed(() => {
    if (!authStore.isAuthenticated) return "登录后同步个人信息";
    const active = householdStore.activeHousehold;
    if (active) {
        return `${active.name} · ${
            active.role === "admin" ? "管理员" : "成员"
        }`;
    }
    return account.value.email;
});

/* === 最近会话分组 === */
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

const isActiveConversation = (id: string) => store.activeSessionId === id;

/* === 滚动渐隐 === */
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

watch(
    () => route.path,
    () => void nextTick(updateScrollState),
);

watch(
    () => store.recentConversations.length,
    () => void nextTick(updateScrollState),
);

/* === 紧凑模式会话浮层 === */
const compactPanelOpen = ref(false);
const toggleChatFromCompact = async () => {
    if (props.mode !== "compact") return;
    compactPanelOpen.value = !compactPanelOpen.value;
};

/* === 交互 === */
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

/* === 判断分组是否包含当前路由 === */
const isGroupActive = (group: NavigationGroup) =>
    group.items.some((item) => item.path === route.path);
</script>

<template>
    <aside
        :class="[
            `is-${mode}`,
            `phase-${props.phase}`,
            { 'is-collapsed': isCollapsed },
            isCollapsed ? 'px-2 py-4' : 'px-3 py-4',
        ]"
        class="page-enter-stagger relative flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-sidebar-bg)] shadow-soft transition-[width] duration-300 ease-out"
        :style="{ width: isCollapsed ? '72px' : '240px' }"
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

        <!-- === 品牌区（固定） === -->
        <div
            class="mb-5 flex shrink-0 items-center"
            :class="isCollapsed ? 'justify-center' : 'gap-3'"
        >
            <button
                class="brand-logo motion-button grid h-10 w-10 shrink-0 place-items-center overflow-hidden rounded-full bg-[var(--color-primary-50)] ring-1 ring-[var(--color-primary-100)] transition-transform duration-200 hover:scale-105"
                type="button"
                :title="isCollapsed ? '展开侧栏' : 'Orion Home'"
                @click="isCollapsed && store.toggleSidebar()"
            >
                <img
                    class="h-full w-full object-cover"
                    src="/orion-sidebar-icon.svg"
                    alt="Orion Home"
                />
            </button>
            <div
                v-show="!isCollapsed"
                class="min-w-0 sidebar-detail"
            >
                <strong
                    class="block truncate text-2xl font-extrabold text-[var(--color-primary-700)]"
                >
                    Orion
                </strong>
                <span
                    class="block truncate text-sm font-semibold text-[var(--color-text-tertiary)]"
                >
                    Home Assistant
                </span>
            </div>
            <button
                v-show="!isCollapsed"
                class="motion-button ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-lg text-[var(--color-text-tertiary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary-700)] sidebar-detail transition-all duration-150"
                type="button"
                :title="'折叠菜单'"
                @click="store.toggleSidebar"
            >
                <SvgIcon name="chevron-left" />
            </button>
        </div>

        <!-- === 内容区（滚动） === -->
        <div class="sidebar-content flex min-h-0 flex-1 flex-col overflow-hidden">
            <div class="scroll-region">
                <div
                    ref="scrollGroupRef"
                    class="sidebar-scroll-group min-h-0 flex-1 overflow-y-auto"
                    @scroll.passive="updateScrollState"
                >
                    <!-- 导航分组 -->
                    <template v-for="group in navigationGroups" :key="group.label">
                        <!-- 分组标题（折叠时隐藏） -->
                        <div
                            v-show="!isCollapsed"
                            class="group-header sidebar-detail"
                        >
                            <p class="group-label">{{ group.label }}</p>
                            <span class="group-line" aria-hidden="true"></span>
                        </div>

                        <nav class="group-nav grid gap-1">
                            <button
                                v-for="item in group.items"
                                :key="item.label"
                                class="motion-button nav-item relative flex items-center rounded-lg text-sm font-bold text-[var(--color-text-secondary)] transition-all duration-150"
                                :class="[
                                    activeLabel === item.label
                                        ? 'bg-[var(--color-primary-50)] text-[var(--color-primary-700)]'
                                        : 'hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-primary-700)]',
                                    isCollapsed ? 'justify-center gap-0 px-0' : 'gap-3 px-3',
                                ]"
                                type="button"
                                :title="isCollapsed ? item.label : ''"
                                :aria-label="item.label"
                                @focus="preloadMenu(item)"
                                @mouseenter="preloadMenu(item)"
                                @click="selectMenu(item)"
                            >
                                <!-- 左侧色条（当前项） -->
                                <span
                                    v-if="activeLabel === item.label"
                                    class="active-indicator absolute left-0 h-5 w-[3px] rounded-full"
                                    :style="{ background: item.tone }"
                                ></span>
                                <!-- 图标 -->
                                <span
                                    class="menu-icon"
                                    :class="{ 'is-active': activeLabel === item.label }"
                                    :style="
                                        activeLabel === item.label
                                            ? { background: item.soft, color: item.tone }
                                            : {}
                                    "
                                >
                                    <SvgIcon :name="item.icon" />
                                </span>
                                <!-- 标签 -->
                                <span
                                    v-show="!isCollapsed"
                                    class="truncate sidebar-detail"
                                >
                                    {{ item.label }}
                                </span>
                            </button>
                        </nav>
                    </template>

                    <!-- 最近会话 -->
                    <section
                        v-show="route.path === '/' && !compactPanelOpen"
                        class="conversation-panel"
                        :class="{ 'is-collapsed-mode': isCollapsed }"
                    >
                        <div
                            v-show="!isCollapsed"
                            class="conversation-heading sidebar-detail"
                        >
                            <span>最近会话</span>
                            <button type="button" @click="startConversation">
                                <SvgIcon name="plus" size="sm" />
                                新建
                            </button>
                        </div>

                        <!-- 折叠时只保留新建按钮 -->
                        <button
                            v-show="isCollapsed"
                            class="collapsed-new-chat"
                            type="button"
                            title="新建会话"
                            aria-label="新建会话"
                            @click="startConversation"
                        >
                            <SvgIcon name="plus" />
                        </button>

                        <template v-if="store.recentConversations.length && !isCollapsed">
                            <div
                                v-for="group in conversationGroups"
                                :key="group.key"
                                class="conversation-group"
                            >
                                <p class="conversation-group-label">
                                    {{ group.label }}
                                </p>
                                <div class="conversation-list">
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
                                            <SvgIcon name="delete" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </template>
                        <p
                            v-else-if="!store.recentConversations.length && !isCollapsed"
                            class="conversation-empty"
                        >
                            暂无会话
                        </p>
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

        <!-- === 账户区（固定底部） === -->
        <button
            class="mt-auto flex h-[68px] w-full shrink-0 items-center justify-start gap-3 overflow-hidden rounded-xl border border-[var(--color-border)] bg-gradient-to-r from-[var(--color-card-bg)] to-[var(--color-primary-50)] p-3 transition-all duration-150 hover:border-[var(--color-primary-200)] hover:shadow-sm"
            :class="isCollapsed ? 'justify-center px-0' : ''"
            type="button"
            :title="isCollapsed ? '账户' : ''"
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
                v-show="!isCollapsed"
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
                    {{ accountSubline }}
                </span>
            </div>
            <span
                v-show="!isCollapsed"
                class="ml-auto text-[var(--color-text-muted)] transition-transform duration-150 sidebar-detail"
            >
                <SvgIcon name="chevron-right" />
            </span>
        </button>
    </aside>
</template>

<style scoped>
/* === 布局重置 === */
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

/* === 桌面端手动折叠 === */
.is-collapsed {
    padding: 14px 10px !important;
}

.is-collapsed nav button {
    justify-content: center;
    gap: 0;
    padding: 0;
}

.is-collapsed nav button > span:first-child {
    left: -8px;
}

.is-collapsed .conversation-panel .conversation-heading,
.is-collapsed .conversation-group,
.is-collapsed .conversation-empty {
    display: none;
}

.is-collapsed .group-label {
    display: none;
}

.is-collapsed .sidebar-scroll-group {
    margin-top: 4px;
}

.is-collapsed > button:last-of-type {
    height: 52px;
    justify-content: center;
    padding: 6px;
}

/* === 侧边栏本体 === */
aside {
    will-change: transform, opacity;
    transition: padding 300ms cubic-bezier(0.22, 1, 0.36, 1);
    box-shadow:
        inset -1px 0 0 var(--color-border-subtle),
        var(--shadow-soft);
}

@media (prefers-reduced-motion: reduce) {
    aside,
    .brand-logo,
    .menu-icon,
    .nav-item,
    aside > button:last-of-type {
        transition-duration: 1ms;
    }
}

.brand-logo,
.menu-icon,
.nav-item,
aside > button:last-of-type {
    transition-duration: 300ms;
    transition-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
}

/* === 分组标题 === */
.group-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 18px 10px 7px;
}

.group-header:first-of-type {
    margin-top: 5px;
}

.group-line {
    width: 28px;
    height: 1px;
    background: linear-gradient(
        90deg,
        var(--color-border-subtle),
        transparent
    );
    opacity: 0.85;
}

.group-label {
    margin: 0;
    color: var(--color-text-tertiary);
    font-size: 11.5px;
    font-weight: 750;
    letter-spacing: 0.08em;
    opacity: 0.72;
    white-space: nowrap;
}

/* === 导航项 === */
.nav-item {
    position: relative;
    min-height: 44px;
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 0 10px;
    font-size: 14px;
    font-weight: 750;
    cursor: pointer;
    transition:
        background 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.nav-item:hover {
    background: var(--color-surface-hover);
}

.nav-item:focus-visible {
    outline: 2px solid var(--color-focus-ring);
    outline-offset: -1px;
}

.nav-item:has(.menu-icon.is-active) {
    border-color: color-mix(in srgb, var(--color-primary-200) 58%, transparent);
    box-shadow: inset 0 1px 0 color-mix(in srgb, white 52%, transparent);
}

.nav-item:hover .menu-icon {
    transform: scale(1.05);
}

/* 已激活项指示条 */
.active-indicator {
    left: 3px;
    width: 3px;
    height: 22px;
    box-shadow: 0 0 8px color-mix(in srgb, currentColor 26%, transparent);
    animation: active-stripe 260ms var(--motion-ease) both;
    transform-origin: left center;
}

@keyframes active-stripe {
    from {
        transform: scaleY(0.3);
        opacity: 0;
    }
    to {
        transform: scaleY(1);
        opacity: 1;
    }
}

/* === 菜单图标 === */
.menu-icon {
    display: grid;
    width: 32px;
    height: 32px;
    flex: 0 0 auto;
    place-items: center;
    border-radius: 10px;
    color: inherit;
    will-change: transform, background, color;
    transition:
        background 180ms var(--motion-ease),
        color 180ms var(--motion-ease),
        transform 180ms var(--motion-ease);
}

.menu-icon svg {
    transition: transform 160ms var(--motion-ease);
}

.nav-item:hover .menu-icon svg {
    transform: translateX(1px);
}

.menu-icon.is-active {
    box-shadow:
        inset 0 0 0 1px color-mix(in srgb, currentColor 18%, transparent),
        0 0 12px color-mix(in srgb, currentColor 12%, transparent);
}

.menu-icon.is-active svg {
    animation: icon-pop 280ms var(--motion-ease) both;
}

@keyframes icon-pop {
    0% { transform: scale(0.86); }
    100% { transform: scale(1); }
}

/* === 滚动区 === */
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

/* === 渐隐遮罩 === */
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

/* === 紧凑模式标记 === */
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

/* === 会话面板 === */
.conversation-panel {
    display: flex;
    flex-direction: column;
    margin-top: 12px;
    margin-bottom: 12px;
    padding-top: 10px;
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

/* 折叠时新建会话按钮 */
.collapsed-new-chat {
    display: grid;
    width: 100%;
    height: 40px;
    place-items: center;
    border-radius: 10px;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
    border: 1px solid var(--color-primary-200);
    transition:
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

.collapsed-new-chat:hover {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
    border-color: var(--color-primary-300);
    transform: scale(1.08);
}

.collapsed-new-chat:active {
    transform: scale(0.96);
}

.collapsed-new-chat svg {
    width: 20px;
    height: 20px;
}

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

/* SvgIcon 接管图标渲染，不再需要内联 SVG 样式 */

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

/* === 账户区 === */
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

/* === 三阶段折叠动画 === */
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

aside.phase-collapsed .sidebar-detail {
    display: none;
}

/* === 抽屉关闭按钮 === */
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
</style>
