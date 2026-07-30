<script setup lang="ts">
import { computed } from "vue";
import { Bell, Search } from "@element-plus/icons-vue";
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
            <el-input
                class="header-search"
                placeholder="搜索设备、场景或房间"
                :prefix-icon="Search"
            />
            <el-badge :value="3" class="rounded-full">
                <el-button :icon="Bell" circle />
            </el-badge>
            <div
                class="h-10 w-10 rounded-full border border-[var(--color-border-default)] bg-gradient-to-br from-blue-100 to-blue-600"
            ></div>
        </div>
    </header>
</template>
