<script setup lang="ts">
import { computed, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import { useSettingsStore } from "../../stores/settings";
import { useAuthStore } from "../../stores/auth";

const props = defineProps<{
    compact?: boolean;
}>();

const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const avatarLoadError = ref(false);
const username = computed(() =>
    authStore.isAuthenticated
        ? settingsStore.settings.account.username.trim() || "用户"
        : "访客",
);
const avatarUrl = computed(() =>
    avatarLoadError.value ? null : settingsStore.settings.account.avatarUrl,
);
const accountInitial = computed(() => username.value.slice(0, 1).toUpperCase());
const today = new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
}).format(new Date());
const greeting = computed(() => {
    const hour = new Date().getHours();
    if (hour < 6) return "凌晨好";
    if (hour < 12) return "上午好";
    if (hour < 18) return "下午好";
    return "晚上好";
});
</script>

<template>
    <header
        class="home-header page-enter-stagger flex shrink-0 items-center justify-between px-6 transition-[height,box-shadow] duration-200"
        :class="compact ? 'home-header-compact' : 'h-[88px]'"
        style="animation-delay: 80ms"
    >
        <div
            class="min-w-0"
            :class="compact ? 'flex items-center gap-3' : ''"
        >
            <h1
                class="truncate font-extrabold text-[var(--color-text-primary)] transition-all duration-200"
                :class="compact ? 'text-base' : 'text-xl'"
            >
                {{ greeting }}，{{ username }}
            </h1>
            <Transition name="expand">
                <p v-if="!compact" class="date-chip">
                    <SvgIcon name="calendar" />
                    <span>今天是 {{ today }}</span>
                </p>
            </Transition>
        </div>

        <div class="flex items-center gap-3">
            <label class="header-search-native">
                <span aria-hidden="true">⌕</span>
                <input
                    :disabled="!authStore.isAuthenticated"
                    type="search"
                    :placeholder="
                        authStore.isAuthenticated
                            ? '搜索设备、场景或房间'
                            : '登录后可搜索'
                    "
                />
            </label>
            <button
                v-if="authStore.isAuthenticated"
                aria-label="通知，3 条未读"
                class="notification-button"
                type="button"
            >
                <span aria-hidden="true">●</span>
                <small>3</small>
            </button>
            <button
                class="rounded-full"
                type="button"
                title="登录或查看账户"
                @click="authStore.openLogin"
            >
                <img
                    v-if="authStore.isAuthenticated && avatarUrl"
                    class="h-10 w-10 rounded-full border border-[var(--color-border-default)] object-cover"
                    :src="avatarUrl"
                    alt=""
                    @error="avatarLoadError = true"
                />
                <div
                    v-else
                    class="grid h-10 w-10 place-items-center rounded-full border border-[var(--color-border-default)] bg-gradient-to-br from-blue-100 to-blue-600 text-sm font-bold text-white"
                >
                    {{ accountInitial }}
                </div>
            </button>
        </div>
    </header>
</template>

<style scoped>
.home-header {
    position: relative;
    z-index: 1;
    border-bottom: 1px solid var(--color-primary-200);
    background:
        radial-gradient(
            circle at 88% 20%,
            var(--color-primary-100),
            transparent 34%
        ),
        linear-gradient(
            110deg,
            var(--color-panel-background),
            var(--color-primary-50)
        );
    box-shadow: 0 8px 20px color-mix(in srgb, var(--color-primary-600) 8%, transparent);
}

/* 紧凑模式：已有对话时压缩顶部栏，保留标题、搜索、头像 */
.home-header-compact {
    height: 58px;
    box-shadow: 0 2px 10px color-mix(in srgb, var(--color-primary-600) 5%, transparent);
}

.header-search-native {
    display: flex;
    width: 240px;
    height: 34px;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    padding: 0 11px;
    color: var(--color-text-tertiary);
    background: var(--color-panel-background);
    box-shadow: var(--shadow-card);
}

.date-chip {
    display: inline-flex;
    height: 30px;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    padding: 0 11px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.date-chip svg {
    width: 16px;
    height: 16px;
    color: var(--color-primary-600);
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 2;
}

.header-search-native:focus-within {
    border-color: var(--color-border-focus);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.header-search-native input {
    min-width: 0;
    flex: 1;
    border: 0;
    color: var(--color-text-secondary);
    background: transparent;
    outline: 0;
}

.notification-button {
    position: relative;
    display: grid;
    width: 34px;
    height: 34px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 50%;
    color: var(--color-primary-600);
    background: var(--color-panel-background);
}

.notification-button small {
    position: absolute;
    top: -5px;
    right: -5px;
    min-width: 17px;
    height: 17px;
    border: 2px solid var(--color-panel-background);
    border-radius: 999px;
    color: white;
    font-size: 9px;
    line-height: 13px;
    background: var(--color-danger);
}
</style>
