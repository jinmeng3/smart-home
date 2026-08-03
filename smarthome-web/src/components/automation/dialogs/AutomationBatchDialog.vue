<script setup lang="ts">
import { computed, ref, watch } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import type { AutomationRule } from "./AutomationFormDialog.vue";

const props = defineProps<{
    modelValue: boolean;
    rules: AutomationRule[];
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    batch: [ids: number[]];
}>();

const batchQuery = ref("");
const batchTab = ref("全部");
const selectedIds = ref<number[]>([]);

const filteredRules = computed(() =>
    props.rules.filter((rule) => {
        const matchesQuery = rule.name.includes(batchQuery.value);
        const matchesTab =
            batchTab.value === "全部" ||
            (batchTab.value === "已启用" && rule.enabled) ||
            (batchTab.value === "未启用" && !rule.enabled);
        return matchesQuery && matchesTab;
    }),
);

watch(
    () => props.modelValue,
    (value) => {
        if (value) {
            selectedIds.value = props.rules
                .filter((rule) => !rule.enabled)
                .map((rule) => rule.id);
        }
    },
);

const close = () => emit("update:modelValue", false);

const confirm = () => {
    emit("batch", selectedIds.value);
    close();
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        icon="power"
        title="批量启用规则"
        description="选择要启用的自动化规则，已启用的规则将保持原状态"
        width="820px"
        :confirm-text="`批量启用 (${selectedIds.length})`"
        @update:model-value="close"
        @confirm="confirm"
    >
        <input
            v-model="batchQuery"
            class="search"
            placeholder="搜索规则名称或关键词"
        />
        <div class="tabs">
            <button
                v-for="tab in ['全部', '已启用', '未启用']"
                :key="tab"
                :class="{ active: batchTab === tab }"
                type="button"
                @click="batchTab = tab"
            >
                {{ tab }}
            </button>
        </div>
        <div class="batch-table">
            <header>
                <span></span><span>规则名称</span><span>状态</span
                ><span>关联房间</span><span>关联设备</span>
            </header>
            <label v-for="rule in filteredRules" :key="rule.id"
                ><input
                    v-model="selectedIds"
                    :value="rule.id"
                    type="checkbox"
                /><span class="rule-name"
                    ><SvgIcon :name="rule.icon" /><span
                        ><b>{{ rule.name }}</b
                        ><small>{{ rule.description }}</small></span
                    ></span
                ><em>{{ rule.enabled ? "已启用" : "未启用" }}</em
                ><span>玄关、客厅</span
                ><span>{{ rule.devices }} 个设备</span></label
            >
        </div>
        <div class="batch-settings">
            <b>已选择 {{ selectedIds.length }} 条规则</b><span>执行设置</span
            ><label><input checked type="radio" /> 立即执行</label
            ><label><input type="radio" /> 仅启用，不立即执行</label>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
input,
select {
    width: 100%;
    border: 1px solid #d9e3f0;
    border-radius: 8px;
    background: #fff;
    padding: 10px;
    color: #26364d;
    outline: 0;
}
.search {
    max-width: 300px;
}
.tabs {
    display: flex;
    gap: 8px;
    margin: 12px 0;
}
.tabs button {
    border: 1px solid #dce5f1;
    border-radius: 7px;
    padding: 7px 10px;
    color: #52637a;
    background: #fff;
}
.tabs button.active {
    border-color: #1769ff;
    color: #1769ff;
    background: #edf4ff;
}
.batch-table {
    overflow: hidden;
    border: 1px solid #dce5f1;
    border-radius: 10px;
}
.batch-table header,
.batch-table label {
    display: grid;
    grid-template-columns: 28px 2fr 0.7fr 1fr 0.7fr;
    align-items: center;
    gap: 10px;
    margin: 0;
    padding: 10px 12px;
    border-bottom: 1px solid #e5ebf2;
}
.batch-table header {
    color: #718198;
    background: #f8fafd;
    font-size: 12px;
}
.batch-table input {
    width: auto;
}
.rule-name {
    display: flex;
    align-items: center;
    gap: 9px;
}
.rule-name > span {
    display: flex;
    flex-direction: column;
}
.rule-name small {
    color: #7d8c9f;
}
.batch-table em {
    width: max-content;
    border-radius: 5px;
    padding: 3px 7px;
    color: #19a45d;
    background: #e7f8ed;
    font-style: normal;
}
.batch-settings {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 14px;
    border: 1px solid #e1e8f1;
    border-radius: 9px;
    padding: 14px;
}
.batch-settings b {
    margin-right: auto;
}
.batch-settings label {
    display: block;
    margin: 0;
}
.batch-settings input {
    width: auto;
}
@media (max-width: 760px) {
    .batch-table header,
    .batch-table label {
        grid-template-columns: 24px 2fr 0.8fr;
    }
    .batch-table header span:nth-child(n + 4),
    .batch-table label > span:nth-child(n + 4) {
        display: none;
    }
}
</style>
