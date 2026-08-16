<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Room, RoomDeviceCard } from "../../types/room";
import type { RoomEnvironmentItem } from "./RoomDetailPanel.vue";
import { isDeviceActive } from "../../utils/device";
import { keyToCategory } from "./roomMeta";

const props = defineProps<{
    selected: Room | undefined;
    loading: boolean;
    devices: RoomDeviceCard[];
    environment: RoomEnvironmentItem[];
    temperature: number;
    activeCategory: string;
    currentScene?: string;
}>();

const emit = defineEmits<{
    select: [room: Room];
    toggle: [device: RoomDeviceCard];
    "update:temperature": [value: number];
    "update:activeCategory": [value: string];
    open: [dialog: "scene" | "devices" | "environment"];
}>();

const onlineCount = computed(() => props.selected?.onlineCount ?? 0);
const deviceCount = computed(() => props.selected?.deviceCount ?? 0);

const categoryDeviceCounts = computed(() => {
    const counts: Record<string, number> = { "全部设备": props.devices.length };
    for (const cat of ["灯光", "空调", "窗帘", "插座"]) {
        counts[cat] = 0;
    }
    for (const device of props.devices) {
        const catName = keyToCategory[device.key];
        if (catName && counts[catName] !== undefined) {
            counts[catName]++;
        }
    }
    return counts;
});

const categories = [
    { name: "全部设备", icon: "chevron-down" },
    { name: "灯光", icon: "light" },
    { name: "空调", icon: "air-conditioner" },
    { name: "窗帘", icon: "curtain" },
    { name: "插座", icon: "plug" },
    { name: "更多", icon: "chevron-down" },
];

const selectCategory = (name: string) => {
    emit("update:activeCategory", name);
    if (name === "更多") emit("open", "devices");
};

const offlineDevices = computed(() =>
    props.devices.filter((d) => d.status === "offline" || d.status === "warning"),
);
</script>

<template>
    <section class="quick-control" :class="{ 'is-loading': loading }">
        <aside class="room-sidebar" :style="{ '--theme-color': selected?.themeColor || '#3478f6' }">
            <template v-if="selected">
                <h1>{{ selected.name }}</h1>
                <p class="sidebar-meta">
                    <span><SvgIcon name="online-device" size="sm" />{{ onlineCount }}/{{ deviceCount }} 台设备在线</span>
                    <span class="sidebar-comfort" :class="selected.comfort >= 84 ? 'is-comfort' : 'is-good'">
                        舒适度 {{ selected.comfort }}
                    </span>
                    <span v-if="currentScene" class="sidebar-scene">
                        <SvgIcon name="scene" size="sm" />{{ currentScene }}
                    </span>
                </p>
            </template>
            <template v-else>
                <h1>房间快捷控制</h1>
                <p class="sidebar-meta">{{ loading ? "正在加载..." : "暂无房间" }}</p>
            </template>
        </aside>

        <main v-if="selected" :key="selected.id" class="control-content">
            <div class="control-header">
                <div>
                    <h2 class="control-title">设备控制</h2>
                    <p class="control-context">{{ onlineCount }} 台在线 · 舒适度 {{ selected?.comfort ?? 0 }}<template v-if="currentScene"> · {{ currentScene }}</template></p>
                </div>
                <button
                    class="scene-btn"
                    type="button"
                    @click="$emit('open', 'scene')"
                >
                    <SvgIcon name="scene" size="sm" />
                    <span>{{ currentScene || '场景' }}</span>
                </button>
            </div>

            <nav class="category-bar" aria-label="设备分类">
                <button
                    v-for="category in categories"
                    :key="category.name"
                    :class="{ active: activeCategory === category.name }"
                    type="button"
                    @click="selectCategory(category.name)"
                >
                    <SvgIcon :name="category.icon" size="sm" />
                    <span>{{ category.name }}</span>
                    <span class="cat-count" :class="{ 'is-zero': categoryDeviceCounts[category.name] === 0 }">{{ categoryDeviceCounts[category.name] }}</span>
                </button>
            </nav>

            <section class="control-section">
                <h2>常用设备</h2>
                <div class="device-grid">
                    <article
                        v-for="device in devices"
                        :key="device.id"
                        class="device-card"
                        :class="{
                            featured: device.key === 'airConditioner',
                            disabled: device.status === 'offline',
                            'is-warning': device.status === 'warning',
                            'is-running': device.status === 'running',
                        }"
                    >
                        <header>
                            <span class="device-icon" :class="{ 'is-on': isDeviceActive(device.status) }" :style="{ '--device-color': device.color || '#6b7280' }">
                                <SvgIcon :name="device.icon" size="sm" />
                            </span>
                            <div>
                                <strong>{{ device.name }}</strong>
                                <small>{{ selected.name }}</small>
                            </div>
                            <button
                                class="switch"
                                :class="{ enabled: isDeviceActive(device.status) }"
                                :aria-label="`切换${device.name}`"
                                type="button"
                                @click="$emit('toggle', device)"
                            ><span></span></button>
                        </header>

                        <div v-if="device.key === 'light'" class="range-row">
                            <span>{{ isDeviceActive(device.status) ? '亮度 60%' : '已关闭' }}</span><i v-if="isDeviceActive(device.status)"><b></b></i>
                        </div>
                        <div v-else-if="device.key === 'television'" class="range-row">
                            <span>音量</span><i class="volume"><b></b></i><em>30%</em>
                        </div>
                        <div v-else-if="device.key === 'airConditioner'" class="temperature-row">
                            <b>{{ temperature }}°C</b>
                            <button type="button" @click="$emit('update:temperature', Math.max(16, temperature - 1))">−</button>
                            <button type="button" @click="$emit('update:temperature', Math.min(30, temperature + 1))">＋</button>
                        </div>
                        <div v-else-if="device.key === 'airPurifier'" class="purifier-row">
                            <span>风速</span><b>自动</b><SvgIcon name="refresh" size="sm" />
                        </div>
                        <div v-else class="device-status-text">
                            <span class="status-label" :class="isDeviceActive(device.status) ? 'is-on' : (device.status === 'warning' ? 'is-warning' : 'is-off')">
                                {{ isDeviceActive(device.status) ? '已开启' : (device.status === 'warning' ? '异常' : '已关闭') }}
                            </span>
                        </div>
                    </article>
                </div>
            </section>

            <section class="control-section environment-section">
                <h2>环境数据</h2>
                <div class="environment-grid">
                    <article
                        v-for="item in environment"
                        :key="item.name"
                        role="button"
                        tabindex="0"
                        @click="$emit('open', 'environment')"
                        @keydown.enter="$emit('open', 'environment')"
                    >
                        <small>{{ item.name }}</small>
                        <strong>{{ item.value }}</strong>
                        <span v-if="item.statusLabel" class="env-status-label">{{ item.statusLabel }}</span>
                        <svg :class="item.tone" viewBox="0 0 66 22" aria-hidden="true">
                            <polyline :points="item.points" />
                        </svg>
                    </article>
                </div>
            </section>

            <section v-if="offlineDevices.length > 0" class="control-section alert-section">
                <h2>需关注设备 <small>{{ offlineDevices.length }}</small></h2>
                <div class="alert-list">
                    <div
                        v-for="device in offlineDevices"
                        :key="device.id"
                        class="alert-item"
                        :class="{ 'is-warning': device.status === 'warning' }"
                    >
                        <span class="alert-icon">
                            <SvgIcon :name="device.icon" size="sm" />
                        </span>
                        <span class="alert-name">{{ device.name }}</span>
                        <span class="alert-status">{{ device.status === 'warning' ? '异常' : '离线' }}</span>
                    </div>
                </div>
            </section>
        </main>

        <div v-else class="empty-state">
            {{ loading ? "正在加载房间..." : "暂无房间数据" }}
        </div>
    </section>
</template>

<style scoped>
.quick-control {
    display: grid;
    min-width: 0;
    min-height: 0;
    grid-template-columns: 164px minmax(0, 1fr);
    gap: 10px;
    align-self: stretch;
    overflow: hidden auto;
}

.quick-control.is-loading {
    opacity: 0.72;
}

.room-sidebar {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 16px 14px;
    box-shadow: var(--shadow-card);
}

.room-sidebar h1 {
    margin: 0 0 6px;
    color: var(--color-primary-700);
    font-size: 20px;
    font-weight: 900;
    line-height: 1.3;
}

.sidebar-meta {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin: 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
    line-height: 1.5;
}

.sidebar-meta svg {
    color: var(--color-text-muted);
    margin-right: 3px;
}

.sidebar-comfort {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    width: fit-content;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 800;
}

.sidebar-comfort.is-comfort {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.sidebar-comfort.is-good {
    background: color-mix(in srgb, var(--theme-color, #3478f6) 12%, transparent);
    color: var(--color-primary-600);
}

.control-content {
    min-width: 0;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 18px;
    background: var(--color-card-bg);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    box-shadow: var(--shadow-card);
}

/* === 控制区头部 === */
.control-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 14px;
}

.control-title {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 17px;
    font-weight: 900;
}

.control-context {
    margin: 3px 0 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.scene-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 32px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 800;
    cursor: pointer;
    transition: 120ms var(--motion-ease);
}

.scene-btn:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    transform: translateY(-1px);
}

.scene-btn:active {
    transform: scale(0.97);
}

.scene-btn:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
}

.scene-btn svg {
    width: 16px;
    height: 16px;
}

.category-bar {
    display: flex;
    gap: 6px;
    padding-bottom: 16px;
    overflow-x: auto;
    overscroll-behavior: contain;
    scrollbar-width: none;
}

.category-bar::-webkit-scrollbar {
    display: none;
}

.category-bar button {
    display: inline-flex;
    flex: 0 0 auto;
    height: 32px;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
    box-shadow: none;
    transition: 120ms var(--motion-ease);
    cursor: pointer;
    white-space: nowrap;
}

.category-bar button:first-child {
    min-width: 0;
}

.category-bar button svg {
    color: var(--color-primary-600);
}

.category-bar button:first-child svg {
    order: 2;
    color: var(--color-text-tertiary);
}

.cat-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    border-radius: 999px;
    background: var(--color-surface-subtle);
    padding: 0 5px;
    color: var(--color-text-muted);
    font-size: 10px;
    font-weight: 800;
    line-height: 1;
}

.cat-count.is-zero {
    opacity: 0.45;
}

.category-bar button.active .cat-count {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.sidebar-scene {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    width: fit-content;
    border-radius: 999px;
    background: var(--tone-purple-soft);
    padding: 2px 8px;
    color: var(--tone-purple);
    font-size: 12px;
    font-weight: 800;
}

.sidebar-scene svg {
    width: 12px;
    height: 12px;
}

/* === 键盘焦点样式 === */
.room-sidebar button:focus-visible,
.category-bar button:focus-visible,
.device-card:focus-visible,
.environment-grid article:focus-visible,
.quick-control .switch:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
}

.category-bar button:hover,
.category-bar button.active {
    border-color: var(--color-primary-200);
    color: var(--color-primary-700);
    box-shadow: none;
    transform: translateY(-1px);
}

.control-section h2 {
    margin: 0 2px 10px;
    color: var(--color-text-primary);
    font-size: 17px;
    font-weight: 900;
}

.device-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.environment-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 10px;
}

.device-card,
.environment-grid article {
    min-width: 0;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
transition: 160ms var(--motion-ease);
}

.device-card {
    min-height: 90px;
    grid-column: span 1;
    padding: 8px 10px;
    transition: 160ms var(--motion-ease);
}

.device-card:hover {
    border-color: var(--color-primary-200);
    transform: translateY(-1px);
}

.device-card.featured {
    border-color: var(--color-primary-300);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.device-card.disabled {
    opacity: 0.68;
    border-color: var(--color-border);
}

.device-card.is-warning {
    border-color: var(--color-danger);
    background: var(--color-danger-soft);
}

.device-card.is-running {
    border-color: var(--color-primary-400);
    background: color-mix(in srgb, var(--color-primary-500) 6%, transparent);
}

.device-card.is-warning .device-icon {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.device-card.is-running .device-icon {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.device-card header {
    display: grid;
    grid-template-columns: 28px minmax(0, 1fr) auto;
    align-items: center;
    gap: 6px;
}

.device-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 7px;
    background: color-mix(in srgb, var(--device-color, #6b7280) 14%, transparent);
    color: var(--device-color, #6b7280);
    transition: transform 160ms var(--motion-ease), background-color 220ms var(--motion-ease), color 220ms var(--motion-ease);
}

.device-icon.is-on {
    transform: scale(1.05);
}

.device-card header div {
    display: grid;
    min-width: 0;
    gap: 1px;
}

.device-card strong,
.device-card small {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-card strong {
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 900;
}

.device-card small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.switch {
    width: 28px;
    height: 15px;
    border-radius: 999px;
    background: var(--color-text-muted);
    padding: 2px;
    transition: 160ms var(--motion-ease);
}

.switch span {
    display: block;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 1px 3px rgb(15 23 42 / 24%);
    transition: 160ms var(--motion-ease);
}

.switch.enabled {
    background: var(--color-primary-600);
}

.switch.enabled span {
    transform: translateX(13px);
}

.device-status-text {
    display: flex;
    align-items: center;
    min-height: 22px;
    padding-top: 2px;
}

.status-label {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 800;
}

.status-label.is-on {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.status-label.is-off {
    background: var(--color-surface-subtle);
    color: var(--color-text-muted);
}

.status-label.is-warning {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.range-row,
.temperature-row,
.purifier-row {
    display: flex;
    min-height: 24px;
    align-items: flex-end;
    gap: 4px;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.range-row i {
    position: relative;
    height: 5px;
    flex: 1;
    overflow: hidden;
    border-radius: 999px;
    background: var(--color-surface-subtle);
}

.range-row i::before {
    display: block;
    width: 64%;
    height: 100%;
    background: var(--color-primary-600);
    content: "";
}

.range-row i b {
    position: absolute;
    top: -3px;
    left: 62%;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: var(--color-primary-600);
}

.range-row .volume::before {
    width: 54%;
}

.range-row em {
    color: var(--color-text-secondary);
    font-style: normal;
}

.temperature-row {
    align-items: flex-end;
}

.temperature-row > b {
    margin-right: auto;
    color: var(--color-text-primary);
    font-size: 15px;
}

.temperature-row button {
    display: grid;
    width: 20px;
    height: 20px;
    place-items: center;
    border-radius: 5px;
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    font-size: 14px;
    font-weight: 700;
}

.purifier-row b {
    color: var(--color-text-secondary);
}

.purifier-row svg {
    margin-left: auto;
    color: var(--color-primary-500);
}

.environment-section {
    margin-top: 16px;
}

.alert-section {
    margin-top: 12px;
}

.alert-section h2 small {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    margin-left: 6px;
    border-radius: 999px;
    background: var(--color-danger);
    padding: 0 5px;
    color: #fff;
    font-size: 10px;
    font-weight: 900;
    vertical-align: middle;
}

.alert-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.alert-item {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 32px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 4px 10px;
    background: var(--color-card-bg);
}

.alert-item.is-warning {
    border-color: var(--color-danger-border);
    background: var(--color-danger-soft);
}

.alert-icon {
    display: grid;
    width: 24px;
    height: 24px;
    flex: 0 0 24px;
    place-items: center;
    border-radius: 6px;
    background: var(--color-surface-subtle);
    color: var(--color-text-muted);
}

.alert-item.is-warning .alert-icon {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.alert-name {
    min-width: 0;
    flex: 1;
    overflow: hidden;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 800;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.alert-status {
    flex: 0 0 auto;
    border-radius: 999px;
    padding: 1px 8px;
    font-size: 11px;
    font-weight: 800;
    background: var(--color-surface-subtle);
    color: var(--color-text-muted);
}

.alert-item.is-warning .alert-status {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.environment-grid article {
    position: relative;
    min-height: 72px;
    overflow: hidden;
    padding: 12px 14px;
}

.environment-grid small,
.environment-grid strong {
    position: relative;
    z-index: 1;
    display: block;
}

.environment-grid small {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 750;
}

.environment-grid strong {
    margin-top: 3px;
    color: var(--color-text-primary);
    font-size: 19px;
    font-weight: 900;
}

.environment-grid svg {
    position: absolute;
    right: 12px;
    bottom: 10px;
    width: 58px;
    height: 20px;
    fill: none;
    stroke: var(--color-primary-500);
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 2;
}

.environment-grid article .env-status-label {
    position: relative;
    z-index: 1;
    display: block;
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.environment-grid svg.green {
    stroke: var(--color-success);
}
.environment-grid svg.orange {
    stroke: var(--color-warning);
}
.environment-grid svg.purple {
    stroke: var(--tone-purple);
}

.empty-state {
    display: grid;
    min-height: 100%;
    place-items: center;
    background: var(--color-page-bg);
    color: var(--color-text-tertiary);
    font-size: 15px;
    font-weight: 800;
}

@media (max-width: 1280px) {
    .device-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .environment-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}

@media (max-width: 1450px) {
    .quick-control {
        grid-template-columns: 148px minmax(0, 1fr);
    }
    .room-sidebar {
        padding: 14px 10px;
    }
    .control-content {
        padding-right: 14px;
        padding-left: 14px;
    }
}

@media (max-width: 860px) {
    .quick-control {
        grid-template-columns: 1fr;
    }
    .room-sidebar {
        border: 1px solid var(--color-border);
        border-radius: 12px;
        padding: 14px 16px;
    }
    .room-sidebar h1 {
        margin-bottom: 4px;
    }
    .sidebar-meta {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 8px;
    }
    .control-content {
        padding: 16px;
    }
}

@media (max-width: 620px) {
    .device-grid,
    .environment-grid {
        grid-template-columns: 1fr;
    }
}

@media (prefers-reduced-motion: reduce) {
    .quick-control *,
    .quick-control *::before,
    .quick-control *::after {
        transition-duration: 1ms !important;
    }
    .device-icon.is-on {
        transform: none;
    }
}
</style>
