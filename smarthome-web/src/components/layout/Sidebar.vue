<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import { useHomeStore } from "../../stores/home";
import { useSettingsStore } from "../../stores/settings";
import {
    navigationItems,
    type NavigationItem,
} from "../../router/navigation";
import SvgIcon from "../common/SvgIcon.vue";

const props = withDefaults(
    defineProps<{
        mode?: "full" | "compact" | "drawer";
    }>(),
    {
        mode: "full",
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
    if (props.mode === "drawer") emit("close");
};
</script>

<template>
    <aside
        :class="[`is-${mode}`]"
        class="page-enter-stagger relative flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border)] bg-[var(--color-sidebar-bg)] px-4 py-5 shadow-soft"
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
        <div class="mb-6 flex shrink-0 items-center gap-3">
            <button
                class="motion-button grid h-11 w-11 shrink-0 place-items-center overflow-hidden rounded-full bg-blue-50 shadow-lg shadow-blue-500/20 ring-1 ring-blue-100"
                type="button"
                title="Orion Home"
            >
                <img
                    class="h-full w-full object-cover"
                    src="/orion-sidebar-icon.svg"
                    alt="Orion Home"
                />
            </button>
            <div class="min-w-0">
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
        </div>

        <nav class="grid shrink-0 gap-1">
            <button
                v-for="item in menuItems"
                :key="item.label"
                class="motion-button relative flex h-11 items-center rounded-lg text-sm font-bold text-slate-700 transition duration-200 hover:bg-blue-50 hover:text-blue-700"
                :class="activeLabel === item.label ? 'gap-3 bg-[var(--color-primary-100)] px-3 text-[var(--color-primary-700)] shadow-sm' : 'gap-3 px-3'"
                type="button"
                :title="item.label"
                @focus="preloadMenu(item)"
                @mouseenter="preloadMenu(item)"
                @click="selectMenu(item)"
            >
                <span
                    v-if="activeLabel === item.label"
                    class="absolute left-0 h-6 w-1 rounded-full bg-[var(--color-primary-600)]"
                ></span>
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
                <span class="truncate">
                    {{ item.label }}
                </span>
            </button>
        </nav>

        <section
            v-show="route.path === '/'"
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
            class="mt-auto flex h-[74px] w-full shrink-0 items-center justify-start gap-3 overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-3 shadow-sm"
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
            <div class="min-w-0">
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
                class="ml-auto text-slate-400"
            >
                ˅
            </span>
        </button>
    </aside>
</template>

<style scoped>
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

.is-compact > button:last-of-type {
    height: 52px;
    justify-content: center;
    padding: 6px;
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
    transition:
        background 160ms var(--motion-ease),
        color 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

.menu-icon.is-active {
    box-shadow: inset 0 0 0 1px color-mix(in srgb, currentColor 18%, transparent);
}

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
