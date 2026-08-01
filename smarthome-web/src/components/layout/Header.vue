<script setup lang="ts">
import { computed, ref } from "vue";
import { useSettingsStore } from "../../stores/settings";
import { useAuthStore } from "../../stores/auth";

const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const avatarLoadError = ref(false);
const username = computed(
    () => authStore.isAuthenticated
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
        class="page-enter-stagger flex h-[88px] shrink-0 items-center justify-between border-b border-blue-100/70 px-6 py-4"
        style="animation-delay: 80ms"
    >
        <div>
            <h1 class="text-xl font-extrabold tracking-normal text-slate-900">
                {{ greeting }}，{{ username }}
            </h1>
            <p class="date-chip">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M7 3v4M17 3v4M4 9h16" />
                    <path d="M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z" />
                    <path d="M8 13h3M8 16h6" />
                </svg>
                <span>今天是 {{ today }}</span>
            </p>
        </div>

        <div class="flex items-center gap-3">
            <label class="header-search-native">
                <span aria-hidden="true">⌕</span>
                <input :disabled="!authStore.isAuthenticated" type="search" :placeholder="authStore.isAuthenticated ? '搜索设备、场景或房间' : '登录后可搜索'" />
            </label>
            <button v-if="authStore.isAuthenticated" aria-label="通知，3 条未读" class="notification-button" type="button">
                <span aria-hidden="true">●</span>
                <small>3</small>
            </button>
            <button class="rounded-full" type="button" title="登录或查看账户" @click="authStore.openLogin">
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
  background: rgb(255 255 255 / 72%);
  box-shadow: 0 1px 2px rgb(15 23 42 / 5%);
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
