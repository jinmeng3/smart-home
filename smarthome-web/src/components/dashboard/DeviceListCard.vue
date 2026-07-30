<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { useHomeStore } from "../../stores/home";
import { statusColorMap } from "../../constants/status-colors";
import type { Device } from "../../types/device";
import type { SemanticStatus } from "../../types/theme";
import { getDeviceRuntimeStatus } from "../../utils/device";
import AnimatedList from "../animation/AnimatedList.vue";
import AnimatedStatus from "../animation/AnimatedStatus.vue";

const store = useHomeStore();
const lastFocusedElement = ref<HTMLElement | null>(null);

const statusClass = (device: Device) => {
    const status = getDeviceRuntimeStatus(device) as SemanticStatus;
    const colors = statusColorMap[status];

    return [
        "device-status-label",
        `status-${status}`,
        colors.textClass,
        colors.backgroundClass,
        colors.borderClass,
    ];
};

const detailText = computed(() => {
    const device = store.selectedDevice;

    if (!device) {
        return "点击设备查看详情";
    }

    return `${device.room} · ${device.status}${device.value ? ` · ${device.value}` : ""} · ${device.updatedAt}`;
});

const openDevice = async (device: Device, event: MouseEvent) => {
    lastFocusedElement.value = event.currentTarget as HTMLElement;
    store.selectDevice(device);
    await nextTick();
};

const closeDrawer = () => {
    store.closeDeviceDrawer();
    lastFocusedElement.value?.focus();
};

const handleKeydown = (event: KeyboardEvent) => {
    if (event.key === "Escape" && store.deviceDrawerOpen) {
        closeDrawer();
    }
};

onMounted(() => {
    window.addEventListener("keydown", handleKeydown);
});

onBeforeUnmount(() => {
    window.removeEventListener("keydown", handleKeydown);
});
</script>

<template>
    <section
        class="motion-card page-enter-stagger min-w-0 shrink-0 rounded-xl border border-blue-100 bg-white/90 p-3 shadow-soft"
        style="animation-delay: 260ms"
    >
        <div class="mb-2 flex items-center justify-between">
            <h2 class="text-sm font-extrabold text-slate-800">▣ 设备清单</h2>
            <a class="motion-button text-xs font-bold text-blue-600" href="#"
                >更多</a
            >
        </div>

        <div class="mb-2 flex justify-between text-sm text-slate-500">
            <span
                >在线
                <strong class="text-[var(--color-success)]"
                    >{{ store.deviceSummary.online }} 台</strong
                ></span
            >
            <span
                >离线
                <strong class="text-[var(--color-text-tertiary)]"
                    >{{ store.deviceSummary.offline }} 台</strong
                ></span
            >
        </div>

        <AnimatedList tag="div" name="recent-list" class="grid gap-2">
            <button
                v-for="device in store.devices"
                :key="device.id"
                v-memo="[
                    device.id,
                    device.status,
                    device.value,
                    device.online,
                    store.selectedDevice?.id === device.id,
                ]"
                class="motion-button device-row grid h-10 min-w-0 grid-cols-[26px_minmax(0,1fr)_minmax(66px,88px)] items-center gap-2 rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-panel-background)] px-2 text-left transition hover:border-[var(--color-border-default)] hover:bg-[var(--color-surface-subtle)]"
                type="button"
                @click="openDevice(device, $event)"
            >
                <span
                    class="grid h-6 w-6 place-items-center rounded-lg bg-slate-100 text-xs"
                    >{{ device.type.slice(0, 1).toUpperCase() }}</span
                >
                <strong class="truncate text-sm text-slate-700">{{
                    device.name
                }}</strong>
                <em
                    class="truncate rounded-md px-2 py-1 text-center text-xs not-italic font-bold"
                    :class="statusClass(device)"
                >
                    <AnimatedStatus
                        :status="getDeviceRuntimeStatus(device)"
                        :label="device.value ?? device.status"
                    />
                </em>
            </button>
        </AnimatedList>

        <p
            class="mt-2 truncate rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-panel-secondary)] px-3 py-2 text-xs text-slate-500"
        >
            {{ detailText }}
        </p>
        <a
            class="motion-button mt-2 block text-center text-xs font-bold text-blue-600"
            href="#"
            >查看全部设备</a
        >

        <Transition name="drawer">
            <div
                v-if="store.deviceDrawerOpen"
                class="fixed inset-0 z-40 bg-slate-900/20 backdrop-blur-[1px]"
                @click.self="closeDrawer"
            >
                <aside
                    class="absolute right-3 top-3 h-[calc(100%-24px)] w-80 rounded-2xl bg-white p-5 shadow-2xl"
                >
                    <button
                        class="motion-button absolute right-4 top-4 text-slate-400"
                        type="button"
                        @click="closeDrawer"
                    >
                        ×
                    </button>
                    <h3 class="text-lg font-extrabold">设备详情</h3>
                    <div
                        v-if="store.selectedDevice"
                        class="mt-5 grid gap-3 text-sm"
                    >
                        <strong class="text-base">{{
                            store.selectedDevice.name
                        }}</strong>
                        <p class="text-slate-500">
                            房间：{{ store.selectedDevice.room }}
                        </p>
                        <p class="text-slate-500">
                            状态：{{ store.selectedDevice.status }}
                        </p>
                        <p class="text-slate-500">
                            数值：{{ store.selectedDevice.value ?? "无" }}
                        </p>
                        <p class="text-slate-500">
                            更新时间：{{ store.selectedDevice.updatedAt }}
                        </p>
                    </div>
                </aside>
            </div>
        </Transition>
    </section>
</template>

<style scoped>
.device-row {
    animation: device-highlight 600ms var(--motion-ease) both;
}

@keyframes device-highlight {
    0% {
        background: var(--color-surface-hover);
    }
    100% {
        background: var(--color-panel-background);
    }
}
</style>
