<script setup lang="ts">
import { reactive, ref, watch } from "vue";
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
    if (!form.name.trim()) return;
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
        width="980px"
        :confirm-text="confirmText"
        @update:model-value="close"
        @confirm="submitForm"
    >
        <div class="form-grid">
            <div class="form-column">
                <section>
                    <h3><SvgIcon name="info" />1. 基本信息</h3>
                    <label
                        >自动化名称 <b>*</b
                        ><input
                            v-model="form.name"
                            maxlength="30"
                            placeholder="例如：回家自动开灯"
                        /><small>{{ form.name.length }}/30</small></label
                    ><label
                        >描述（可选）<textarea
                            v-model="form.description"
                            maxlength="100"
                            placeholder="补充说明该自动化的用途与效果"
                        ></textarea
                        ><small>{{ form.description.length }}/100</small></label
                    >
                </section>
                <section>
                    <h3><SvgIcon name="sensor" />2. 触发条件</h3>
                    <label
                        >触发类型 <b>*</b
                        ><select v-model="form.trigger">
                            <option>设备状态变化</option>
                            <option>位置触发</option>
                            <option>时间触发</option>
                            <option>手动触发</option>
                        </select></label
                    >
                    <div class="inline">
                        <select v-model="form.triggerDevice">
                            <option>门磁传感器</option>
                            <option>人体传感器</option>
                            <option>温度传感器</option></select
                        ><select>
                            <option>状态变为</option></select
                        ><select v-model="form.triggerState">
                            <option>打开</option>
                            <option>关闭</option>
                        </select>
                    </div>
                    <button class="outline" type="button">＋ 添加条件</button
                    ><label
                        >生效时间段<select>
                            <option>全天有效</option>
                            <option>自定义时间</option>
                        </select></label
                    >
                </section>
                <section>
                    <h3><SvgIcon name="location" />3. 关联范围</h3>
                    <p class="label">关联房间</p>
                    <div class="chips">
                        <button
                            v-for="room in [
                                '玄关',
                                '客厅',
                                '餐厅',
                                '主卧',
                                '次卧',
                            ]"
                            :key="room"
                            :class="{ active: form.rooms.includes(room) }"
                            type="button"
                            @click="toggleValue(form.rooms, room)"
                        >
                            {{ room }}</button
                        ><button type="button">＋ 选择房间</button>
                    </div>
                    <p class="label">关联设备（可选）</p>
                    <div class="chips">
                        <button
                            v-for="device in ['玄关灯', '客厅灯带', '空调']"
                            :key="device"
                            class="active"
                            type="button"
                        >
                            {{ device }}⌄</button
                        ><button type="button">＋ 选择设备</button>
                    </div>
                </section>
            </div>
            <div class="form-column">
                <section>
                    <h3><SvgIcon name="automation" />4. 执行动作</h3>
                    <div
                        v-for="(device, index) in form.devices"
                        :key="device"
                        class="action-row"
                    >
                        <i>{{ index + 1 }}</i
                        ><SvgIcon
                            :name="index === 2 ? 'air-conditioner' : 'light'"
                        /><span
                            ><b>{{ device }}</b
                            ><small>{{
                                index === 2
                                    ? "开启｜制冷｜温度：26°C"
                                    : "开灯｜亮度 80%｜色温 4000K"
                            }}</small></span
                        ><button
                            type="button"
                            @click="form.devices.splice(index, 1)"
                        >
                            ×
                        </button>
                    </div>
                    <button
                        class="outline"
                        type="button"
                        @click="form.devices.push('智能设备')"
                    >
                        ＋ 添加动作</button
                    ><label
                        >执行延迟（可选）
                        <div class="suffix">
                            <input
                                v-model.number="form.delay"
                                type="number"
                                min="0"
                            /><span>秒</span>
                        </div></label
                    >
                </section>
                <section>
                    <h3><SvgIcon name="settings" />5. 高级设置</h3>
                    <label
                        >优先级<select v-model="form.priority">
                            <option>中（默认）</option>
                            <option>高</option>
                            <option>低</option>
                        </select></label
                    ><label
                        >重复触发间隔<select v-model="form.repeat">
                            <option>不限制</option>
                            <option>5 分钟</option>
                            <option>30 分钟</option>
                        </select></label
                    ><label
                        >备注（可选）<textarea
                            v-model="form.note"
                            maxlength="100"
                            placeholder="可填写更多备注信息"
                        ></textarea>
                    </label>
                </section>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 14px;
    color: var(--color-text-primary);
    font-size: 15px;
}
h3 > svg {
    width: 19px;
    height: 19px;
    padding: 3px;
    border-radius: 6px;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}
.form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-card-bg);
}
.form-column + .form-column {
    border-left: 1px solid var(--color-border-subtle);
}
.form-column section {
    padding: 18px;
    border-bottom: 1px solid var(--color-border-subtle);
}
.form-column section:last-child {
    border-bottom: 0;
}
label {
    position: relative;
    display: flex;
    gap: 7px;
    flex-direction: column;
    margin: 12px 0;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
}
label b {
    color: var(--color-danger);
}
input,
select,
textarea {
    width: 100%;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 10px;
    color: var(--color-text-primary);
    outline: 0;
}

select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}
textarea {
    min-height: 58px;
    resize: none;
}
label > small {
    position: absolute;
    right: 9px;
    bottom: 8px;
    color: var(--color-text-muted);
    font-weight: 400;
}
.inline {
    display: grid;
    grid-template-columns: 1.3fr 1fr 1fr;
    gap: 10px;
}
.outline {
    margin-top: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 7px;
    padding: 8px 12px;
    color: var(--color-primary-600);
    background: var(--color-card-bg);
    font-weight: 700;
}
.label {
    margin: 10px 0 7px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
}
.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
}
.chips button {
    border: 1px solid var(--color-border-default);
    border-radius: 7px;
    padding: 7px 10px;
    color: var(--color-text-secondary);
    background: var(--color-card-bg);
}
.chips button.active {
    border-color: var(--color-primary-600);
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}
.action-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 9px;
}
.action-row > i {
    display: grid;
    width: 21px;
    height: 21px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 50%;
    font-size: 11px;
    font-style: normal;
}
.action-row > svg {
    color: var(--color-primary-600);
}
.action-row > span {
    display: flex;
    flex: 1;
    flex-direction: column;
}
.action-row small {
    color: var(--color-text-tertiary);
}
.suffix {
    display: flex;
}
.suffix input {
    border-radius: 8px 0 0 8px;
}
.suffix span {
    display: grid;
    width: 48px;
    place-items: center;
    border: 1px solid var(--color-border-default);
    border-left: 0;
    border-radius: 0 8px 8px 0;
}
@media (max-width: 760px) {
    .form-grid {
        grid-template-columns: 1fr;
    }
    .form-column + .form-column {
        border-left: 0;
    }
}
</style>
