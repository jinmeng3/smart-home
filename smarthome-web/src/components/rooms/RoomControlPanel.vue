<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Room, RoomDeviceCard } from "../../types/room";
import type { RoomEnvironmentItem } from "./RoomDetailPanel.vue";

defineProps<{
    rooms: Room[];
    selected: Room | undefined;
    loading: boolean;
    devices: RoomDeviceCard[];
    environment: RoomEnvironmentItem[];
    temperature: number;
    activeCategory: string;
}>();

const emit = defineEmits<{
    select: [room: Room];
    toggle: [device: RoomDeviceCard];
    "update:temperature": [value: number];
    "update:activeCategory": [value: string];
    open: [dialog: "scene" | "devices" | "environment"];
}>();

const categories = [
    { name: "全部设备", icon: "chevron-down" },
    { name: "灯光", icon: "light" },
    { name: "空调", icon: "air-conditioner" },
    { name: "窗帘", icon: "curtain" },
    { name: "插座", icon: "plug" },
    { name: "场景", icon: "scene" },
    { name: "更多...", icon: "more" },
];

const selectCategory = (name: string) => {
    emit("update:activeCategory", name);
    if (name === "场景") emit("open", "scene");
    if (name === "更多...") emit("open", "devices");
};
</script>

<template>
    <section class="quick-control" :class="{ 'is-loading': loading }">
        <aside class="room-sidebar">
            <h1>房间快捷控制</h1>
            <nav aria-label="房间列表">
                <button
                    v-for="room in rooms"
                    :key="room.id"
                    :class="{ active: selected?.id === room.id }"
                    type="button"
                    @click="$emit('select', room)"
                >
                    {{ room.name }}
                </button>
            </nav>
        </aside>

        <main v-if="selected" class="control-content">
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
                </button>
            </nav>

            <section class="control-section">
                <h2>常用设备</h2>
                <div class="device-grid">
                    <article
                        v-for="device in devices"
                        :key="device.name"
                        class="device-card"
                        :class="{
                            featured: device.key === 'airConditioner',
                            disabled: !selected.deviceStates[device.key],
                        }"
                    >
                        <header>
                            <span class="device-icon">
                                <SvgIcon :name="device.icon" size="sm" />
                            </span>
                            <div>
                                <strong>{{ device.name }}</strong>
                                <small>{{ selected.name }}</small>
                            </div>
                            <button
                                class="switch"
                                :class="{ enabled: selected.deviceStates[device.key] }"
                                :aria-label="`切换${device.name}`"
                                type="button"
                                @click="$emit('toggle', device)"
                            ><span></span></button>
                        </header>

                        <div v-if="device.key === 'light'" class="range-row">
                            <span>亮度 0%</span><i><b></b></i>
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
                        <svg :class="item.tone" viewBox="0 0 66 22" aria-hidden="true">
                            <polyline :points="item.points" />
                        </svg>
                    </article>
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
    grid-template-columns: 138px minmax(0, 1fr);
    align-self: stretch;
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    border-radius: 18px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.quick-control.is-loading {
    opacity: 0.72;
}

.room-sidebar {
    border-right: 1px solid var(--color-border-subtle);
    padding: 14px 10px;
    background: var(--color-sidebar-bg);
}

.room-sidebar h1 {
    margin: 0 8px 10px;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.room-sidebar nav {
    display: grid;
    gap: 4px;
}

.room-sidebar button {
    position: relative;
    min-height: 31px;
    border-radius: 7px;
    padding: 0 12px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
    text-align: left;
    transition: 160ms var(--motion-ease);
}

.room-sidebar button:hover {
    background: var(--color-surface-hover);
}

.room-sidebar button.active {
    background: linear-gradient(90deg, var(--color-primary-50), var(--color-primary-100));
    color: var(--color-primary-700);
}

.room-sidebar button.active::before {
    position: absolute;
    top: 4px;
    bottom: 4px;
    left: 0;
    width: 3px;
    border-radius: 999px;
    background: var(--color-primary-600);
    content: "";
}

.control-content {
    min-width: 0;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 12px 14px 14px;
    background: var(--color-page-bg);
}

.category-bar {
    display: grid;
    grid-template-columns: 1.25fr repeat(6, minmax(0, 1fr));
    gap: 9px;
    padding-bottom: 9px;
}

.category-bar button {
    display: inline-flex;
    min-width: 0;
    height: 36px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    font-size: 10px;
    font-weight: 800;
    box-shadow: var(--shadow-card);
    transition: 160ms var(--motion-ease);
}

.category-bar button svg {
    color: var(--color-primary-600);
}

.category-bar button:first-child svg {
    order: 2;
    color: var(--color-text-tertiary);
}

.category-bar button:hover,
.category-bar button.active {
    border-color: var(--color-primary-200);
    color: var(--color-primary-700);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-1px);
}

.control-section h2 {
    margin: 1px 5px 7px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 900;
}

.device-grid,
.environment-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 8px;
}

.device-card,
.environment-grid article {
    min-width: 0;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.device-card {
    min-height: 88px;
    padding: 10px;
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
}

.device-card header {
    display: grid;
    grid-template-columns: 30px minmax(0, 1fr) auto;
    align-items: center;
    gap: 7px;
}

.device-icon {
    display: grid;
    width: 30px;
    height: 30px;
    place-items: center;
    border-radius: 7px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.device-card header div {
    display: grid;
    min-width: 0;
    gap: 2px;
}

.device-card strong,
.device-card small {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-card strong {
    color: var(--color-text-primary);
    font-size: 10px;
    font-weight: 900;
}

.device-card small {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-weight: 700;
}

.switch {
    width: 29px;
    height: 16px;
    border-radius: 999px;
    background: var(--color-text-muted);
    padding: 2px;
    transition: 160ms var(--motion-ease);
}

.switch span {
    display: block;
    width: 12px;
    height: 12px;
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

.range-row,
.temperature-row,
.purifier-row {
    display: flex;
    min-height: 27px;
    align-items: flex-end;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-size: 8px;
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
    font-size: 14px;
}

.temperature-row button {
    display: grid;
    width: 22px;
    height: 20px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    font-size: 13px;
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
    margin-top: 9px;
}

.environment-grid article {
    position: relative;
    min-height: 58px;
    overflow: hidden;
    padding: 9px 11px;
}

.environment-grid small,
.environment-grid strong {
    position: relative;
    z-index: 1;
    display: block;
}

.environment-grid small {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-weight: 750;
}

.environment-grid strong {
    margin-top: 4px;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 900;
}

.environment-grid svg {
    position: absolute;
    right: 9px;
    bottom: 8px;
    width: 52px;
    height: 18px;
    fill: none;
    stroke: var(--color-primary-500);
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 2;
}

.environment-grid svg.green {
    stroke: var(--color-success);
}
.environment-grid svg.orange {
    stroke: var(--color-warning);
}
.environment-grid svg.purple {
    stroke: #8b5cf6;
}

.empty-state {
    display: grid;
    min-height: 400px;
    place-items: center;
    background: var(--color-page-bg);
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 800;
}

@media (max-width: 1280px) {
    .category-bar {
        display: flex;
        gap: 10px;
        overflow-x: auto;
    }
    .category-bar button {
        min-width: 96px;
    }
    .category-bar button:first-child {
        min-width: 120px;
    }
    .device-grid,
    .environment-grid {
        grid-template-columns: repeat(3, minmax(160px, 1fr));
    }
}

@media (max-width: 1450px) {
    .quick-control {
        grid-template-columns: 128px minmax(0, 1fr);
    }
    .room-sidebar {
        padding-right: 10px;
        padding-left: 10px;
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
        border-right: 0;
        border-bottom: 1px solid var(--color-border-subtle);
        padding: 16px;
    }
    .room-sidebar h1 {
        margin-bottom: 10px;
    }
    .room-sidebar nav {
        display: flex;
        overflow-x: auto;
    }
    .room-sidebar button {
        min-width: 90px;
        text-align: center;
    }
    .room-sidebar button.active::before {
        top: auto;
        right: 8px;
        bottom: 0;
        left: 8px;
        width: auto;
        height: 3px;
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
}
</style>
