<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import { gsap, registerFlip, useMotionMode } from "../../motion";
import { motionEase } from "../../motion/tokens";
import { useSkeletonTransition } from "../../composables/useSkeletonTransition";
import { formatDeviceTimestamp } from "../../utils/device";
import type { Device, DeviceType } from "../../types/device";
import DeviceRow from "./DeviceRow.vue";
import {
    deviceStatusLabelMap,
    deviceTypeIconMap,
    deviceTypeLabelMap,
    deviceTypeOptions,
    getDeviceTypeIcon,
    getDeviceTypeLabel,
    getStatusClasses,
} from "./deviceMeta";

const props = defineProps<{
    devices: Device[];
    total: number;
    page: number;
    pageSize: number;
    selectedId: number | null;
    loading: boolean;
    syncing: boolean;
    sort: "updated" | "name" | "status";
    activeType: DeviceType | "";
    batchMode?: boolean;
    selectedDeviceIds?: number[];
}>();

defineEmits<{
    "update:page": [value: number];
    "update:pageSize": [value: number];
    "update:sort": [value: "updated" | "name" | "status"];
    "update:activeType": [value: DeviceType | ""];
    select: [device: Device];
    "batch-select": [device: Device];
    edit: [device: Device];
    remove: [device: Device];
    add: [];
    batch: [];
    sync: [];
    "clear-filters": [];
}>();

/* === 骨架 → 真实内容短交叉淡入 === */
const skeletonHostRef = ref<HTMLElement | null>(null);
const { play: playSkeletonTransition } = useSkeletonTransition(
    skeletonHostRef,
    computed(() => props.loading),
);

const pageSizeOptions = [10, 20, 50];
const viewMode = ref<"list" | "grid">("list");

/* === 列表/网格切换 Flip：保持设备项位置连续 === */
const { isReduced } = useMotionMode();
let flipReady = false;
void registerFlip().then(() => {
    flipReady = true;
});

/** 切换视图：先捕获旧布局，切换后再 Flip 到新布局 */
const switchView = async (next: "list" | "grid") => {
    if (next === viewMode.value) return;
    if (!flipReady || isReduced.value) {
        viewMode.value = next;
        return;
    }

    // 捕获当前可见的设备项布局
    const state = (gsap as any)?.Flip?.getState?.(
        ".device-table-wrap [data-flip-id], .device-grid-wrap [data-flip-id]",
    );

    viewMode.value = next;
    await nextTick();

    // 新视图渲染完成后，从旧位置过渡到新位置
    if (state) {
        (gsap as any).Flip?.from?.(state, {
            targets: ".device-table-wrap [data-flip-id], .device-grid-wrap [data-flip-id]",
            duration: 0.28,
            ease: motionEase.ease,
            absolute: true,
        });
    }
};
</script>

<template>
    <section class="device-list-panel">
        <header class="device-list-header">
            <h2>设备列表</h2>
            <div class="device-list-tools">
                <button
                    class="device-list-action"
                    :class="{ 'is-active': batchMode }"
                    type="button"
                    @click="$emit('batch')"
                >
                    <SvgIcon name="delete" /> 批量删除
                </button>
                <button
                    class="device-list-action device-list-sync"
                    :disabled="syncing"
                    type="button"
                    @click="$emit('sync')"
                >
                    <SvgIcon :class="{ 'is-spinning': syncing }" name="refresh" />
                    {{ syncing ? "同步中" : "同步设备" }}
                </button>
                <select
                    :value="sort"
                    @change="
                        $emit(
                            'update:sort',
                            ($event.target as HTMLSelectElement).value as
                                'updated' | 'name' | 'status',
                        )
                    "
                >
                    <option value="updated">按最后在线</option>
                    <option value="name">按名称</option>
                    <option value="status">按状态</option>
                </select>
                <button
                    :class="{ 'is-active': viewMode === 'list' }"
                    type="button"
                    title="列表视图"
                    @click="switchView('list')"
                >
                    <SvgIcon name="list" />
                </button>
                <button
                    :class="{ 'is-active': viewMode === 'grid' }"
                    type="button"
                    title="网格视图"
                    @click="switchView('grid')"
                >
                    <SvgIcon name="grid" />
                </button>
            </div>
        </header>

        <!-- 列表/网格切换由 GSAP Flip 接管（保持设备项位置连续），不再使用 CSS out-in -->
        <div ref="skeletonHostRef" class="device-view-host">
            <div v-if="viewMode === 'list'" key="list" class="device-table-wrap" :class="{ 'is-loading': loading && devices.length }">
                <div v-if="loading && devices.length" class="device-refresh-overlay">
                    <div class="device-refresh-spinner" aria-hidden="true"></div>
                    <span>正在刷新</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th></th>
                            <th>设备名称</th>
                            <th>房间</th>
                            <th>类型</th>
                            <th>品牌</th>
                            <th>状态</th>
                            <th>最后在线</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <TransitionGroup
                        v-if="devices.length"
                        tag="tbody"
                        name="device-row"
                    >
                        <DeviceRow
                            v-for="device in devices"
                            :key="device.id"
                            :device="device"
                            :selected="selectedId === device.id"
                            :batch-mode="batchMode"
                            :batch-selected="selectedDeviceIds?.includes(device.id)"
                            @edit="$emit('edit', $event)"
                            @remove="$emit('remove', $event)"
                            @select="$emit('select', $event)"
                            @batch-select="$emit('batch-select', $event)"
                        />
                    </TransitionGroup>
                    <tbody v-else class="skeleton-body">
                        <tr v-for="i in 6" :key="i" class="skeleton-row">
                            <td><div class="skeleton-box" style="width:16px;height:16px;border-radius:4px"></div></td>
                            <td><div class="skeleton-box" style="width:60%;height:14px"></div></td>
                            <td><div class="skeleton-box" style="width:50%;height:14px"></div></td>
                            <td><div class="skeleton-box" style="width:40%;height:14px"></div></td>
                            <td><div class="skeleton-box" style="width:45%;height:14px"></div></td>
                            <td><div class="skeleton-box" style="width:35%;height:14px"></div></td>
                            <td><div class="skeleton-box" style="width:50%;height:14px"></div></td>
                            <td><div class="skeleton-box" style="width:30%;height:14px"></div></td>
                        </tr>
                    </tbody>
                </table>
                <div v-if="!loading && !devices.length" class="device-empty">
                    <SvgIcon name="device-management" />
                    <span>暂无匹配设备</span>
                    <small class="device-empty-desc">调整筛选条件或添加新设备</small>
                    <div class="device-empty-actions">
                        <button
                            class="device-empty-action"
                            type="button"
                            @click="$emit('clear-filters')"
                        >
                            清除筛选
                        </button>
                        <button
                            class="device-empty-action is-primary"
                            type="button"
                            @click="$emit('add')"
                        >
                            添加设备
                        </button>
                    </div>
                </div>
            </div>

            <div v-else key="grid" class="device-grid-wrap" :class="{ 'is-loading': loading && devices.length }">
                <div v-if="loading && devices.length" class="device-refresh-overlay">
                    <div class="device-refresh-spinner" aria-hidden="true"></div>
                    <span>正在刷新</span>
                </div>
                <div v-if="!loading && !devices.length" class="device-empty">
                    <SvgIcon name="device-management" />
                    <span>暂无匹配设备</span>
                    <small class="device-empty-desc">调整筛选条件或添加新设备</small>
                    <div class="device-empty-actions">
                        <button
                            class="device-empty-action"
                            type="button"
                            @click="$emit('clear-filters')"
                        >
                            清除筛选
                        </button>
                        <button
                            class="device-empty-action is-primary"
                            type="button"
                            @click="$emit('add')"
                        >
                            添加设备
                        </button>
                    </div>
                </div>
                <TransitionGroup
                    v-else
                    tag="div"
                    name="device-card"
                    class="device-grid"
                    :class="{ 'is-loading': loading }"
                >
                    <article
                        v-for="device in devices"
                        :key="device.id"
                        :data-flip-id="`dev-${device.id}`"
                        class="device-grid-card"
                        :class="{ 'is-selected': selectedId === device.id }"
                        @click="$emit('select', device)"
                    >
                        <header>
                            <span
                                class="device-grid-icon"
                                :style="{ '--device-color': device.color || '#6b7280' }"
                                aria-hidden="true"
                            >
                                <SvgIcon :name="getDeviceTypeIcon(device.icon || device.type)" />
                            </span>
                            <span class="device-status-badge" :class="getStatusClasses(device.status)">
                                <i :class="`status-dot is-${device.status}`"></i>
                                {{ deviceStatusLabelMap[device.status] }}
                            </span>
                        </header>
                        <div class="device-grid-main">
                            <strong>{{ device.name }}</strong>
                            <small>{{ device.room }}</small>
                        </div>
                        <dl>
                            <div><dt>类型</dt><dd>{{ getDeviceTypeLabel(device.type) }}</dd></div>
                            <div><dt>品牌</dt><dd>{{ device.brand }}</dd></div>
                            <div><dt>最后在线</dt><dd>{{ formatDeviceTimestamp(device.lastOnline, '从未在线') }}</dd></div>
                        </dl>
                        <footer>
                            <button type="button" @click.stop="$emit('edit', device)">编辑</button>
                            <button type="button" @click.stop="$emit('remove', device)">删除</button>
                        </footer>
                    </article>
                </TransitionGroup>
            </div>
        </div>

        <footer class="device-pagination">
            <span>共 {{ total }} 条</span>
            <div class="device-page-actions">
                <button
                    :disabled="page <= 1"
                    type="button"
                    @click="$emit('update:page', page - 1)"
                >
                    ‹
                </button>
                <strong>{{ page }}</strong>
                <button
                    :disabled="page * pageSize >= total"
                    type="button"
                    @click="$emit('update:page', page + 1)"
                >
                    ›
                </button>
            </div>
            <select
                :value="pageSize"
                @change="
                    $emit(
                        'update:pageSize',
                        Number(($event.target as HTMLSelectElement).value),
                    )
                "
            >
                <option
                    v-for="item in pageSizeOptions"
                    :key="item"
                    :value="item"
                >
                    {{ item }} 条/页
                </option>
            </select>
        </footer>
    </section>
</template>

<style scoped>
.device-list-panel {
    display: flex;
    min-height: 400px;
    flex: 1 1 auto;
    flex-direction: column;
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 0;
    box-shadow: var(--shadow-card);
    animation: device-list-enter 240ms var(--motion-ease) both;
}

.device-list-header,
.device-list-tools,
.device-type-tabs,
.device-pagination,
.device-page-actions {
    display: flex;
    align-items: center;
}

.device-list-header {
    display: flex;
    min-width: 0;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
    padding: 16px 18px 12px;
}

.device-list-header h2 {
    min-width: 0;
}

.device-list-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 900;
}

.device-list-tools,
.device-type-tabs,
.device-page-actions {
    gap: 8px;
}

.device-list-tools {
    min-width: 0;
    width: auto;
    margin-left: auto;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.device-list-tools button {
    flex: 0 0 auto;
}

.device-list-tools .device-list-primary,
.device-list-tools .device-list-action {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 0 10px;
    font-size: 13px;
    white-space: nowrap;
}

.device-list-tools .device-list-primary {
    border-color: var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

@media (max-width: 900px) {
    .device-list-header h2 {
        flex: 1 0 100%;
    }

    .device-list-tools {
        width: 100%;
    }
}

@media (max-width: 560px) {
    .device-list-panel {
        min-height: 460px;
    }

    .device-list-header,
    .device-type-tabs,
    .device-pagination {
        padding-right: 12px;
        padding-left: 12px;
    }

    .device-list-tools {
        justify-content: flex-start;
    }

    .device-pagination {
        flex-wrap: wrap;
    }
}

.device-list-tools select,
.device-pagination select {
    height: 34px;
    height: 38px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    color: var(--color-text-secondary);
    font-weight: 700;
}

.device-pagination select {
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    text-align: center;
    text-align-last: center;
    padding: 0 32px;
    cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 8px center;
    background-size: 14px;
}

.device-pagination select::-ms-expand {
    display: none;
}

.device-list-tools select option,
.device-pagination select option {
    background: var(--color-panel-background);
    color: var(--color-text-primary);
}

.device-list-tools select {
    width: 132px;
    height: 34px;
    padding: 0 28px 0 10px;
    font-size: 12px;
}

.device-list-tools button,
.device-type-tabs button,
.device-page-actions button,
.device-page-actions strong {
    min-width: 34px;
    height: 32px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    color: var(--color-text-secondary);
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease);
}

.device-type-tabs {
    margin: 0;
    padding: 0 18px 14px;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--color-border);
}

.device-type-tabs button {
    min-width: auto;
    padding: 0 12px;
    font-size: 12px;
}

.device-list-tools .is-active,
.device-type-tabs .is-active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
}
.device-list-action.is-active {
    border-color: var(--color-danger);
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.device-table-wrap {
    position: relative;
    min-height: 0;
    flex: 1 1 auto;
    overflow: auto;
    padding: 0 8px;
}

.device-grid-wrap {
    position: relative;
    min-height: 0;
    flex: 1 1 auto;
    overflow: auto;
    padding: 12px;
}

.device-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
}

.device-grid-card {
    display: grid;
    min-width: 0;
    gap: 12px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 14px;
    cursor: pointer;
    transition:
        transform 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease);
}

.device-grid-card:hover,
.device-grid-card.is-selected {
    border-color: var(--color-primary-200);
    background: var(--color-surface-hover);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}

.device-grid-card header,
.device-grid-card footer,
.device-status-badge {
    display: flex;
    align-items: center;
}

.device-grid-card header,
.device-grid-card footer {
    justify-content: space-between;
    gap: 10px;
}

.device-grid-icon {
    display: grid;
    width: 38px;
    height: 38px;
    place-items: center;
    border-radius: 8px;
    background: color-mix(in srgb, var(--device-color, #6b7280) 14%, transparent);
    color: var(--device-color, #6b7280);
    flex-shrink: 0;
    transition: 160ms var(--motion-ease);
}

.device-grid-main {
    display: grid;
    min-width: 0;
    gap: 4px;
}

.device-grid-main strong,
.device-grid-main small,
.device-grid-card dd {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-grid-main strong {
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 900;
}

.device-grid-main small {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.device-grid-card dl {
    display: grid;
    gap: 8px;
    margin: 0;
}

.device-grid-card dl div {
    display: grid;
    min-width: 0;
    grid-template-columns: 68px minmax(0, 1fr);
    gap: 10px;
}

.device-grid-card dt {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

.device-grid-card dd {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
    text-align: right;
}

.device-grid-card footer {
    padding-top: 10px;
    border-top: 1px solid var(--color-border-subtle);
}

.device-grid-card footer button {
    border: 0;
    background: transparent;
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 900;
}

.device-grid-card footer button:hover {
    color: var(--color-primary-800);
}

.device-status-badge {
    gap: 6px;
    border: 1px solid;
    border-radius: 999px;
    padding: 4px 9px;
    font-size: 13px;
    font-weight: 900;
    white-space: nowrap;
}

table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

th {
    padding: 10px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 900;
    text-align: left;
    white-space: nowrap;
    background: var(--color-surface-subtle);
}

th:first-child {
    width: 42px;
}

th:nth-child(2) {
    width: 24%;
}

th:nth-child(7) {
    width: 172px;
}

th:last-child {
    width: 96px;
}

.device-empty {
    display: grid;
    min-height: 220px;
    place-items: center;
    color: var(--color-text-tertiary);
    font-weight: 700;
}

.device-pagination {
    flex: 0 0 auto;
    justify-content: space-between;
    gap: 14px;
    padding: 8px 18px;
    border-top: 1px solid var(--color-border);
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.device-page-actions strong {
    display: grid;
    place-items: center;
    border-color: transparent;
    background: transparent;
    color: var(--color-text-primary);
}

button:not(:disabled):hover {
    transform: translateY(-1px);
}

button:not(:disabled):active {
    transform: scale(0.98);
}

button:disabled {
    cursor: default;
    opacity: 0.45;
}

/* === 骨架屏 === */
.skeleton-body {
    pointer-events: none;
}

.skeleton-row td {
    border-top: none;
    padding: 8px 10px;
}

.skeleton-box {
    background: var(--color-surface-subtle);
    border-radius: 6px;
    animation: skeleton-shimmer 1500ms ease-in-out infinite;
    background: linear-gradient(
        90deg,
        var(--color-surface-subtle) 25%,
        var(--color-surface-hover) 50%,
        var(--color-surface-subtle) 75%
    );
    background-size: 200% 100%;
}

@keyframes skeleton-shimmer {
    from { background-position: 200% 0; }
    to { background-position: -200% 0; }
}

/* === 列表/网格切换由 GSAP Flip 接管（device-view-host 包裹两个视图） === */
.device-view-host {
    min-width: 0;
}

/* === 加载中保留旧数据降透明度 === */
.device-grid.is-loading {
    opacity: 0.55;
    pointer-events: none;
    transition: opacity 180ms var(--motion-ease);
}

/* === 空状态增加图标和操作入口 === */
.device-empty {
    display: grid;
    place-items: center;
    align-content: center;
    gap: 10px;
    min-height: 200px;
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 700;
}

.device-empty svg {
    width: 40px;
    height: 40px;
    color: var(--color-text-muted);
}

.device-empty-action {
    margin-top: 4px;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 800;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
    transition: background-color 160ms var(--motion-ease);
}

.device-empty-action:hover {
    background: var(--color-primary-100);
}

.device-empty-action.is-primary {
    color: #fff;
    background: var(--color-primary-600);
}

.device-empty-action.is-primary:hover {
    background: var(--color-primary-700);
}

.device-empty-desc {
    font-size: 12px;
    color: var(--color-text-muted);
    font-weight: 600;
}

.device-empty-actions {
    display: flex;
    gap: 8px;
    margin-top: 4px;
}

@keyframes device-list-enter {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@media (prefers-reduced-motion: reduce) {
    button:not(:disabled):hover,
    button:not(:disabled):active {
        transform: none;
    }
}

/* === 刷新遮罩 === */

.device-refresh-overlay {
    position: absolute;
    inset: 0;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: color-mix(in srgb, var(--color-card-bg) 72%, transparent);
    backdrop-filter: blur(2px);
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    animation: device-refresh-fade-in 160ms ease;
}

/* 顶部细进度条 */
.device-refresh-overlay::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    overflow: hidden;
    background: color-mix(in srgb, var(--color-primary-500) 25%, transparent);
}

.device-refresh-overlay::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 40%;
    height: 2px;
    border-radius: 999px;
    background: var(--color-primary-500);
    animation: device-loading-slide 900ms var(--motion-ease) infinite;
}

/* 使用 transform 平移，避免持续修改 left 造成布局抖动 */
@keyframes device-loading-slide {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(250%); }
}

.device-refresh-spinner {
    width: 26px;
    height: 26px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 600ms linear infinite;
}

@keyframes device-refresh-fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
    .device-refresh-overlay {
        animation: none;
    }
}

/* === 同步按钮旋转 === */

.device-list-sync svg.is-spinning {
    animation-duration: 800ms;
}

/* === 行/卡片增删过渡 === */

.device-row-enter-active,
.device-row-leave-active {
    transition:
        opacity 200ms ease,
        transform 200ms var(--motion-ease);
}

.device-row-enter-from {
    opacity: 0;
    transform: translateY(6px);
}

.device-row-enter-to {
    opacity: 1;
    transform: translateY(0);
}

.device-row-leave-to {
    opacity: 0;
}

.device-row-leave-active {
    position: relative;
}

.device-row-move {
    transition: transform 220ms var(--motion-ease);
}

.device-card-enter-active,
.device-card-leave-active {
    transition:
        opacity 200ms ease,
        transform 200ms var(--motion-ease);
}

.device-card-enter-from {
    opacity: 0;
    transform: translateY(8px);
}

.device-card-enter-to {
    opacity: 1;
    transform: translateY(0);
}

.device-card-leave-to {
    opacity: 0;
}

.device-card-leave-active {
    position: absolute;
}

.device-card-move {
    transition: transform 220ms var(--motion-ease);
}
</style>
