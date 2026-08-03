<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { useHomeStore } from "../../stores/home";
import { statusColorMap } from "../../constants/status-colors";
import type { DashboardDevice } from "../../types/device";
import type { SemanticStatus } from "../../types/theme";
import { getDeviceRuntimeStatus } from "../../utils/device";
import { deviceTypeIconMap, getDeviceStatusLabel } from "../device/deviceMeta";
import { formatDeviceTimestamp } from "../../utils/date";
import AnimatedList from "../animation/AnimatedList.vue";
import AnimatedStatus from "../animation/AnimatedStatus.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";

const store = useHomeStore();
const lastFocusedElement = ref<HTMLElement | null>(null);

const statusClass = (device: DashboardDevice) => {
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

const statusLabel = (device: DashboardDevice) =>
    getDeviceStatusLabel(device.status);

const openDevice = async (device: DashboardDevice, event: MouseEvent) => {
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
        class="motion-card page-enter-stagger min-w-0 shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-3 shadow-soft"
        style="animation-delay: 260ms"
    >
        <div class="mb-2 flex items-center justify-between">
            <h2
                class="flex items-center gap-2 text-sm font-extrabold text-slate-800"
            >
                <SvgIcon name="device-management" size="sm" />
                设备清单
            </h2>
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
                class="motion-button device-row grid h-12 min-w-0 grid-cols-[28px_minmax(0,1fr)_minmax(70px,92px)] items-center gap-2 rounded-lg border border-[var(--color-border-subtle)] bg-[var(--color-panel-background)] px-2 text-left transition hover:border-[var(--color-border-default)] hover:bg-[var(--color-surface-subtle)]"
                type="button"
                @click="openDevice(device, $event)"
            >
                <span
                    class="grid h-6 w-6 place-items-center rounded-lg bg-slate-100 text-[var(--color-primary-700)]"
                >
                    <SvgIcon :name="deviceTypeIconMap[device.type]" size="sm" />
                </span>
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
        <RouterLink
            class="motion-button mt-2 block text-center text-xs font-bold text-blue-600"
            to="/devices"
            >查看全部设备</RouterLink
        >

        <BaseSmartModal
            :model-value="store.deviceDrawerOpen"
            icon="device-management"
            title="设备详情"
            width="560px"
            @update:model-value="$event ? undefined : closeDrawer()"
        >
            <template #header>
                <header class="device-modal-header">
                    <h2>设备详情</h2>
                    <button
                        type="button"
                        aria-label="关闭"
                        @click="closeDrawer"
                    >
                        <SvgIcon name="close" size="sm" />
                    </button>
                </header>
            </template>
            <section v-if="store.selectedDevice" class="device-detail-card">
                <div class="device-detail-summary">
                    <div class="device-detail-icon">
                        <img
                            v-if="store.selectedDevice.image"
                            :src="store.selectedDevice.image"
                            alt=""
                        />
                        <SvgIcon
                            v-else
                            :name="deviceTypeIconMap[store.selectedDevice.type]"
                            size="lg"
                        />
                    </div>
                    <div class="device-detail-title">
                        <strong>{{ store.selectedDevice.name }}</strong>
                        <span>{{ store.selectedDevice.type }}</span>
                        <em>
                            <i :class="`is-${store.selectedDevice.status}`"></i>
                            {{ statusLabel(store.selectedDevice) }}
                        </em>
                    </div>
                </div>
                <dl>
                    <div>
                        <dt>房间</dt>
                        <dd>{{ store.selectedDevice.room }}</dd>
                    </div>
                    <div>
                        <dt>品牌</dt>
                        <dd>{{ store.selectedDevice.brand ?? "暂无" }}</dd>
                    </div>
                    <div>
                        <dt>连接方式</dt>
                        <dd>{{ store.selectedDevice.connection ?? "暂无" }}</dd>
                    </div>
                    <div>
                        <dt>固件版本</dt>
                        <dd>{{ store.selectedDevice.firmware ?? "暂无" }}</dd>
                    </div>
                    <div>
                        <dt>最后同步</dt>
                        <dd>
                            {{
                                formatDeviceTimestamp(store.selectedDevice.updatedAt)
                            }}
                        </dd>
                    </div>
                </dl>
            </section>
            <template #footer></template>
        </BaseSmartModal>
    </section>
</template>

<style scoped>
.device-row {
    animation: device-highlight 600ms var(--motion-ease) both;
}

.device-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 18px 22px;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-card-bg);
}

.device-modal-header h2 {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 900;
}

.device-modal-header button {
    display: grid;
    width: 34px;
    height: 34px;
    place-items: center;
    border: 0;
    border-radius: 8px;
    color: var(--color-text-tertiary);
    background: transparent;
}

.device-modal-header button:hover {
    color: var(--color-text-primary);
    background: var(--color-surface-hover);
}

.device-detail-card {
    display: grid;
    gap: 16px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 18px;
}

.device-detail-summary {
    display: grid;
    grid-template-columns: 104px minmax(0, 1fr);
    align-items: center;
    gap: 16px;
}

.device-detail-icon {
    display: grid;
    width: 104px;
    height: 104px;
    place-items: center;
    overflow: hidden;
    border-radius: 10px;
    background: linear-gradient(
        180deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
    color: var(--color-primary-700);
}

.device-detail-icon img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.device-detail-title {
    display: grid;
    min-width: 0;
    gap: 7px;
}

.device-detail-title strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-detail-title span {
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 700;
}

.device-detail-title em {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-default);
    border-radius: 999px;
    background: var(--color-surface-subtle);
    padding: 5px 10px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-style: normal;
    font-weight: 900;
}

.device-detail-title i {
    width: 8px;
    height: 8px;
    border-radius: 999px;
}

.device-detail-title i.is-online {
    background: var(--color-success);
}
.device-detail-title i.is-running {
    background: var(--color-info);
}
.device-detail-title i.is-warning {
    background: var(--color-warning);
}
.device-detail-title i.is-offline {
    background: var(--color-text-muted);
}

.device-detail-card dl {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin: 0;
}

.device-detail-card dl > div {
    min-width: 0;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-panel-secondary);
    padding: 12px;
}

.device-detail-card dl > div:last-child {
    grid-column: 1 / -1;
}

.device-detail-card dt {
    margin-bottom: 7px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 800;
}

.device-detail-card dd {
    overflow: hidden;
    margin: 0;
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
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
