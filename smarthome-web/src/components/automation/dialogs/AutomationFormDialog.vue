<script setup lang="ts">
import { reactive, ref, computed, watch } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { toggleValue } from "../../../utils/array";

export interface AutomationRule {
    id: number;
    name: string;
    description: string;
    trigger: string;
    devices: number;
    icon: string;
    tone: string;
    enabled: boolean;
}

const props = defineProps<{
    modelValue: boolean;
    rule?: AutomationRule;
    mode: "create" | "edit";
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    save: [
        payload: {
            mode: "create" | "edit";
            name: string;
            description: string;
            trigger: string;
        },
    ];
}>();

const form = reactive({
    name: "",
    description: "",
    trigger: "设备状态变化",
    triggerDevice: "门磁传感器",
    triggerState: "打开",
    rooms: ["玄关", "客厅", "餐厅"] as string[],
    devices: ["玄关灯", "客厅灯带", "空调"] as string[],
    delay: 0,
    priority: "中（默认）",
    repeat: "不限制",
    note: "",
});

const dialogTitle = props.mode === "edit" ? "编辑规则" : "创建自动化";
const icon = props.mode === "edit" ? "edit" : "automation";
const confirmText = props.mode === "edit" ? "保存修改" : "创建";

const triggerOptions = [
    { value: "设备状态变化", icon: "device-management", desc: "传感器检测到变化时触发" },
    { value: "位置触发", icon: "location", desc: "到达或离开指定位置时触发" },
    { value: "时间触发", icon: "clock", desc: "在设定的时间点自动触发" },
    { value: "手动触发", icon: "automation", desc: "通过语音或手动方式触发" },
];

const roomOptions = ["玄关", "客厅", "餐厅", "主卧", "次卧", "书房", "厨房", "阳台", "卫生间"];

const nameError = ref(false);

const triggerIconMap: Record<string, string> = {
    "设备状态变化": "device-management",
    "位置触发": "location",
    "时间触发": "clock",
    "手动触发": "automation",
};

const flowSummary = computed(() => {
    const trigger = form.trigger;
    const rooms = form.rooms.length ? form.rooms.join("、") : "未选择";
    const actionCount = form.devices.length;
    const hasDelay = form.delay > 0;
    return { trigger, rooms, actionCount, hasDelay };
});

watch(
    () => [props.modelValue, props.rule, props.mode] as const,
    () => {
        if (props.mode === "edit" && props.rule) {
            form.name = props.rule.name;
            form.description = props.rule.description;
            form.trigger = props.rule.trigger;
        } else if (props.mode === "create") {
            form.name = "";
            form.description = "";
            form.trigger = "设备状态变化";
        }
    },
    { immediate: true },
);

const close = () => emit("update:modelValue", false);

const submitForm = () => {
    if (!form.name.trim()) {
        nameError.value = true;
        return;
    }
    nameError.value = false;
    emit("save", {
        mode: props.mode,
        name: form.name.trim(),
        description:
            form.description.trim() ||
            `${form.trigger} · ${form.triggerDevice}${form.triggerState}`,
        trigger: form.trigger,
    });
    close();
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="dialogTitle"
        :icon="icon"
        description="设置触发条件和执行动作，让设备在合适的时机自动响应"
        width="960px"
        :confirm-text="confirmText"
        @update:model-value="close"
        @confirm="submitForm"
    >
        <div class="form-grid">
            <!-- 左列 -->
            <div class="form-column">
                <!-- 1. 基本信息 -->
                <section class="form-section">
                    <div class="section-header">
                        <span class="section-step is-blue">1</span>
                        <SvgIcon name="info" />
                        <h3>基本信息</h3>
                    </div>
                    <div class="section-body">
                        <div class="field">
                            <label>自动化名称 <span class="required">*</span></label>
                            <div class="input-wrap" :class="{ 'is-error': nameError }">
                                <input
                                    v-model="form.name"
                                    maxlength="30"
                                    placeholder="例如：回家自动开灯"
                                    @input="nameError = false"
                                />
                                <span class="char-count">{{ form.name.length }}/30</span>
                                <span v-if="nameError" class="error-msg">请输入自动化名称</span>
                            </div>
                        </div>
                        <div class="field">
                            <label>描述（可选）</label>
                            <div class="input-wrap">
                                <textarea
                                    v-model="form.description"
                                    maxlength="100"
                                    placeholder="补充说明该自动化的用途与效果"
                                ></textarea>
                                <span class="char-count">{{ form.description.length }}/100</span>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- 2. 触发条件 -->
                <section class="form-section">
                    <div class="section-header">
                        <span class="section-step is-green">2</span>
                        <SvgIcon name="sensor" />
                        <h3>触发条件</h3>
                    </div>
                    <div class="section-body">
                        <div class="field">
                            <label>触发类型 <span class="required">*</span></label>
                            <div class="trigger-grid">
                                <button
                                    v-for="opt in triggerOptions"
                                    :key="opt.value"
                                    type="button"
                                    class="trigger-card"
                                    :class="{ active: form.trigger === opt.value }"
                                    @click="form.trigger = opt.value"
                                >
                                    <SvgIcon :name="opt.icon" />
                                    <div class="trigger-card-text">
                                        <strong>{{ opt.value }}</strong>
                                        <small>{{ opt.desc }}</small>
                                    </div>
                                </button>
                            </div>
                        </div>
                        <Transition name="slide-fade" mode="out-in">
                            <div v-if="form.trigger === '设备状态变化'" key="device" class="trigger-detail">
                                <div class="inline-field">
                                    <div class="select-wrap">
                                        <select v-model="form.triggerDevice">
                                            <option>门磁传感器</option>
                                            <option>人体传感器</option>
                                            <option>温度传感器</option>
                                            <option>光照传感器</option>
                                        </select>
                                    </div>
                                    <div class="select-wrap">
                                        <select>
                                            <option>状态变为</option>
                                        </select>
                                    </div>
                                    <div class="select-wrap">
                                        <select v-model="form.triggerState">
                                            <option>打开</option>
                                            <option>关闭</option>
                                            <option>高于阈值</option>
                                            <option>低于阈值</option>
                                        </select>
                                    </div>
                                </div>
                                <button class="add-btn" type="button">
                                    <SvgIcon name="plus" />添加条件
                                </button>
                            </div>
                            <div v-else-if="form.trigger === '位置触发'" key="location" class="trigger-detail">
                                <div class="inline-field two-col">
                                    <div class="select-wrap">
                                        <select>
                                            <option>到达指定位置</option>
                                            <option>离开指定位置</option>
                                        </select>
                                    </div>
                                    <div class="select-wrap">
                                        <select>
                                            <option>家</option>
                                            <option>公司</option>
                                            <option>学校</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div v-else-if="form.trigger === '时间触发'" key="time" class="trigger-detail">
                                <div class="inline-field two-col">
                                    <div class="select-wrap">
                                        <select>
                                            <option>每天</option>
                                            <option>工作日</option>
                                            <option>周末</option>
                                            <option>自定义</option>
                                        </select>
                                    </div>
                                    <div class="select-wrap">
                                        <input type="time" value="07:00" />
                                    </div>
                                </div>
                            </div>
                        </Transition>
                        <div class="field">
                            <label>生效时间段</label>
                            <div class="select-wrap">
                                <select>
                                    <option>全天有效</option>
                                    <option>自定义时间</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- 3. 关联范围 -->
                <section class="form-section">
                    <div class="section-header">
                        <span class="section-step is-orange">3</span>
                        <SvgIcon name="location" />
                        <h3>关联范围</h3>
                    </div>
                    <div class="section-body">
                        <div class="field">
                            <label>关联房间</label>
                            <div class="chip-group">
                                <button
                                    v-for="room in roomOptions"
                                    :key="room"
                                    type="button"
                                    class="chip"
                                    :class="{ active: form.rooms.includes(room) }"
                                    @click="toggleValue(form.rooms, room)"
                                >
                                    <SvgIcon
                                        :name="form.rooms.includes(room) ? 'check-circle' : 'room'"
                                        size="sm"
                                    />
                                    {{ room }}
                                </button>
                            </div>
                        </div>
                        <div class="field">
                            <label>关联设备（可选）</label>
                            <div class="chip-group">
                                <button
                                    v-for="device in ['玄关灯', '客厅灯带', '空调', '窗帘']"
                                    :key="device"
                                    type="button"
                                    class="chip active"
                                >
                                    {{ device }}
                                </button>
                                <button class="chip chip-add" type="button">
                                    <SvgIcon name="plus" size="sm" />添加设备
                                </button>
                            </div>
                        </div>
                    </div>
                </section>
            </div>

            <!-- 右列 -->
            <div class="form-column">
                <!-- 4. 执行动作 -->
                <section class="form-section">
                    <div class="section-header">
                        <span class="section-step is-purple">4</span>
                        <SvgIcon name="automation" />
                        <h3>执行动作</h3>
                    </div>
                    <div class="section-body">
                        <div class="action-list">
                            <div
                                v-for="(device, index) in form.devices"
                                :key="device"
                                class="action-card"
                                :style="{ '--action-delay': `${index * 50}ms` }"
                            >
                                <span class="action-index">{{ index + 1 }}</span>
                                <span class="action-icon" :class="index === 2 ? 'is-cool' : 'is-warm'">
                                    <SvgIcon :name="index === 2 ? 'air-conditioner' : 'light'" />
                                </span>
                                <div class="action-info">
                                    <strong>{{ device }}</strong>
                                    <span>{{
                                        index === 2
                                            ? "开启 · 制冷 · 26°C"
                                            : "开灯 · 亮度 80% · 色温 4000K"
                                    }}</span>
                                </div>
                                <button
                                    class="action-remove"
                                    type="button"
                                    title="移除"
                                    @click="form.devices.splice(index, 1)"
                                >
                                    <SvgIcon name="close" size="sm" />
                                </button>
                            </div>
                            <div v-if="!form.devices.length" class="action-empty">
                                <SvgIcon name="automation" />
                                <span>暂无执行动作，点击下方按钮添加</span>
                            </div>
                        </div>
                        <button class="add-btn" type="button" @click="form.devices.push('智能设备')">
                            <SvgIcon name="plus" />添加动作
                        </button>
                        <div class="field">
                            <label>执行延迟（可选）</label>
                            <div class="suffix-input">
                                <input
                                    v-model.number="form.delay"
                                    type="number"
                                    min="0"
                                    placeholder="0"
                                />
                                <span class="suffix-label">秒</span>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- 5. 高级设置 -->
                <section class="form-section">
                    <div class="section-header">
                        <span class="section-step is-teal">5</span>
                        <SvgIcon name="settings" />
                        <h3>高级设置</h3>
                    </div>
                    <div class="section-body">
                        <div class="field">
                            <label>优先级</label>
                            <div class="select-wrap">
                                <select v-model="form.priority">
                                    <option>高</option>
                                    <option>中（默认）</option>
                                    <option>低</option>
                                </select>
                            </div>
                        </div>
                        <div class="field">
                            <label>重复触发间隔</label>
                            <div class="select-wrap">
                                <select v-model="form.repeat">
                                    <option>不限制</option>
                                    <option>5 分钟</option>
                                    <option>30 分钟</option>
                                    <option>1 小时</option>
                                </select>
                            </div>
                        </div>
                        <div class="field">
                            <label>备注（可选）</label>
                            <div class="input-wrap">
                                <textarea
                                    v-model="form.note"
                                    maxlength="100"
                                    placeholder="可填写更多备注信息"
                                ></textarea>
                                <span class="char-count">{{ form.note.length }}/100</span>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>

        <!-- 底部流程预览 -->
        <div class="flow-preview">
            <div class="flow-preview-label">流程预览</div>
            <div class="flow-preview-bar">
                <div class="flow-node">
                    <span class="flow-node-icon is-trigger">
                        <SvgIcon :name="triggerIconMap[flowSummary.trigger] || 'sensor'" size="sm" />
                    </span>
                    <span class="flow-node-text">{{ flowSummary.trigger }}</span>
                </div>
                <span class="flow-arrow">
                    <SvgIcon name="chevron-right" size="sm" />
                </span>
                <div class="flow-node">
                    <span class="flow-node-icon is-room">
                        <SvgIcon name="location" size="sm" />
                    </span>
                    <span class="flow-node-text">{{ flowSummary.rooms }}</span>
                </div>
                <span class="flow-arrow">
                    <SvgIcon name="chevron-right" size="sm" />
                </span>
                <div class="flow-node">
                    <span class="flow-node-icon is-action">
                        <SvgIcon name="automation" size="sm" />
                    </span>
                    <span class="flow-node-text">{{ flowSummary.actionCount }} 个动作{{ flowSummary.hasDelay ? ` · 延迟 ${form.delay}秒` : '' }}</span>
                </div>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
/* ── 布局 ── */
.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
    border-radius: 14px;
    background: var(--color-card-bg);
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.form-column + .form-column {
    border-left: 1px solid var(--color-border-subtle);
}

/* ── 节卡片 ── */
.form-section {
    position: relative;
    padding: 0;
    border-bottom: 1px solid var(--color-border-subtle);
    transition: background-color 200ms;
}

.form-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 0;
    border-radius: 0 0 3px 3px;
    background: var(--color-primary-500);
    transition: height 250ms ease;
}

.form-section:hover::before {
    height: 100%;
    border-radius: 0 3px 3px 0;
}

.form-section:last-child {
    border-bottom: 0;
}

.form-section:hover {
    background: var(--color-surface-subtle);
}

/* ── 节标题 ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 16px 20px 0;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
    user-select: none;
}

.section-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 800;
    color: var(--color-text-primary);
}

.section-header > svg {
    width: 18px;
    height: 18px;
    padding: 3px;
    border-radius: 6px;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}

.section-step {
    display: grid;
    width: 22px;
    height: 22px;
    place-items: center;
    border-radius: 7px;
    color: #fff;
    font-size: 11px;
    font-weight: 900;
    line-height: 1;
    transition: transform 200ms ease;
}

.form-section:hover .section-step {
    transform: scale(1.08);
}

.section-step.is-blue { background: linear-gradient(135deg, #3b82f6, #2563eb); }
.section-step.is-green { background: linear-gradient(135deg, #22c55e, #16a34a); }
.section-step.is-orange { background: linear-gradient(135deg, #f59e0b, #d97706); }
.section-step.is-purple { background: linear-gradient(135deg, #a855f7, #9333ea); }
.section-step.is-teal { background: linear-gradient(135deg, #14b8a6, #0d9488); }

/* ── 节内容 ── */
.section-body {
    padding: 14px 20px 18px;
}

.field {
    margin-bottom: 12px;
}

.field:last-child {
    margin-bottom: 0;
}

.field > label {
    display: block;
    margin-bottom: 6px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
}

.required {
    color: var(--color-danger);
}

/* ── 输入框 ── */
.input-wrap {
    position: relative;
}

.input-wrap input,
.input-wrap textarea,
.select-wrap select,
.suffix-input input {
    width: 100%;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 10px 12px;
    color: var(--color-text-primary);
    font-size: 14px;
    outline: none;
    transition: border-color 180ms, box-shadow 180ms;
}

.input-wrap input:focus,
.input-wrap textarea:focus,
.select-wrap select:focus,
.suffix-input input:focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.input-wrap.is-error input {
    border-color: var(--color-danger);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-danger) 15%, transparent);
}

.error-msg {
    position: absolute;
    left: 0;
    bottom: -20px;
    color: var(--color-danger);
    font-size: 12px;
    font-weight: 600;
    animation: error-shake 300ms ease;
}

@keyframes error-shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-4px); }
    75% { transform: translateX(4px); }
}

.select-wrap select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    padding-right: 32px;
    cursor: pointer;
}

.select-wrap select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

.input-wrap textarea {
    min-height: 56px;
    resize: none;
}

.char-count {
    position: absolute;
    right: 10px;
    bottom: 9px;
    color: var(--color-text-muted);
    font-size: 11px;
    font-weight: 400;
    pointer-events: none;
}

/* ── 触发类型选择 ── */
.trigger-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}

.trigger-card {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 10px 12px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 200ms;
    text-align: left;
}

.trigger-card:hover {
    border-color: var(--color-primary-300);
    background: var(--color-primary-50);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.trigger-card.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.trigger-card > svg {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
    margin-top: 1px;
}

.trigger-card-text strong {
    display: block;
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-primary);
    margin-bottom: 2px;
}

.trigger-card.active .trigger-card-text strong {
    color: var(--color-primary-700);
}

.trigger-card-text small {
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-text-muted);
    line-height: 1.3;
}

.trigger-card.active .trigger-card-text small {
    color: var(--color-primary-500);
}

/* ── 触发详情过渡 ── */
.trigger-detail {
    margin-bottom: 12px;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
    transition: opacity 200ms ease, transform 200ms ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
    opacity: 0;
    transform: translateY(-6px);
}

/* ── 内联选择 ── */
.inline-field {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    margin-bottom: 8px;
}

.inline-field.two-col {
    grid-template-columns: 1fr 1fr;
}

/* ── 添加按钮 ── */
.add-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: 1px dashed var(--color-primary-300);
    border-radius: 8px;
    background: transparent;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: all 200ms;
}

.add-btn:hover {
    border-style: solid;
    background: var(--color-primary-50);
    border-color: var(--color-primary-400);
    transform: translateY(-1px);
}

.add-btn > svg {
    width: 14px;
    height: 14px;
    transition: transform 200ms;
}

.add-btn:hover > svg {
    transform: rotate(90deg);
}

/* ── Chip 标签 ── */
.chip-group {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 7px 12px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: all 150ms;
}

.chip:hover {
    border-color: var(--color-primary-300);
    transform: translateY(-1px);
}

.chip.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.chip > svg {
    width: 14px;
    height: 14px;
}

.chip-add {
    border-style: dashed;
    border-color: var(--color-border-strong);
    color: var(--color-text-tertiary);
}

.chip-add:hover {
    border-style: solid;
    border-color: var(--color-primary-300);
    color: var(--color-primary-600);
}

/* ── 动作卡片 ── */
.action-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 12px;
}

.action-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-card-bg);
    animation: action-card-in 300ms ease both;
    animation-delay: var(--action-delay, 0ms);
    transition: border-color 180ms, box-shadow 180ms, transform 180ms;
}

.action-card:hover {
    border-color: var(--color-primary-200);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    transform: translateX(2px);
}

@keyframes action-card-in {
    from {
        opacity: 0;
        transform: translateX(-8px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.action-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 24px 16px;
    border: 1px dashed var(--color-border-strong);
    border-radius: 10px;
    color: var(--color-text-muted);
    font-size: 13px;
    font-weight: 600;
}

.action-empty > svg {
    width: 28px;
    height: 28px;
    opacity: 0.4;
}

.action-index {
    display: grid;
    width: 22px;
    height: 22px;
    flex-shrink: 0;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 50%;
    font-size: 11px;
    font-weight: 800;
    font-style: normal;
    color: var(--color-text-tertiary);
    background: var(--color-surface-subtle);
}

.action-icon {
    display: grid;
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 8px;
    font-style: normal;
}

.action-icon.is-warm {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.action-icon.is-cool {
    background: var(--color-info-soft);
    color: var(--color-info);
}

.action-info {
    flex: 1;
    min-width: 0;
}

.action-info strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.action-info span {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
    margin-top: 2px;
}

.action-remove {
    display: grid;
    width: 26px;
    height: 26px;
    flex-shrink: 0;
    place-items: center;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--color-text-muted);
    cursor: pointer;
    transition: all 150ms;
}

.action-remove:hover {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

/* ── 后缀输入 ── */
.suffix-input {
    display: flex;
}

.suffix-input input {
    border-radius: 8px 0 0 8px;
}

.suffix-label {
    display: grid;
    width: 44px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-left: 0;
    border-radius: 0 8px 8px 0;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 700;
}

/* ── 底部流程预览 ── */
.flow-preview {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 16px;
    padding: 14px 18px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-surface-subtle);
}

.flow-preview-label {
    flex-shrink: 0;
    color: var(--color-text-muted);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.flow-preview-bar {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    min-width: 0;
    overflow-x: auto;
    padding: 2px 0;
}

.flow-preview-bar::-webkit-scrollbar {
    height: 2px;
}

.flow-preview-bar::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border);
}

.flow-node {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
    padding: 6px 12px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-secondary);
    white-space: nowrap;
}

.flow-node-icon {
    display: grid;
    width: 22px;
    height: 22px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 6px;
}

.flow-node-icon.is-trigger {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.flow-node-icon.is-room {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.flow-node-icon.is-action {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.flow-node-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 120px;
}

.flow-arrow {
    flex-shrink: 0;
    color: var(--color-text-muted);
    opacity: 0.5;
}

/* ── 响应式 ── */
@media (max-width: 760px) {
    .form-grid {
        grid-template-columns: 1fr;
    }
    .form-column + .form-column {
        border-left: 0;
        border-top: 1px solid var(--color-border-subtle);
    }
    .trigger-grid {
        grid-template-columns: 1fr;
    }
    .inline-field {
        grid-template-columns: 1fr;
    }
    .inline-field.two-col {
        grid-template-columns: 1fr;
    }
    .flow-preview {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }
}
</style>