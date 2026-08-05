<script setup lang="ts">
import { ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";

defineProps<{
    modelValue: boolean;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const expandedLog = ref<number | null>(null);

const logs = [
    {
        id: 1,
        time: "2026-08-08 10:15:23",
        name: "回家联动",
        source: "位置触发",
        result: "成功",
        duration: "2.4s",
    },
    {
        id: 2,
        time: "2026-08-08 07:00:11",
        name: "晨间唤醒联动",
        source: "定时触发",
        result: "成功",
        duration: "3.1s",
    },
    {
        id: 3,
        time: "2026-08-07 23:00:05",
        name: "夜间回家照明",
        source: "手动触发",
        result: "成功",
        duration: "1.8s",
    },
    {
        id: 4,
        time: "2026-08-07 19:42:12",
        name: "离家安防联动",
        source: "位置触发",
        result: "失败",
        duration: "0.9s",
    },
];

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        icon="log"
        title="执行日志"
        description="查看自动化规则的执行记录与结果，便于排查与优化"
        width="880px"
        confirm-text="关闭"
        @update:model-value="close"
        @confirm="close"
    >
        <!-- 筛选栏 -->
        <div class="log-filters">
            <div class="filter-item">
                <SvgIcon name="calendar" size="sm" />
                <input type="date" value="2026-08-08" />
            </div>
            <div class="filter-item">
                <SvgIcon name="list" size="sm" />
                <select>
                    <option>全部规则</option>
                    <option>回家联动</option>
                    <option>晨间唤醒</option>
                </select>
            </div>
            <div class="filter-item">
                <SvgIcon name="check-circle" size="sm" />
                <select>
                    <option>全部结果</option>
                    <option>成功</option>
                    <option>失败</option>
                </select>
            </div>
            <button class="search-btn" type="button">
                <SvgIcon name="search" size="sm" />搜索
            </button>
        </div>

        <!-- 日志表格 -->
        <div class="log-table">
            <div class="log-table-header">
                <span class="col-time">执行时间</span>
                <span class="col-name">规则名称</span>
                <span class="col-source">触发来源</span>
                <span class="col-result">执行结果</span>
                <span class="col-duration">耗时</span>
                <span class="col-expand"></span>
            </div>

            <div v-for="log in logs" :key="log.id" class="log-row-wrapper">
                <button
                    class="log-row"
                    :class="{ 'is-expanded': expandedLog === log.id }"
                    type="button"
                    @click="expandedLog = expandedLog === log.id ? null : log.id"
                >
                    <span class="col-time">{{ log.time }}</span>
                    <span class="col-name"><b>{{ log.name }}</b></span>
                    <span class="col-source">
                        <span class="source-badge">{{ log.source }}</span>
                    </span>
                    <span class="col-result">
                        <span class="result-badge" :class="log.result === '失败' ? 'is-fail' : 'is-success'">
                            <SvgIcon :name="log.result === '失败' ? 'close' : 'check-circle'" size="sm" />
                            {{ log.result }}
                        </span>
                    </span>
                    <span class="col-duration">{{ log.duration }}</span>
                    <span class="col-expand">
                        <span class="expand-icon" :class="{ 'is-open': expandedLog === log.id }">
                            <SvgIcon name="chevron-down" size="sm" />
                        </span>
                    </span>
                </button>

                <!-- 展开详情 -->
                <Transition name="detail-expand">
                    <div v-if="expandedLog === log.id" class="log-detail">
                        <div class="detail-section">
                            <div class="detail-section-title">
                                <span class="detail-dot is-trigger"></span>
                                触发详情
                            </div>
                            <div class="detail-card">
                                <SvgIcon name="location" size="sm" />
                                <span>设备"小明的手机"到达"家"半径 100m</span>
                            </div>
                            <div class="detail-section-title" style="margin-top: 10px;">
                                <span class="detail-dot is-condition"></span>
                                条件检查
                            </div>
                            <div class="condition-list">
                                <span class="condition-item is-pass">
                                    <SvgIcon name="check-circle" size="sm" />时间条件
                                </span>
                                <span class="condition-item is-pass">
                                    <SvgIcon name="check-circle" size="sm" />设备在线
                                </span>
                                <span class="condition-item is-pass">
                                    <SvgIcon name="check-circle" size="sm" />位置条件
                                </span>
                            </div>
                        </div>
                        <div class="detail-section">
                            <div class="detail-section-title">
                                <span class="detail-dot is-action"></span>
                                执行动作（共 4 个）
                            </div>
                            <div class="action-list-detail">
                                <div class="action-item-detail">
                                    <span class="action-step">1</span>
                                    <SvgIcon name="light" size="sm" />
                                    <span>玄关灯开启</span>
                                    <span class="action-status is-done">✓</span>
                                </div>
                                <div class="action-item-detail">
                                    <span class="action-step">2</span>
                                    <SvgIcon name="light" size="sm" />
                                    <span>客厅灯带开启</span>
                                    <span class="action-status is-done">✓</span>
                                </div>
                                <div class="action-item-detail">
                                    <span class="action-step">3</span>
                                    <SvgIcon name="air-conditioner" size="sm" />
                                    <span>空调 26°C</span>
                                    <span class="action-status is-done">✓</span>
                                </div>
                                <div class="action-item-detail">
                                    <span class="action-step">4</span>
                                    <SvgIcon name="curtain" size="sm" />
                                    <span>客厅窗帘打开</span>
                                    <span class="action-status is-done">✓</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </Transition>
            </div>

            <div v-if="!logs.length" class="log-empty">
                <SvgIcon name="log" />
                <span>暂无执行日志</span>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
/* ── 筛选栏 ── */
.log-filters {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr auto;
    gap: 10px;
    margin-bottom: 16px;
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 12px;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    background: var(--color-card-bg);
    transition: border-color 180ms, box-shadow 180ms;
}

.filter-item:focus-within {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.filter-item > svg {
    flex-shrink: 0;
    color: var(--color-text-muted);
}

.filter-item input,
.filter-item select {
    width: 100%;
    border: none;
    background: transparent;
    padding: 9px 0;
    color: var(--color-text-primary);
    font-size: 13px;
    outline: none;
}

.filter-item select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0 center;
    padding-right: 18px;
    cursor: pointer;
}

.filter-item select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.search-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 0 20px;
    border: none;
    border-radius: 9px;
    background: var(--color-primary-600);
    color: #fff;
    font-size: 13px;
    font-weight: 800;
    cursor: pointer;
    transition: background-color 180ms, transform 150ms;
}

.search-btn:hover {
    background: var(--color-primary-700);
    transform: translateY(-1px);
}

/* ── 日志表格 ── */
.log-table {
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-card-bg);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.log-table-header {
    display: grid;
    grid-template-columns: 1.35fr 1.3fr 1fr 0.9fr 0.5fr 0.3fr;
    align-items: center;
    gap: 8px;
    padding: 11px 14px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
    border-bottom: 1px solid var(--color-border-subtle);
}

.log-row-wrapper {
    border-bottom: 1px solid var(--color-border-subtle);
    transition: background-color 150ms;
}

.log-row-wrapper:last-child {
    border-bottom: 0;
}

.log-row-wrapper:hover {
    background: var(--color-surface-subtle);
}

.log-row {
    display: grid;
    grid-template-columns: 1.35fr 1.3fr 1fr 0.9fr 0.5fr 0.3fr;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 12px 14px;
    border: none;
    background: transparent;
    text-align: left;
    font-size: 13px;
    cursor: pointer;
    transition: background-color 150ms;
}

.log-row.is-expanded {
    background: var(--color-primary-50);
}

.log-row b {
    color: var(--color-text-primary);
    font-weight: 800;
}

/* ── 来源徽章 ── */
.source-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 5px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    font-size: 11px;
    font-weight: 700;
}

/* ── 结果徽章 ── */
.result-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 800;
}

.result-badge.is-success {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.result-badge.is-fail {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.result-badge > svg {
    width: 14px;
    height: 14px;
}

/* ── 展开图标 ── */
.expand-icon {
    display: inline-flex;
    color: var(--color-text-muted);
    transition: transform 250ms ease;
}

.expand-icon.is-open {
    transform: rotate(180deg);
}

/* ── 展开详情过渡 ── */
.detail-expand-enter-active {
    transition: opacity 250ms ease, transform 250ms ease;
}

.detail-expand-leave-active {
    transition: opacity 200ms ease, transform 200ms ease;
}

.detail-expand-enter-from,
.detail-expand-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}

/* ── 展开详情 ── */
.log-detail {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin: 0 10px 12px;
    padding: 16px;
    border: 1px solid var(--color-primary-200);
    border-radius: 11px;
    background: linear-gradient(135deg, var(--color-primary-50), color-mix(in srgb, var(--color-primary-50) 60%, var(--color-card-bg)));
}

.detail-section-title {
    display: flex;
    align-items: center;
    gap: 7px;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 8px;
}

.detail-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.detail-dot.is-trigger {
    background: var(--color-primary-500);
}

.detail-dot.is-condition {
    background: var(--color-warning);
}

.detail-dot.is-action {
    background: var(--color-success);
}

/* ── 详情卡片 ── */
.detail-card {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 9px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 600;
}

.detail-card > svg {
    flex-shrink: 0;
    color: var(--color-primary-600);
}

/* ── 条件列表 ── */
.condition-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.condition-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 10px;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 700;
}

.condition-item.is-pass {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.condition-item > svg {
    width: 14px;
    height: 14px;
}

/* ── 动作列表 ── */
.action-list-detail {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.action-item-detail {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-card-bg);
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-secondary);
    transition: border-color 150ms;
}

.action-item-detail:hover {
    border-color: var(--color-primary-200);
}

.action-step {
    display: grid;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 50%;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 10px;
    font-weight: 800;
}

.action-item-detail > svg {
    flex-shrink: 0;
    color: var(--color-primary-600);
}

.action-item-detail > span {
    flex: 1;
}

.action-status {
    flex-shrink: 0;
    font-size: 14px;
    font-weight: 900;
}

.action-status.is-done {
    color: var(--color-success);
}

/* ── 空状态 ── */
.log-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 48px 16px;
    color: var(--color-text-muted);
    font-size: 13px;
    font-weight: 600;
}

.log-empty > svg {
    width: 40px;
    height: 40px;
    opacity: 0.3;
}

/* ── 响应式 ── */
@media (max-width: 760px) {
    .log-filters {
        grid-template-columns: 1fr;
    }
    .log-detail {
        grid-template-columns: 1fr;
    }
    .log-table-header,
    .log-row {
        grid-template-columns: 1fr 0.8fr 0.6fr 0.4fr;
    }
    .col-source,
    .col-duration {
        display: none;
    }
}
</style>