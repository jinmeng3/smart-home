<script setup lang="ts">
import { ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import type { AutomationRule } from "./AutomationFormDialog.vue";

defineProps<{
    modelValue: boolean;
    rules: AutomationRule[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    imported: [count: number];
}>();

const imported = ref(false);
const preserveIds = ref(true);
const smartMerge = ref(false);
const conflictMode = ref("跳过冲突规则");

const close = () => emit("update:modelValue", false);

const confirm = () => {
    if (!imported.value) return;
    emit("imported", 4);
    close();
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        icon="upload"
        title="导入规则"
        description="从文件中导入自动化规则，快速复用或分享你的智能场景配置"
        width="760px"
        confirm-text="开始导入"
        @update:model-value="close"
        @confirm="confirm"
    >
        <button class="upload" type="button" @click="imported = true">
            <SvgIcon name="upload" size="lg" /><b>{{
                imported ? "automation-rules.yaml" : "点击上传或拖拽文件到此处"
            }}</b
            ><span>支持 JSON、YAML、模板包格式，单个文件最大 10MB</span>
        </button>
        <div class="format-row">
            支持的文件格式： <b>JSON</b><b>YAML</b><b>模板包</b
            ><a>查看示例模板 ›</a>
        </div>
        <div class="two-cols">
            <label
                >导入范围<select>
                    <option>仅导入到当前家庭</option>
                    <option>导入到全部家庭</option>
                </select></label
            ><label
                >冲突处理方式<select v-model="conflictMode">
                    <option>跳过冲突规则</option>
                    <option>覆盖现有规则</option>
                    <option>创建副本</option>
                </select></label
            >
        </div>
        <div class="check-row">
            <label
                ><input v-model="preserveIds" type="checkbox" />
                保留导入规则的原始 ID</label
            ><label
                ><input v-model="smartMerge" type="checkbox" />
                智能合并相似规则</label
            >
        </div>
        <h3>检测到的规则（共 4 条）</h3>
        <div class="import-list">
            <div v-for="rule in rules.slice(0, 4)" :key="rule.id">
                <SvgIcon :name="rule.icon" /><span
                    ><b>{{ rule.name }}</b
                    ><small>{{ rule.description }}</small></span
                ><em>待导入</em>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
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
.two-cols {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}
.upload {
    display: flex;
    width: 100%;
    height: 165px;
    align-items: center;
    justify-content: center;
    gap: 7px;
    flex-direction: column;
    border: 1px dashed var(--color-primary-200);
    border-radius: 10px;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}
.upload span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.format-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 13px 0;
    border-bottom: 1px solid var(--color-border-subtle);
    font-size: 12px;
}
.format-row b {
    border-radius: 5px;
    padding: 4px 10px;
    color: var(--color-primary-600);
    background: var(--color-primary-50);
}
.format-row a {
    margin-left: auto;
    color: var(--color-primary-600);
}
.check-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    margin: 14px 0;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 12px;
}
.check-row label {
    display: block;
    margin: 0;
}
.check-row input {
    width: auto;
}
h3 {
    margin: 0 0 10px;
    color: var(--color-text-primary);
    font-size: 14px;
}
.import-list {
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
}
.import-list > div {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 13px;
    border-bottom: 1px solid var(--color-border-subtle);
}
.import-list span {
    display: flex;
    flex: 1;
    flex-direction: column;
}
.import-list small {
    color: var(--color-text-tertiary);
}
.import-list em {
    border-radius: 6px;
    padding: 4px 9px;
    color: var(--color-success);
    background: var(--color-success-soft);
    font-style: normal;
}
@media (max-width: 760px) {
    .two-cols {
        grid-template-columns: 1fr;
    }
}
</style>
