<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import BaseSwitch from "../../BaseSwitch.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { useModalConfirm } from "../../../composables/useModalConfirm";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const autoSync = ref(true);

const schedules = reactive([
    {
        time: "07:00",
        name: "起床模式",
        detail: "窗帘打开 · 卧室灯亮 · 空调制热 24°C",
        color: "#ff9418",
    },
    {
        time: "19:00",
        name: "回家模式",
        detail: "玄关灯亮 · 空调制冷 26°C · 新风开启",
        color: "#3478f6",
    },
    {
        time: "22:00",
        name: "离家模式",
        detail: "关闭灯光 · 安防布防 · 监控夜视",
        color: "#20b86a",
    },
    {
        time: "23:00",
        name: "睡眠模式",
        detail: "灯光渐暗 · 窗帘关闭 · 安防设防",
        color: "#825bea",
    },
]);

const { loading, confirm } = useModalConfirm(() => {
    ElMessage.success("编辑家庭日程操作成功");
    emit("update:modelValue", false);
});
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="编辑家庭日程"
        description="管理家庭日程与自动化计划"
        :width="720"
        :loading="loading"
        confirm-text="保存计划"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="schedule-dialog">
            <!-- 顶部日期导航 -->
            <div class="date-nav">
                <button class="date-arrow" type="button" aria-label="上一个日期">
                    <SvgIcon name="chevron-left" size="sm" />
                </button>
                <div class="date-info">
                    <strong>2025年5月20日 星期二</strong>
                    <span class="today-badge"><i></i>今天</span>
                </div>
                <button class="date-arrow" type="button" aria-label="下一个日期">
                    <SvgIcon name="chevron-right" size="sm" />
                </button>
            </div>

            <div class="dialog-grid">
                <!-- 左栏：计划时间线 -->
                <section class="timeline-panel">
                    <header class="panel-head">
                        <h3>
                            <span class="tone-chip is-orange">
                                <SvgIcon name="calendar" size="sm" />
                            </span>
                            计划时间线
                        </h3>
                        <span class="count-badge">{{ schedules.length }} 个计划</span>
                    </header>

                    <div class="timeline">
                        <article
                            v-for="item in schedules"
                            :key="item.time"
                            class="timeline-row"
                            :style="{ '--row-color': item.color }"
                        >
                            <time class="time-pill">{{ item.time }}</time>
                            <span class="tl-node" aria-hidden="true"></span>
                            <div class="plan-body">
                                <b>{{ item.name }}</b>
                                <small>{{ item.detail }}</small>
                            </div>
                            <div class="row-actions">
                                <button class="icon-btn" type="button" title="编辑">
                                    <SvgIcon name="edit" size="sm" />
                                </button>
                                <button class="icon-btn" type="button" title="刷新">
                                    <SvgIcon name="refresh" size="sm" />
                                </button>
                            </div>
                        </article>
                    </div>
                </section>

                <!-- 右栏：运行设置 -->
                <aside class="settings-panel">
                    <header class="panel-head">
                        <h3>
                            <span class="tone-chip is-indigo">
                                <SvgIcon name="settings" size="sm" />
                            </span>
                            运行设置
                        </h3>
                    </header>

                    <section class="setting-block">
                        <div class="setting-head">
                            <span class="tone-chip is-purple icon-s">
                                <SvgIcon name="refresh" size="sm" />
                            </span>
                            <div class="setting-txt">
                                <b>重复设置</b>
                                <small>选择重复执行的星期</small>
                            </div>
                        </div>
                        <div class="chips">
                            <button
                                v-for="(day, i) in [
                                    '一',
                                    '二',
                                    '三',
                                    '四',
                                    '五',
                                    '六',
                                    '日',
                                ]"
                                :key="i"
                                type="button"
                                :class="{
                                    active: i < 5,
                                    'is-weekend': i >= 5,
                                }"
                            >
                                {{ day }}
                            </button>
                        </div>
                    </section>

                    <section class="setting-block">
                        <div class="setting-head">
                            <span class="tone-chip is-teal icon-s">
                                <SvgIcon name="power" size="sm" />
                            </span>
                            <div class="setting-txt">
                                <b>自动执行</b>
                                <small>到点自动运行该计划</small>
                            </div>
                            <BaseSwitch v-model="autoSync" small />
                        </div>
                    </section>

                    <section class="setting-block">
                        <div class="setting-head">
                            <span class="tone-chip is-orange icon-s">
                                <SvgIcon name="room" size="sm" />
                            </span>
                            <div class="setting-txt">
                                <b>关联房间 / 设备</b>
                                <small>选择计划生效范围</small>
                            </div>
                        </div>
                        <div class="chips icon-chips">
                            <button
                                v-for="item in [
                                    { label: '客厅', icon: 'room' },
                                    { label: '玄关', icon: 'room' },
                                    { label: '主卧', icon: 'room' },
                                    { label: '空调', icon: 'air-conditioner' },
                                    { label: '灯光', icon: 'light' },
                                    { label: '窗帘', icon: 'curtain' },
                                ]"
                                :key="item.label"
                                type="button"
                                class="active"
                            >
                                <SvgIcon :name="item.icon" size="sm" />
                                {{ item.label }}
                            </button>
                        </div>
                    </section>
                </aside>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.schedule-dialog {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

/* ---------- 顶部日期导航 ---------- */
.date-nav {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: linear-gradient(
        to right,
        var(--tone-primary-soft),
        var(--color-card-bg) 45%
    );
    padding: 9px 12px;
}
.date-arrow {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
}
.date-arrow:hover {
    border-color: var(--tone-primary);
    color: var(--tone-primary);
    background: var(--tone-primary-soft);
}
.date-info {
    display: flex;
    align-items: center;
    gap: 8px;
}
.date-info strong {
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-primary);
}
.today-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    background: var(--tone-success-soft);
    padding: 2px 9px;
    color: var(--tone-success);
    font-size: 11px;
    font-weight: 700;
}
.today-badge i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--tone-success);
}

/* ---------- 双栏布局 ---------- */
.dialog-grid {
    display: grid;
    grid-template-columns: 1.25fr 1fr;
    gap: 12px;
    align-items: start;
}
.panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}
.panel-head h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 13px;
    color: var(--color-text-primary);
}
.panel-head h3 .tone-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 8px;
    font-size: 13px;
}
.count-badge {
    border-radius: 999px;
    background: var(--tone-primary-soft);
    padding: 2px 9px;
    color: var(--tone-primary);
    font-size: 11px;
    font-weight: 800;
}

/* ---------- 左栏：计划时间线 ---------- */
.timeline-panel {
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-panel-background);
    padding: 14px;
}
.timeline {
    position: relative;
    display: grid;
}
.timeline::before {
    content: "";
    position: absolute;
    top: 6px;
    bottom: 6px;
    left: calc(64px + 14px + 5px);
    width: 2px;
    border-radius: 2px;
    background: var(--color-border-subtle);
}
.timeline-row {
    display: grid;
    grid-template-columns: 64px 24px minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    padding: 10px 0;
    border-radius: 10px;
    transition: background 0.2s ease;
}
.timeline-row:hover {
    background: var(--color-surface-hover);
}
.timeline-row + .timeline-row {
    border-top: 1px dashed var(--color-border-subtle);
}
.time-pill {
    justify-self: end;
    min-width: 56px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--row-color) 12%, transparent);
    padding: 4px 9px;
    color: var(--row-color);
    font-size: 12px;
    font-weight: 900;
    text-align: center;
}
.tl-node {
    position: relative;
    z-index: 1;
    justify-self: center;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: var(--row-color);
    box-shadow:
        0 0 0 3px var(--color-card-bg),
        0 0 0 6px color-mix(in srgb, var(--row-color) 18%, transparent);
}
.plan-body {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
}
.plan-body b {
    font-size: 13px;
    color: var(--color-text-primary);
}
.plan-body small {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-tertiary);
    font-size: 11px;
}
.row-actions {
    display: flex;
    gap: 6px;
}
.icon-btn {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
}
.icon-btn:hover {
    border-color: var(--tone-primary);
    color: var(--tone-primary);
    background: var(--tone-primary-soft);
}

/* ---------- 右栏：运行设置 ---------- */
.settings-panel {
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-panel-background);
    padding: 14px;
}
.setting-block {
    padding: 12px 0;
}
.setting-block + .setting-block {
    border-top: 1px dashed var(--color-border-subtle);
}
.setting-head {
    display: flex;
    align-items: center;
    gap: 8px;
}
.setting-head .icon-s {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    flex: none;
    border-radius: 8px;
    font-size: 13px;
}
.setting-txt {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
    flex: 1;
}
.setting-txt b {
    font-size: 13px;
    color: var(--color-text-primary);
}
.setting-txt small {
    color: var(--color-text-tertiary);
    font-size: 11px;
}
.setting-head .chips {
    margin: 0;
}
.chips .is-weekend {
    color: var(--tone-warning);
}
.chips .is-weekend.active {
    border-color: var(--tone-warning);
    background: var(--tone-warning-soft);
    color: var(--tone-warning);
}
.icon-chips button {
    display: inline-flex;
    align-items: center;
    gap: 5px;
}

/* ---------- 响应式 ---------- */
@media (max-width: 760px) {
    .dialog-grid {
        grid-template-columns: 1fr;
    }
    .timeline-row {
        grid-template-columns: 56px 20px minmax(0, 1fr) auto;
    }
    .timeline::before {
        left: calc(56px + 8px + 5px);
    }
}
</style>
