<script setup lang="ts">
import { ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { toggleValue } from "../../../utils/array";
import type { AutomationRule } from "./AutomationFormDialog.vue";

defineProps<{
    modelValue: boolean;
    rules: AutomationRule[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    scheduled: [
        payload: { weekdays: number[]; time: string; ruleIds: number[] },
    ];
}>();

const weekdays = ref([1, 2, 3, 4, 5]);
const scheduleTime = ref("07:30");
const scheduleRuleIds = ref<number[]>([2, 3]);

const close = () => emit("update:modelValue", false);

const confirm = () => {
    emit("scheduled", {
        weekdays: weekdays.value,
        time: scheduleTime.value,
        ruleIds: scheduleRuleIds.value,
    });
    close();
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        icon="calendar"
        title="定时设置"
        description="设置自动化的执行时间和重复规则"
        width="620px"
        confirm-text="保存设置"
        @update:model-value="close"
        @confirm="confirm"
    >
        <div class="schedule">
            <section>
                <h3><SvgIcon name="refresh" />1. 重复设置</h3>
                <div class="weekdays">
                    <button
                        v-for="(day, index) in [
                            '一',
                            '二',
                            '三',
                            '四',
                            '五',
                            '六',
                            '日',
                        ]"
                        :key="day"
                        :class="{ active: weekdays.includes(index + 1) }"
                        type="button"
                        @click="toggleValue(weekdays, index + 1)"
                    >
                        {{ day }}
                    </button>
                </div>
                <p>已选择 {{ weekdays.length }} 天，将在每周对应日期执行</p>
            </section>
            <section>
                <h3><SvgIcon name="clock" />2. 时间设置</h3>
                <label
                    >执行时间<input v-model="scheduleTime" type="time"
                /></label>
            </section>
            <section>
                <h3><SvgIcon name="calendar" />3. 日期类型</h3>
                <div class="date-types">
                    <button class="active" type="button">
                        工作日<small>周一至周五</small></button
                    ><button type="button">每天<small>包括周末</small></button>
                </div>
            </section>
            <section>
                <h3><SvgIcon name="layers" />4. 执行频率</h3>
                <div class="two-cols">
                    <select>
                        <option>每天执行</option></select
                    ><select>
                        <option>1 次</option>
                    </select>
                </div>
            </section>
            <section>
                <h3><SvgIcon name="automation" />5. 关联规则</h3>
                <label
                    v-for="rule in rules.slice(1, 3)"
                    :key="rule.id"
                    class="scheduled-rule"
                    ><input
                        v-model="scheduleRuleIds"
                        :value="rule.id"
                        type="checkbox"
                    /><SvgIcon :name="rule.icon" /><span
                        ><b>{{ rule.name }}</b
                        ><small>07:30 · 每天 · 工作日</small></span
                    ><em>已关联</em></label
                >
            </section>
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
.schedule {
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-card-bg);
}
.schedule section {
    padding: 18px;
    border-bottom: 1px solid var(--color-border-subtle);
}
.schedule section:last-child {
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
input,
select {
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
.weekdays {
    display: flex;
    gap: 12px;
}
.weekdays button {
    width: 42px;
    height: 35px;
    border: 1px solid var(--color-border-default);
    border-radius: 20px;
    background: var(--color-card-bg);
}
.weekdays button.active {
    border-color: var(--color-primary-600);
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}
.schedule p {
    margin-top: 8px;
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.date-types {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.date-types button {
    display: flex;
    gap: 4px;
    flex-direction: column;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    padding: 12px;
    text-align: left;
    background: var(--color-card-bg);
}
.date-types button.active {
    border-color: var(--color-primary-600);
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}
.date-types small {
    color: var(--color-text-tertiary);
}
.two-cols {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}
.scheduled-rule {
    display: grid;
    grid-template-columns: auto auto 1fr auto;
    align-items: center;
    padding: 9px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
}
.scheduled-rule input {
    width: auto;
}
.scheduled-rule span {
    display: flex;
    flex-direction: column;
}
.scheduled-rule em {
    color: var(--color-success);
    font-style: normal;
}
@media (max-width: 760px) {
    .two-cols {
        grid-template-columns: 1fr;
    }
}
</style>
