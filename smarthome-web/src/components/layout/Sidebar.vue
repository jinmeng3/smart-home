<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useHomeStore } from "../../stores/home";
import { useSettingsStore } from "../../stores/settings";
import { useAuthStore } from "../../stores/auth";
import AnimatedList from "../animation/AnimatedList.vue";

const store = useHomeStore();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const sidebarScrolled = ref(false);

const menuItems = [
    { icon: "✦", label: "智能对话", path: "/" },
    { icon: "▦", label: "全屋总览" },
    { icon: "▣", label: "房间控制" },
    { icon: "☷", label: "设备管理" },
    { icon: "♙", label: "场景模式" },
    { icon: "⌘", label: "自动化" },
    { icon: "▥", label: "能耗分析" },
    { icon: "◇", label: "安防中心" },
    { icon: "⚙", label: "设置", path: "/settings" },
];

const activeLabel = computed(() =>
    route.path === "/settings" ? "设置" : store.activeMenu,
);
const activeIndex = computed(() =>
    Math.max(
        menuItems.findIndex((item) => item.label === activeLabel.value),
        0,
    ),
);
const account = computed(() => settingsStore.settings.account);
const accountInitial = computed(() =>
    authStore.isAuthenticated
        ? account.value.username.trim().slice(0, 1).toUpperCase()
        : "访",
);

const selectMenu = async (item: (typeof menuItems)[number]) => {
    store.setActiveMenu(item.label);

    if (item.path === "/" && route.path === "/") {
        if (!authStore.isAuthenticated) {
            authStore.openLogin();
            return;
        }
        await store.startNewConversation();
    }

    if (item.path && item.path !== route.path) {
        await router.push(item.path);
    }
};

const selectConversation = async (conversationId: string) => {
    store.setActiveMenu("智能对话");

    if (route.path !== "/") {
        await router.push("/");
    }

    await store.loadConversation(conversationId);
};

const updateSidebarScroll = (event: Event) => {
    sidebarScrolled.value = (event.currentTarget as HTMLElement).scrollTop > 8;
};
</script>

<template>
    <aside
        class="page-enter-stagger relative min-h-0 overflow-hidden rounded-2xl border border-[var(--color-border-default)] border-r-[var(--color-border-default)] bg-[var(--color-sidebar-background)] py-5 shadow-soft transition-[padding] duration-500 ease-out"
        :class="store.sidebarCollapsed ? 'px-2' : 'px-4'"
        style="animation-delay: 0ms"
    >
        <div
            class="flex items-center transition-[gap,height,margin] duration-500 ease-out"
            :class="
                store.sidebarCollapsed
                    ? 'relative mb-4 h-11 gap-0'
                    : 'mb-5 h-[58px] justify-start gap-3'
            "
        >
            <button
                class="motion-button grid shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-lg font-bold text-white shadow-lg shadow-blue-500/20 transition-[width,height,transform] duration-300 hover:scale-105"
                :class="
                    store.sidebarCollapsed
                        ? 'absolute left-1/2 h-10 w-10 -translate-x-1/2'
                        : 'h-10 w-10'
                "
                type="button"
                :title="store.sidebarCollapsed ? '展开菜单' : 'Orion Home'"
                @click="store.sidebarCollapsed && store.toggleSidebar()"
            >
                ✦
            </button>

            <strong
                class="block overflow-hidden whitespace-nowrap text-lg font-extrabold leading-7 text-blue-700 transition-[width,opacity,transform] duration-300 ease-out"
                :class="
                    store.sidebarCollapsed
                        ? 'w-0 translate-x-2 opacity-0'
                        : 'w-[132px] translate-x-0 opacity-100'
                "
            >
                Orion Home
            </strong>

            <button
                class="motion-button ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-500 transition-[width,opacity,transform,background-color,color] duration-300 hover:bg-blue-50 hover:text-blue-700"
                :class="
                    store.sidebarCollapsed
                        ? 'w-0 scale-75 overflow-hidden opacity-0'
                        : 'w-8 scale-100 opacity-100'
                "
                type="button"
                title="折叠菜单"
                @click="store.toggleSidebar"
            >
                ‹
            </button>
        </div>

        <div
            class="sidebar-scroll overflow-y-auto overscroll-contain"
            :class="
                store.sidebarCollapsed
                    ? 'h-[calc(100%-128px)] pr-0'
                    : 'h-[calc(100%-154px)] pr-1'
            "
            @scroll.passive="updateSidebarScroll"
        >
            <nav class="relative grid gap-1">
                <span
                    v-if="!store.sidebarCollapsed && activeIndex !== 0"
                    class="absolute left-0 h-7 w-1 rounded-full bg-[var(--color-primary-600)] transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]"
                    :style="{
                        transform: `translateY(${activeIndex * 48 + 8}px)`,
                    }"
                ></span>

                <button
                    v-for="item in menuItems"
                    :key="item.label"
                    class="motion-button group flex h-11 items-center rounded-lg text-sm font-semibold text-slate-600 transition duration-200 hover:bg-blue-50 hover:text-blue-700 active:scale-[0.98]"
                    :class="[
                        activeLabel === item.label
                            ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-700)] shadow-sm'
                            : '',
                        item.path === '/'
                            ? 'sticky top-0 z-20 bg-[var(--color-sidebar-background)]'
                            : '',
                        item.path === '/' && sidebarScrolled
                            ? 'border border-blue-200 bg-white text-blue-800 shadow-[0_8px_22px_rgba(37,99,235,0.16)] ring-1 ring-blue-100/80 backdrop-blur sticky-chat-button'
                            : '',
                        store.sidebarCollapsed
                            ? 'justify-center px-0'
                            : 'gap-3 px-3 pl-5 text-left',
                    ]"
                    type="button"
                    :title="item.label"
                    @click="selectMenu(item)"
                >
                    <span
                        class="w-5 text-center transition duration-200 group-hover:translate-x-0.5 group-hover:scale-110"
                        >{{ item.icon }}</span
                    >
                    <span v-show="!store.sidebarCollapsed" class="truncate">{{
                        item.label
                    }}</span>
                </button>
            </nav>

            <section
                class="mt-5 overflow-hidden transition-[max-height,opacity,transform] duration-300 ease-out"
                :class="
                    store.sidebarCollapsed
                        ? 'max-h-0 translate-y-2 opacity-0'
                        : 'max-h-[360px] translate-y-0 opacity-100'
                "
            >
                <h2
                    class="mb-3 px-2 text-xs font-bold uppercase tracking-wide text-slate-400"
                >
                    最近会话
                </h2>
                <AnimatedList tag="div" name="recent-list">
                    <button
                        v-for="conversation in store.recentConversations"
                        :key="conversation.id"
                        class="motion-button recent-conversation mb-2 grid w-full grid-cols-[30px_minmax(0,1fr)_auto] items-center gap-2 rounded-lg px-2 py-2 text-left transition hover:bg-slate-100"
                        :class="
                            store.activeSessionId === conversation.id
                                ? 'active-conversation'
                                : ''
                        "
                        type="button"
                        :disabled="!authStore.isAuthenticated"
                        @click="selectConversation(conversation.id)"
                    >
                        <span
                            class="recent-conversation-icon"
                            aria-hidden="true"
                        ></span>
                        <span
                            class="truncate text-sm font-medium text-slate-700"
                            >{{ conversation.title }}</span
                        >
                        <span class="text-xs text-slate-400">{{
                            conversation.time
                        }}</span>
                    </button>
                </AnimatedList>
            </section>
        </div>

        <button
            class="absolute bottom-5 flex items-center overflow-hidden border border-slate-200 bg-white shadow-sm transition-[left,right,width,height,transform,border-radius,padding] duration-500 ease-out"
            :class="
                store.sidebarCollapsed
                    ? 'left-1/2 h-11 w-11 -translate-x-1/2 justify-center gap-0 rounded-full p-0'
                    : 'left-4 right-4 h-[74px] translate-x-0 justify-start gap-3 rounded-xl p-3'
            "
            type="button"
            @click="authStore.openLogin"
        >
            <img
                v-if="authStore.isAuthenticated && account.avatarUrl"
                class="h-10 w-10 shrink-0 rounded-full object-cover"
                :src="account.avatarUrl"
                alt=""
            />
            <div
                v-else
                class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-rose-100 to-slate-700 text-sm font-extrabold text-white"
            >
                {{ accountInitial }}
            </div>
            <div
                class="min-w-0 overflow-hidden transition-[width,opacity,transform] duration-300 ease-out"
                :class="
                    store.sidebarCollapsed
                        ? 'w-0 translate-x-3 opacity-0'
                        : 'w-[132px] translate-x-0 opacity-100'
                "
            >
                <strong class="block truncate text-sm">{{
                    authStore.isAuthenticated ? account.username : "访客用户"
                }}</strong>
                <span class="block truncate text-xs text-slate-500">{{
                    authStore.isAuthenticated
                        ? account.email
                        : "登录后同步个人信息"
                }}</span>
            </div>
            <span
                class="ml-auto text-slate-400 transition-[width,opacity] duration-300 ease-out"
                :class="
                    store.sidebarCollapsed
                        ? 'w-0 opacity-0'
                        : 'w-auto opacity-100'
                "
                >⌄</span
            >
        </button>
    </aside>
</template>

<style scoped>
.sticky-chat-button {
    animation: sticky-chat-float 1.8s ease-in-out infinite;
}

.recent-conversation-icon {
    position: relative;
    display: block;
    width: 30px;
    height: 30px;
    border: 1px solid rgba(37, 99, 235, 0.16);
    border-radius: 8px;
    background: linear-gradient(180deg, #ffffff 0%, #eff6ff 100%);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
}

.active-conversation {
    border: 1px solid var(--color-border-default);
    color: var(--color-text-primary);
    background: var(--color-panel-background);
    box-shadow: 0 3px 12px rgb(15 23 42 / 6%);
}

.active-conversation::before {
    width: 3px;
    height: 20px;
    border-radius: 999px;
    background: var(--color-primary-400);
    content: "";
    position: absolute;
    left: -1px;
}

.recent-conversation {
    position: relative;
}

.recent-conversation-icon::before {
    content: "";
    position: absolute;
    left: 8px;
    top: 8px;
    width: 13px;
    height: 9px;
    border: 1.6px solid #2563eb;
    border-radius: 5px;
}

.recent-conversation-icon::after {
    content: "";
    position: absolute;
    left: 17px;
    top: 16px;
    width: 5px;
    height: 5px;
    border-right: 1.6px solid #2563eb;
    border-bottom: 1.6px solid #2563eb;
    transform: skewY(32deg);
}

.recent-conversation:hover .recent-conversation-icon,
.recent-conversation.active-conversation .recent-conversation-icon {
    border-color: rgba(37, 99, 235, 0.28);
    background: #ffffff;
}

@keyframes sticky-chat-float {
    0%,
    100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-1px);
    }
}
</style>
