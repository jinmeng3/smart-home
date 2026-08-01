<script setup lang="ts">
import { computed } from "vue";
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

interface MenuItem {
    icon: string;
    label: string;
    path?: string;
}

const menuItems: MenuItem[] = [
    { icon: "chat", label: "智能对话", path: "/" },
    { icon: "home", label: "全屋总览" },
    { icon: "room", label: "房间控制" },
    { icon: "device-management", label: "设备管理", path: "/devices" },
    { icon: "scene", label: "场景模式" },
    { icon: "automation", label: "自动化" },
    { icon: "energy", label: "能耗分析" },
    { icon: "security", label: "安防中心" },
    { icon: "settings", label: "设置", path: "/settings" },
];

const activeLabel = computed(() => {
    if (route.path === "/settings") {
        return "设置";
    }

    if (route.path === "/devices") {
        return "设备管理";
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
</script>

<template>
    <aside
        class="page-enter-stagger relative min-h-0 overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-sidebar-background)] py-5 shadow-soft transition-[padding] duration-500 ease-out"
        :class="store.sidebarCollapsed ? 'px-2' : 'px-4'"
    >
        <div
            class="mb-6 flex items-center"
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
                <strong class="block truncate text-xl font-extrabold text-blue-700">
                    Orion
                </strong>
                <span class="block truncate text-xs font-semibold text-slate-500">
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

        <nav class="grid gap-1">
            <button
                v-for="item in menuItems"
                :key="item.label"
                class="motion-button relative flex h-11 items-center rounded-lg text-sm font-bold text-slate-700 transition duration-200 hover:bg-blue-50 hover:text-blue-700"
                :class="[
                    activeLabel === item.label
                        ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-700)] shadow-sm'
                        : '',
                    store.sidebarCollapsed ? 'justify-center px-0' : 'gap-3 px-3',
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
                class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-100 to-blue-700 text-sm font-extrabold text-white"
            >
                {{ accountInitial }}
            </div>
            <div v-show="!store.sidebarCollapsed" class="min-w-0">
                <strong class="block truncate text-sm">
                    {{ authStore.isAuthenticated ? account.username : "访客用户" }}
                </strong>
                <span class="block truncate text-xs text-slate-500">
                    {{ authStore.isAuthenticated ? account.email : "登录后同步个人信息" }}
                </span>
            </div>
            <span v-show="!store.sidebarCollapsed" class="ml-auto text-slate-400">
                ˅
            </span>
        </button>
    </aside>
</template>
