<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, shallowRef, watch } from "vue";
import { useHomeStore } from "../../stores/home";
import { statusColorMap } from "../../constants/status-colors";
import type { DashboardDevice } from "../../types/device";
import type { SemanticStatus } from "../../constants/status-colors";
import { getDeviceRuntimeStatus } from "../../utils/device";
import { deviceTypeIconMap, deviceTypeLabelMap, getDeviceStatusLabel, getDeviceTypeIcon, getDeviceTypeLabel } from "../device/deviceMeta";
import AnimatedList from "../animation/AnimatedList.vue";
import AnimatedStatus from "../animation/AnimatedStatus.vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";

const props = withDefaults(
    defineProps<{
        highlightNames?: string[];
    }>(),
    {
        highlightNames: () => [],
    },
);

const store = useHomeStore();
const lastFocusedElement = shallowRef<HTMLElement | null>(null);

/** AI 引用设备时短暂高亮（边框 + 背景，约 1.2 秒） */
const highlightedIds = shallowRef<Set<string>>(new Set());
let highlightTimer = 0;
watch(
    () => props.highlightNames,
    (names) => {
        window.clearTimeout(highlightTimer);
        const next = new Set<string>();
        for (const device of store.devices) {
            if (names.includes(device.name)) {
                next.add(device.id);
            }
        }
        highlightedIds.value = next;
        if (next.size > 0) {
            highlightTimer = window.setTimeout(() => {
                highlightedIds.value = new Set();
            }, 1200);
        }
    },
);

const isHighlighted = (id: string) => highlightedIds.value.has(id);
const MAX_DISPLAY_DEVICES = 4;
const displayDevices = computed(() => store.devices.slice(0, MAX_DISPLAY_DEVICES));

const platformToneMap: Record<string, string> = {
    "Home Assistant": "orange",
    Matter: "blue",
    Zigbee: "green",
    MQTT: "purple",
};

/** 语义状态 → 中文文案 */
const semanticLabelMap: Record<string, string> = {
    online: "在线",
    offline: "离线",
    running: "运行中",
    warning: "告警",
    error: "异常",
    success: "正常",
};

/** 运行时状态（中文文案） */
const runtimeStatusLabel = (device: DashboardDevice) => {
    const status = getDeviceRuntimeStatus(device);
    return semanticLabelMap[status] ?? getDeviceStatusLabel(device.status);
};

/** 状态文字颜色类 */
const statusTextClass = (device: DashboardDevice) => {
    const status = getDeviceRuntimeStatus(device) as SemanticStatus;
    return statusColorMap[status]?.textClass ?? "text-[var(--color-text-tertiary)]";
};

/** 状态圆点颜色类（直接用 statusColorMap 的 dotClass） */
const statusDotClass = (device: DashboardDevice) => {
    const status = getDeviceRuntimeStatus(device) as SemanticStatus;
    return statusColorMap[status]?.dotClass ?? "bg-[var(--color-text-muted)]";
};

/** 状态徽章类（详情弹窗内使用） */
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

const formattedUpdatedAt = computed(() => {
    const value = store.selectedDevice?.updatedAt;
    if (!value) return "暂无";
    const time = new Date(value);
    if (Number.isNaN(time.getTime())) return value;
    const now = new Date();
    const diffMin = Math.floor((now.getTime() - time.getTime()) / 60000);
    const pad = (n: number) => String(n).padStart(2, "0");
    if (diffMin < 1) return "刚刚";
    if (diffMin < 60) return `${diffMin} 分钟前`;
    const clock = `${pad(time.getHours())}:${pad(time.getMinutes())}`;
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    if (time.toDateString() === now.toDateString()) return `今天 ${clock}`;
    if (time.toDateString() === yesterday.toDateString()) return `昨天 ${clock}`;
    if (time.getFullYear() === now.getFullYear()) {
        return `${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${clock}`;
    }
    return `${time.getFullYear()}-${pad(time.getMonth() + 1)}-${pad(time.getDate())} ${clock}`;
});

const detailText = computed(() => {
    const device = store.selectedDevice;
    if (!device) return "";
    return `${device.room} · ${runtimeStatusLabel(device) ?? device.status}${device.value ? ` · ${device.value}` : ""} · ${formattedUpdatedAt.value}`;
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
        class="motion-card page-enter-stagger min-w-0 shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] px-3 py-2.5 shadow-soft"
        style="animation-delay: 260ms"
    >
        <div class="mb-2.5 flex items-center justify-between gap-2">
            <h2
                class="flex items-center gap-2 text-[15px] font-extrabold text-[var(--color-text-primary)]"
            >
                <SvgIcon name="device-management" size="sm" />
                设备清单
            </h2>
            <!-- 紧凑统计标签：圆点 + 数字 + 文字，芯片式设计 -->
            <span class="device-summary">
                <span class="summary-chip is-online">
                    <i></i>{{ store.deviceSummary.online }} 在线
                </span>
                <span class="summary-chip is-offline">
                    <i></i>{{ store.deviceSummary.offline }} 离线
                </span>
            </span>
        </div>

        <AnimatedList tag="div" name="recent-list" class="grid gap-1">
            <button
                v-for="device in displayDevices"
                :key="device.id"
                v-memo="[
                    device.id,
                    device.status,
                    device.value,
                    device.online,
                    store.selectedDevice?.id === device.id,
                    isHighlighted(device.id),
                ]"
                class="motion-button device-row grid h-11 min-w-0 grid-cols-[30px_minmax(0,1fr)_auto] items-center gap-2 rounded-lg px-2 text-left transition-colors duration-150 hover:bg-[var(--color-surface-subtle)]"
                :class="{ 'is-referenced': isHighlighted(device.id), 'is-selected': store.selectedDevice?.id === device.id }"
                type="button"
                @click="openDevice(device, $event)"
            >
                <span
                    class="device-icon grid h-7 w-7 place-items-center rounded-lg bg-[var(--color-primary-50)] text-[var(--color-primary-700)]"
                >
                    <SvgIcon :name="getDeviceTypeIcon(device.icon || device.type)" size="sm" />
                </span>
                <strong class="truncate text-[13px] font-bold text-[var(--color-text-secondary)]">{{
                    device.name
                }}</strong>
                <!-- 状态：圆点 + 中文文字 -->
                <span
                    class="inline-flex items-center gap-1.5 text-xs font-bold"
                    :class="statusTextClass(device)"
                >
                    <i class="status-dot" :class="statusDotClass(device)"></i>
                    {{ runtimeStatusLabel(device) }}
                </span>
            </button>
        </AnimatedList>

        <!-- 查看全部设备：卡片底部轻量文字入口 -->
        <RouterLink
            class="mt-1.5 block border-t border-[var(--color-border-subtle)] px-1 pt-2 text-right text-xs font-bold text-[var(--color-primary-600)] transition-colors duration-150 hover:text-[var(--color-primary-700)]"
            to="/devices"
            >查看全部设备 →</RouterLink
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
                            :name="getDeviceTypeIcon(store.selectedDevice.icon || store.selectedDevice.type)"
                            size="lg"
                        />
                    </div>
                    <div class="device-detail-title">
                        <strong>{{ store.selectedDevice.name }}</strong>
                        <span class="device-type-badge">{{
                            getDeviceTypeLabel(store.selectedDevice.type)
                        }}</span>
                        <span
                            class="device-status-badge"
                            :class="statusClass(store.selectedDevice)"
                        >
                            <AnimatedStatus
                                :status="getDeviceRuntimeStatus(store.selectedDevice)"
                                :label="store.selectedDevice.value ?? statusLabel(store.selectedDevice)"
                            />
                        </span>
                    </div>
                </div>
                <dl>
                    <div>
                        <dt><SvgIcon name="room" size="sm" />房间</dt>
                        <dd class="is-room">{{ store.selectedDevice.room }}</dd>
                    </div>
                    <div>
                        <dt><SvgIcon name="layers" size="sm" />品牌</dt>
                        <dd>{{ store.selectedDevice.brand ?? "暂无" }}</dd>
                    </div>
                    <div>
                        <dt><SvgIcon name="plug" size="sm" />连接方式</dt>
                        <dd>
                            <em
                                v-if="store.selectedDevice.connection"
                                class="platform-tone"
                                :class="`is-${platformToneMap[store.selectedDevice.connection] ?? 'blue'}`"
                                >{{ store.selectedDevice.connection }}</em
                            >
                            <span v-else>暂无</span>
                        </dd>
                    </div>
                    <div>
                        <dt><SvgIcon name="refresh" size="sm" />固件版本</dt>
                        <dd class="is-firmware">{{
                            store.selectedDevice.firmware ?? "暂无"
                        }}</dd>
                    </div>
                    <div>
                        <dt><SvgIcon name="clock" size="sm" />最后同步</dt>
                        <dd class="is-sync">{{ formattedUpdatedAt }}</dd>
                    </div>
                </dl>
            </section>
            <template #footer></template>
        </BaseSmartModal>
    </section>
</template>

<style scoped>
/* 紧凑统计标签：芯片式设计 */
.device-summary {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    font-weight: 800;
}

.summary-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    padding: 2px 8px;
}

.summary-chip.is-online {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.summary-chip.is-offline {
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.summary-chip i {
    width: 5px;
    height: 5px;
    flex: 0 0 5px;
    border-radius: 999px;
}

.summary-chip.is-online i {
    background: var(--color-success);
}

.summary-chip.is-offline i {
    background: var(--color-text-muted);
}

/* 设备行：默认无边框无背景，悬停才显示背景 */
.device-row.is-referenced {
    border-color: var(--color-primary-400);
    background: color-mix(in srgb, var(--color-primary-50) 60%, transparent);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
    animation: device-reference-pulse 1200ms var(--motion-ease) both;
}

.device-row.is-selected {
    background: var(--color-primary-50);
}

@keyframes device-reference-pulse {
    0% {
        background: var(--color-primary-50);
    }
    60% {
        background: var(--color-surface-hover);
    }
    100% {
        background: transparent;
    }
}

/* 状态圆点 */
.status-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    flex: 0 0 6px;
    border-radius: 999px;
}

.device-icon :deep(svg) {
    width: 16px;
    height: 16px;
}

.device-icon :deep(use) {
    pointer-events: none;
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

/* ── 设备详情卡片 ── */

.device-detail-card {
    display: grid;
    gap: 18px;
    padding: 20px;
}

.device-detail-summary {
    display: grid;
    grid-template-columns: 80px minmax(0, 1fr);
    align-items: center;
    gap: 14px;
    padding-bottom: 18px;
    border-bottom: 1px solid var(--color-border);
}

.device-detail-icon {
    display: grid;
    width: 80px;
    height: 80px;
    place-items: center;
    overflow: hidden;
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        var(--color-primary-100),
        var(--color-primary-50)
    );
    box-shadow: 0 4px 12px var(--color-focus-ring);
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
    gap: 6px;
}

.device-detail-title strong {
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-type-badge {
    width: fit-content;
    border-radius: 999px;
    background: var(--color-primary-50);
    padding: 2px 10px;
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 800;
}

.device-status-badge {
    display: inline-flex;
    width: fit-content;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 800;
    line-height: 1.4;
}

/* ── 详情字段列表 ── */

.device-detail-card dl {
    display: grid;
    gap: 0;
    margin: 0;
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-surface-subtle);
}

.device-detail-card dl > div {
    display: flex;
    min-width: 0;
    align-items: baseline;
    justify-content: space-between;
    gap: 10px;
    padding: 11px 14px;
    transition: background 160ms var(--motion-ease);
}

.device-detail-card dl > div + div {
    border-top: 1px solid var(--color-border-subtle);
}

.device-detail-card dl > div:hover {
    background: var(--color-card-bg);
}

.device-detail-card dt {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    flex: 0 0 auto;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 750;
}

.device-detail-card dt svg {
    flex: 0 0 auto;
}

.device-detail-card dl > div:nth-child(1) dt svg {
    color: var(--color-primary-600);
}

.device-detail-card dl > div:nth-child(2) dt svg {
    color: var(--color-success);
}

.device-detail-card dl > div:nth-child(3) dt svg {
    color: var(--color-warning);
}

.device-detail-card dl > div:nth-child(4) dt svg {
    color: var(--tone-purple);
}

.device-detail-card dl > div:nth-child(5) dt svg {
    color: var(--color-info);
}

.device-detail-card dd {
    overflow: hidden;
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    text-align: right;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-detail-card dd.is-room {
    color: var(--color-primary-700);
}

.device-detail-card dd.is-firmware {
    color: var(--tone-purple);
}

.device-detail-card dd.is-sync {
    color: var(--color-info);
}

.platform-tone {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 12px;
    font-style: normal;
    font-weight: 900;
}

.platform-tone.is-orange {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.platform-tone.is-blue {
    background: var(--color-info-soft);
    color: var(--color-info);
}

.platform-tone.is-green {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.platform-tone.is-purple {
    background: var(--color-focus-ring);
    color: var(--tone-purple);
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
