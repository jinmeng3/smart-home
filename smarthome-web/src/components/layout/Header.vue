<script setup lang="ts">
import { computed } from "vue";
import { useSettingsStore } from "../../stores/settings";

const settingsStore = useSettingsStore();
const username = computed(
    () => settingsStore.settings.account.username.trim() || "用户",
);
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
                {{ greeting }}，{{ username }} 👋
            </h1>
            <p class="mt-1 text-sm font-medium text-slate-500">
                今天是 {{ today }}
            </p>
        </div>

        <div class="flex items-center gap-3">
            <label class="header-search-native">
                <span aria-hidden="true">⌕</span>
                <input type="search" placeholder="搜索设备、场景或房间" />
            </label>
            <button aria-label="通知，3 条未读" class="notification-button" type="button">
                <span aria-hidden="true">🔔</span>
                <small>3</small>
            </button>
            <div
                class="h-10 w-10 rounded-full border border-[var(--color-border-default)] bg-gradient-to-br from-blue-100 to-blue-600"
            ></div>
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
