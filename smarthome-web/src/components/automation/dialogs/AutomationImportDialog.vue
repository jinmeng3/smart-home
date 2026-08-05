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
        <!-- 上传区域 -->
        <div class="upload-zone" :class="{ 'is-uploaded': imported }" @click="imported = true">
            <div class="upload-icon">
                <SvgIcon :name="imported ? 'check-circle' : 'upload'" size="lg" />
            </div>
            <div class="upload-text">
                <strong>{{ imported ? "automation-rules.yaml" : "点击上传或拖拽文件到此处" }}</strong>
                <span>支持 JSON、YAML、模板包格式，单个文件最大 10MB</span>
            </div>
            <span v-if="!imported" class="upload-browse">选择文件</span>
            <span v-else class="upload-status is-done">已上传</span>
        </div>

        <!-- 格式信息 -->
        <div class="format-bar">
            <span class="format-label">支持的文件格式：</span>
            <span class="format-badge is-json">JSON</span>
            <span class="format-badge is-yaml">YAML</span>
            <span class="format-badge is-template">模板包</span>
            <a class="format-link" href="#" @click.prevent>查看示例模板 ›</a>
        </div>

        <!-- 导入选项 -->
        <div class="options-grid">
            <div class="option-field">
                <label>导入范围</label>
                <div class="select-wrap">
                    <select>
                        <option>仅导入到当前家庭</option>
                        <option>导入到全部家庭</option>
                    </select>
                </div>
            </div>
            <div class="option-field">
                <label>冲突处理方式</label>
                <div class="select-wrap">
                    <select v-model="conflictMode">
                        <option>跳过冲突规则</option>
                        <option>覆盖现有规则</option>
                        <option>创建副本</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- 复选框 -->
        <div class="checkbox-group">
            <label class="checkbox-row">
                <input v-model="preserveIds" type="checkbox" />
                <span class="checkbox-mark"><SvgIcon name="check-circle" size="sm" /></span>
                <span class="checkbox-text">保留导入规则的原始 ID</span>
            </label>
            <label class="checkbox-row">
                <input v-model="smartMerge" type="checkbox" />
                <span class="checkbox-mark"><SvgIcon name="check-circle" size="sm" /></span>
                <span class="checkbox-text">智能合并相似规则</span>
            </label>
        </div>

        <!-- 规则列表 -->
        <div class="rule-section">
            <div class="rule-section-title">
                <SvgIcon name="list" size="sm" />
                <span>检测到的规则（共 4 条）</span>
            </div>
            <div class="rule-list">
                <div v-for="(rule, index) in rules.slice(0, 4)" :key="rule.id" class="rule-item" :style="{ '--rule-delay': `${index * 60}ms` }">
                    <span class="rule-icon" :class="`tone-${rule.tone}`">
                        <SvgIcon :name="rule.icon" size="sm" />
                    </span>
                    <div class="rule-info">
                        <strong>{{ rule.name }}</strong>
                        <small>{{ rule.description }}</small>
                    </div>
                    <span class="rule-badge">待导入</span>
                </div>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
/* ── 上传区域 ── */
.upload-zone {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 20px 18px;
    border: 2px dashed var(--color-primary-300);
    border-radius: 14px;
    background: var(--color-primary-50);
    cursor: pointer;
    transition: all 220ms;
}

.upload-zone:hover {
    border-color: var(--color-primary-500);
    background: color-mix(in srgb, var(--color-primary-50) 70%, var(--color-primary-100));
    transform: translateY(-1px);
    box-shadow: 0 4px 14px color-mix(in srgb, var(--color-primary-500) 10%, transparent);
}

.upload-zone.is-uploaded {
    border-style: solid;
    border-color: var(--color-success);
    background: var(--color-success-soft);
}

.upload-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 12px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.upload-zone.is-uploaded .upload-icon {
    color: var(--color-success);
}

.upload-text {
    flex: 1;
    min-width: 0;
}

.upload-text strong {
    display: block;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
    margin-bottom: 3px;
}

.upload-text span {
    display: block;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
}

.upload-browse {
    flex-shrink: 0;
    padding: 8px 16px;
    border: 1px solid var(--color-primary-300);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 800;
    transition: all 150ms;
}

.upload-zone:hover .upload-browse {
    border-color: var(--color-primary-500);
    background: var(--color-primary-600);
    color: #fff;
}

.upload-status {
    flex-shrink: 0;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 800;
}

.upload-status.is-done {
    background: var(--color-success);
    color: #fff;
}

/* ── 格式信息 ── */
.format-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 0;
    border-bottom: 1px solid var(--color-border-subtle);
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-tertiary);
}

.format-label {
    flex-shrink: 0;
}

.format-badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 800;
}

.format-badge.is-json {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.format-badge.is-yaml {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.format-badge.is-template {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.format-link {
    margin-left: auto;
    color: var(--color-primary-600);
    font-weight: 700;
    text-decoration: none;
    font-size: 12px;
    cursor: pointer;
    transition: color 150ms;
}

.format-link:hover {
    color: var(--color-primary-800);
    text-decoration: underline;
}

/* ── 导入选项 ── */
.options-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin: 14px 0;
}

.option-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.option-field label {
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
}

.select-wrap select {
    width: 100%;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 10px 12px;
    padding-right: 32px;
    color: var(--color-text-primary);
    font-size: 14px;
    outline: none;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    cursor: pointer;
    transition: border-color 180ms, box-shadow 180ms;
}

.select-wrap select:focus {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.select-wrap select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}

/* ── 复选框 ── */
.checkbox-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 14px 0;
    padding: 14px 16px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-card-bg);
}

.checkbox-row {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    user-select: none;
}

.checkbox-row input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
}

.checkbox-mark {
    display: grid;
    width: 20px;
    height: 20px;
    flex-shrink: 0;
    place-items: center;
    border: 2px solid var(--color-border-strong);
    border-radius: 5px;
    color: transparent;
    transition: all 180ms;
}

.checkbox-row input:checked + .checkbox-mark {
    border-color: var(--color-primary-600);
    background: var(--color-primary-600);
    color: #fff;
}

.checkbox-text {
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 700;
}

/* ── 规则列表 ── */
.rule-section {
    margin-top: 4px;
}

.rule-section-title {
    display: flex;
    align-items: center;
    gap: 7px;
    margin-bottom: 10px;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.rule-section-title > svg {
    color: var(--color-primary-600);
}

.rule-list {
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-card-bg);
}

.rule-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    border-bottom: 1px solid var(--color-border-subtle);
    animation: rule-item-in 300ms ease both;
    animation-delay: var(--rule-delay, 0ms);
    transition: background-color 150ms;
}

.rule-item:last-child {
    border-bottom: 0;
}

.rule-item:hover {
    background: var(--color-surface-subtle);
}

@keyframes rule-item-in {
    from {
        opacity: 0;
        transform: translateY(-6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.rule-icon {
    display: grid;
    width: 36px;
    height: 36px;
    flex-shrink: 0;
    place-items: center;
    border-radius: 10px;
    font-size: 16px;
}

.rule-icon.tone-blue {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.rule-info {
    flex: 1;
    min-width: 0;
}

.rule-info strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 800;
}

.rule-info small {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
    margin-top: 2px;
}

.rule-badge {
    flex-shrink: 0;
    padding: 4px 10px;
    border-radius: 6px;
    background: var(--color-success-soft);
    color: var(--color-success);
    font-size: 12px;
    font-weight: 800;
}

/* ── 响应式 ── */
@media (max-width: 760px) {
    .options-grid {
        grid-template-columns: 1fr;
    }
    .checkbox-group {
        grid-template-columns: 1fr;
    }
    .upload-zone {
        flex-direction: column;
        text-align: center;
        padding: 16px;
    }
}
</style>