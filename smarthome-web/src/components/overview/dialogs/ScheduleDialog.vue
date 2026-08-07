<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import BaseSwitch from "../../BaseSwitch.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import {
    getSchedule,
    saveSchedule,
    type HouseholdSchedule,
    type ScheduleItem,
} from "../../../api/overview";
import { useLatestRequest } from "../../../composables/useLatestRequest";

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    saved: [value: HouseholdSchedule];
}>();

const today = new Date();
const selectedDate = ref(new Date(today.getFullYear(), today.getMonth(), today.getDate()));
const loading = ref(false);
const { loading: loadingSchedule, run } = useLatestRequest();
const enabled = ref(true);
const repeatDays = ref([1, 2, 3, 4, 5]);
const version = ref<number>();
const selectedTargets = ref(["客厅", "玄关", "主卧"]);
const editingIndex = ref<number | null>(null);
const editorOpen = ref(false);
const editor = reactive({ time: "07:00", name: "", detail: "", color: "#3478f6", enabled: true });

const schedules = ref<ScheduleItem[]>([]);
const dateKey = computed(() => {
    const year = selectedDate.value.getFullYear();
    const month = String(selectedDate.value.getMonth() + 1).padStart(2, "0");
    const day = String(selectedDate.value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
});
const dateLabel = computed(() => new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "long", day: "numeric", weekday: "long" }).format(selectedDate.value));
const isToday = computed(() => dateKey.value === [today.getFullYear(), String(today.getMonth() + 1).padStart(2, "0"), String(today.getDate()).padStart(2, "0")].join("-"));

const load = async () => {
    await run(
        () => getSchedule(dateKey.value),
        (result) => {
            enabled.value = result?.enabled ?? true;
            repeatDays.value = result?.repeatDays ?? [1, 2, 3, 4, 5];
            version.value = result?.version;
            schedules.value = (result?.items?.length ? result.items : []).sort(
                (a, b) => a.time.localeCompare(b.time),
            );
        },
        (error) => {
            ElMessage.error(
                error instanceof Error ? error.message : "日程加载失败",
            );
        },
    );
};

const changeDate = (offset: number) => {
    selectedDate.value = new Date(selectedDate.value.getFullYear(), selectedDate.value.getMonth(), selectedDate.value.getDate() + offset);
};
const toggleDay = (day: number) => repeatDays.value = repeatDays.value.includes(day) ? repeatDays.value.filter((item) => item !== day) : [...repeatDays.value, day].sort();
const toggleTarget = (target: string) => selectedTargets.value = selectedTargets.value.includes(target) ? selectedTargets.value.filter((item) => item !== target) : [...selectedTargets.value, target];
const openEditor = (index?: number) => {
    editingIndex.value = index ?? null;
    const item = index === undefined ? { time: "07:00", name: "", detail: "", color: "#3478f6", enabled: true } : schedules.value[index];
    Object.assign(editor, item);
    editorOpen.value = true;
};
const saveEditor = () => {
    if (!editor.name.trim() || !editor.time) return ElMessage.warning("请填写计划名称和时间");
    const item = { ...editor, name: editor.name.trim(), detail: editor.detail.trim(), position: editingIndex.value ?? schedules.value.length };
    if (editingIndex.value === null) schedules.value.push(item);
    else schedules.value.splice(editingIndex.value, 1, item);
    schedules.value.sort((a, b) => a.time.localeCompare(b.time));
    editorOpen.value = false;
};
const removeSchedule = (index: number) => schedules.value.splice(index, 1);

const confirm = async () => {
    if (!repeatDays.value.length) return ElMessage.warning("请至少选择一个重复日期");
    loading.value = true;
    try {
        const result = await saveSchedule(dateKey.value, { enabled: enabled.value, repeatDays: repeatDays.value, targets: {}, items: schedules.value.map((item, position) => ({ ...item, position })), ...(version.value ? { version: version.value } : {}) });
        version.value = result.version;
        emit("saved", result);
        ElMessage.success("家庭日程已保存并同步到后端");
        emit("update:modelValue", false);
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "日程保存失败");
    } finally { loading.value = false; }
};

watch([() => props.modelValue, dateKey], ([visible]) => { if (visible) void load(); }, { immediate: true });
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="编辑家庭日程"
        description="管理家庭日程与自动化计划"
        :width="860"
        :loading="loading"
        confirm-text="保存计划"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="schedule-dialog">
            <!-- 顶部日期导航 -->
            <div class="date-nav">
                <button class="date-arrow" type="button" aria-label="上一个日期" @click="changeDate(-1)">
                    <SvgIcon name="chevron-left" size="sm" />
                </button>
                <div class="date-info">
                    <strong>{{ dateLabel }}</strong>
                    <span v-if="isToday" class="today-badge"><i></i>今天</span>
                </div>
                <button class="date-arrow" type="button" aria-label="下一个日期" @click="changeDate(1)">
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

                    <button class="add-plan" type="button" @click="openEditor()">
                        <SvgIcon name="plus" size="sm" /> 添加日程计划
                    </button>

                    <div v-loading="loadingSchedule" class="timeline">
                        <article
                            v-for="item in schedules"
                            :key="`${item.time}-${item.name}`"
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
                                <button class="icon-btn" type="button" title="编辑" @click="openEditor(schedules.indexOf(item))">
                                    <SvgIcon name="edit" size="sm" />
                                </button>
                                <button class="icon-btn danger" type="button" title="删除" @click="removeSchedule(schedules.indexOf(item))">
                                    <SvgIcon name="delete" size="sm" />
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
                        <div class="repeat-days">
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
                                    active: repeatDays.includes(i + 1),
                                    'is-weekend': i >= 5,
                                }"
                                @click="toggleDay(i + 1)"
                            >
                                <small>周</small>{{ day }}
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
                            <BaseSwitch v-model="enabled" small />
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
                        <div class="target-grid">
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
                                :class="{ active: selectedTargets.includes(item.label) }"
                                @click="toggleTarget(item.label)"
                            >
                                <SvgIcon :name="item.icon" size="sm" />
                                <span>{{ item.label }}</span>
                                <i aria-hidden="true">✓</i>
                            </button>
                        </div>
                    </section>
                </aside>
            </div>

            <section v-if="editorOpen" class="plan-editor">
                <header><div><b>{{ editingIndex === null ? "添加计划" : "编辑计划" }}</b><small>设置执行时间、场景名称与动作摘要</small></div><button type="button" @click="editorOpen = false"><SvgIcon name="close" size="sm" /></button></header>
                <div class="editor-grid">
                    <label>执行时间<input v-model="editor.time" type="time" /></label>
                    <label>计划名称<input v-model="editor.name" maxlength="30" placeholder="例如：回家模式" /></label>
                    <label class="detail-field">动作摘要<input v-model="editor.detail" maxlength="100" placeholder="例如：玄关灯亮 · 空调制冷 26°C" /></label>
                    <label>标记颜色<input v-model="editor.color" class="color-input" type="color" /></label>
                </div>
                <footer><button type="button" @click="editorOpen = false">取消</button><button class="save-editor" type="button" @click="saveEditor">保存计划</button></footer>
            </section>
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
    padding: 12px 16px;
    box-shadow: 0 8px 18px rgb(37 99 235 / 8%);
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
    font-size: 16px;
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
.add-plan {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-bottom: 8px;
    border: 1px dashed var(--color-primary-300);
    border-radius: 10px;
    padding: 8px;
    color: var(--tone-primary);
    background: var(--tone-primary-soft);
    font-size: 12px;
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
.icon-btn.danger:hover {
    border-color: var(--color-danger);
    color: var(--color-danger);
    background: color-mix(in srgb, var(--color-danger) 9%, transparent);
}

.plan-editor {
    border: 1px solid var(--color-primary-200);
    border-radius: 14px;
    background: linear-gradient(135deg, var(--color-card-bg), var(--tone-primary-soft));
    padding: 14px;
    box-shadow: var(--shadow-card);
}
.plan-editor header,
.plan-editor footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.plan-editor header div {
    display: flex;
    flex-direction: column;
}
.plan-editor header small {
    color: var(--color-text-tertiary);
    font-size: 13px;
}
.plan-editor header button {
    color: var(--color-text-tertiary);
}
.editor-grid {
    display: grid;
    grid-template-columns: 130px 1fr 100px;
    gap: 10px;
    margin: 12px 0;
}
.editor-grid label {
    display: flex;
    flex-direction: column;
    gap: 5px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 700;
}
.editor-grid input {
    width: 100%;
    border: 1px solid var(--color-border-default);
    padding: 0 10px;
}
.editor-grid .detail-field {
    grid-column: 1 / 3;
}
.editor-grid .color-input {
    padding: 5px;
}
.plan-editor footer {
    justify-content: flex-end;
    gap: 8px;
}
.plan-editor footer button {
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 700;
}
.plan-editor footer .save-editor {
    border-color: var(--tone-primary);
    color: white;
    background: var(--tone-primary);
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
    font-size: 15px;
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
    font-size: 13px;
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

/* ---------- Enhanced selection controls ---------- */
.plan-body b,
.setting-txt b {
    font-size: 15px;
}
.plan-body small,
.setting-txt small {
    font-size: 13px;
}
.repeat-days {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 6px;
    margin-top: 12px;
}
.repeat-days button {
    display: flex;
    min-width: 0;
    height: 52px;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    border: 1px solid var(--color-border-default);
    border-radius: 11px;
    color: var(--color-text-secondary);
    background: var(--color-card-bg);
    font-size: 15px;
    font-weight: 900;
    transition: all 160ms var(--motion-ease);
}
.repeat-days button small {
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.repeat-days button:hover {
    border-color: var(--color-primary-300);
    transform: translateY(-1px);
}
.repeat-days button.active {
    border-color: var(--tone-primary);
    color: white;
    background: linear-gradient(145deg, var(--color-primary-500), var(--color-primary-600));
    box-shadow: 0 6px 14px var(--color-focus-ring);
}
.repeat-days button.active small {
    color: rgb(255 255 255 / 75%);
}
.repeat-days button.is-weekend:not(.active) {
    color: var(--tone-warning);
    background: var(--tone-warning-soft);
}
.target-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    margin-top: 12px;
}
.target-grid button {
    display: grid;
    grid-template-columns: 24px minmax(0, 1fr) 18px;
    min-height: 46px;
    align-items: center;
    gap: 7px;
    border: 1px solid var(--color-border-default);
    border-radius: 11px;
    padding: 8px 10px;
    color: var(--color-text-secondary);
    background: var(--color-card-bg);
    text-align: left;
    font-size: 14px;
    font-weight: 800;
}
.target-grid button i {
    display: grid;
    width: 18px;
    height: 18px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 50%;
    color: transparent;
    font-size: 11px;
    font-style: normal;
}
.target-grid button:hover,
.target-grid button.active {
    border-color: var(--color-primary-400);
    color: var(--tone-primary);
    background: var(--tone-primary-soft);
}
.target-grid button.active {
    box-shadow: inset 3px 0 0 var(--tone-primary);
}
.target-grid button.active i {
    border-color: var(--tone-primary);
    color: white;
    background: var(--tone-primary);
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
    .editor-grid {
        grid-template-columns: 1fr;
    }
    .editor-grid .detail-field {
        grid-column: auto;
    }
}
</style>
