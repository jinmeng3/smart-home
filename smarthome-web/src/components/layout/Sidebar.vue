<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import { useHomeStore } from "../../stores/home";
import { useSettingsStore } from "../../stores/settings";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const avatarLoadError = ref(false);

interface MenuItem {
    icon: string;
    label: string;
    path?: string;
}

const menuItems: MenuItem[] = [
    { icon: "chat", label: "智能对话", path: "/" },
    { icon: "home", label: "全屋总览", path: "/overview" },
    { icon: "room", label: "房间控制", path: "/rooms" },
    { icon: "device-management", label: "设备管理", path: "/devices" },
    { icon: "scene", label: "场景模式", path: "/scenes" },
    { icon: "automation", label: "自动化", path: "/automations" },
    // { icon: "energy", label: "能耗分析" },
    // { icon: "security", label: "安防中心" },
    { icon: "settings", label: "设置", path: "/settings" },
];

const activeLabel = computed(() => {
    if (route.path === "/rooms") {
        return "房间控制";
    }

    if (route.path === "/settings") {
        return "设置";
    }

    if (route.path === "/devices") {
        return "设备管理";
    }

    if (route.path === "/scenes") {
        return "场景模式";
    }

    if (route.path === "/overview") {
        return "全屋总览";
    }

    if (route.path === "/automations") {
        return "自动化";
    }

    return "智能对话";
});

const account = computed(() => settingsStore.settings.account);
const accountInitial = computed(() =>
    authStore.isAuthenticated
        ? account.value.username.trim().slice(0, 1).toUpperCase()
        : "访",
);

const selectMenu = async (item: MenuItem) => {
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
};
</script>

<template>
    <aside
        class="page-enter-stagger relative flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-sidebar-bg)] py-5 shadow-soft transition-[padding] duration-500 ease-out"
        :class="store.sidebarCollapsed ? 'px-2' : 'px-4'"
    >
        <div
            class="mb-6 flex shrink-0 items-center"
            :class="store.sidebarCollapsed ? 'justify-center' : 'gap-3'"
        >
            <button
                class="motion-button grid h-11 w-11 shrink-0 place-items-center overflow-hidden rounded-full bg-blue-50 shadow-lg shadow-blue-500/20 ring-1 ring-blue-100"
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
            <div v-show="!store.sidebarCollapsed" class="min-w-0">
                <strong
                    class="block truncate text-xl font-extrabold text-blue-700"
                >
                    Orion
                </strong>
                <span
                    class="block truncate text-xs font-semibold text-slate-500"
                >
                    Home Assistant
                </span>
            </div>
            <button
                v-show="!store.sidebarCollapsed"
                class="motion-button ml-auto grid h-8 w-8 place-items-center rounded-lg text-slate-500 hover:bg-blue-50 hover:text-blue-700"
                type="button"
                title="折叠菜单"
                @click="store.toggleSidebar"
            >
                ‹
            </button>
        </div>

        <nav class="grid shrink-0 gap-1">
            <button
                v-for="item in menuItems"
                :key="item.label"
                class="motion-button relative flex h-11 items-center rounded-lg text-sm font-bold text-slate-700 transition duration-200 hover:bg-blue-50 hover:text-blue-700"
                :class="[
                    activeLabel === item.label
                        ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-700)] shadow-sm'
                        : '',
                    store.sidebarCollapsed
                        ? 'justify-center px-0'
                        : 'gap-3 px-3',
                ]"
                type="button"
                :title="item.label"
                @click="selectMenu(item)"
            >
                <span
                    v-if="activeLabel === item.label && !store.sidebarCollapsed"
                    class="absolute left-0 h-6 w-1 rounded-full bg-[var(--color-primary-600)]"
                ></span>
                <SvgIcon :name="item.icon" />
                <span v-show="!store.sidebarCollapsed" class="truncate">
                    {{ item.label }}
                </span>
            </button>
        </nav>

        <section
            v-show="route.path === '/' && !store.sidebarCollapsed"
            class="conversation-panel"
        >
            <div class="conversation-heading">
                <span>最近会话</span>
                <button type="button" @click="startConversation">
                    <SvgIcon name="plus" size="sm" />
                    新建
                </button>
            </div>
            <div
                v-if="store.recentConversations.length"
                class="conversation-list"
            >
                <button
                    v-for="conversation in store.recentConversations"
                    :key="conversation.id"
                    class="conversation-item"
                    type="button"
                    @click="openConversation(conversation.id)"
                >
                    <span>{{ conversation.title }}</span>
                    <small>{{ conversation.time }}</small>
                </button>
            </div>
            <p v-else class="conversation-empty">暂无会话</p>
        </section>

        <button
            class="mt-auto flex shrink-0 items-center overflow-hidden border border-[var(--color-border)] bg-[var(--color-card-bg)] shadow-sm transition-[width,height,transform,border-radius,padding] duration-500 ease-out"
            :class="
                store.sidebarCollapsed
                    ? 'h-11 w-11 self-center justify-center gap-0 rounded-full p-0'
                    : 'h-[74px] w-full justify-start gap-3 rounded-xl p-3'
            "
            type="button"
            @click="authStore.openLogin"
        >
            <img
                v-if="
                    authStore.isAuthenticated &&
                    account.avatarUrl &&
                    !avatarLoadError
                "
                class="h-10 w-10 shrink-0 rounded-full object-cover"
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
            <div v-show="!store.sidebarCollapsed" class="min-w-0">
                <strong class="block truncate text-sm">
                    {{
                        authStore.isAuthenticated
                            ? account.username
                            : "访客用户"
                    }}
                </strong>
                <span class="block truncate text-xs text-slate-500">
                    {{
                        authStore.isAuthenticated
                            ? account.email
                            : "登录后同步个人信息"
                    }}
                </span>
            </div>
            <span
                v-show="!store.sidebarCollapsed"
                class="ml-auto text-slate-400"
            >
                ˅
            </span>
        </button>
    </aside>
</template>

<style scoped>
.conversation-panel {
    display: flex;
    min-height: 0;
    flex: 1 1 auto;
    flex-direction: column;
    margin-top: 14px;
    margin-bottom: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--color-border-subtle);
}

.conversation-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 900;
}

.conversation-heading button {
    display: inline-flex;
    height: 28px;
    align-items: center;
    gap: 4px;
    border-radius: 8px;
    padding: 0 8px;
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 900;
}

.conversation-list {
    display: grid;
    min-height: 0;
    gap: 6px;
    margin-top: 8px;
    overflow-y: auto;
    padding-right: 2px;
}

.conversation-item {
    display: grid;
    min-width: 0;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    border-radius: 8px;
    padding: 8px 9px;
    text-align: left;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
}

.conversation-item:hover {
    background: var(--color-surface-hover);
    color: var(--color-primary-700);
}

.conversation-item span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.conversation-item small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.conversation-empty {
    margin: 10px 0 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}
</style>
