<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const loading = ref(false);

const deviceRows = [
    ["客厅吸顶灯", "客厅", "在线", "—", "10:15", "正常"],
    ["客厅空调", "客厅", "在线", "26°C", "10:15", "正常"],
    ["主卧空调", "主卧", "在线", "26°C", "10:14", "正常"],
    ["智能门锁", "玄关", "在线", "100%", "10:13", "正常"],
    ["空气净化器", "客厅", "在线", "68%", "10:12", "正常"],
    ["厨房烟感", "厨房", "在线", "18%", "10:10", "告警"],
    ["阳台门磁", "阳台", "在线", "100%", "10:09", "正常"],
    ["客厅摄像头", "客厅", "离线", "—", "09:58", "离线"],
];

const confirm = async () => {
    loading.value = true;
    await new Promise((resolve) => window.setTimeout(resolve, 450));
    ElMessage.success("设备状态总览操作成功");
    loading.value = false;
    emit("update:modelValue", false);
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="设备状态总览"
        description="查看在线、离线与异常设备的详细状态"
        :width="860"
        :loading="loading"
        confirm-text="导出列表"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="devices-dialog">
            <div class="summary">
                <article><small>总设备</small><b>36</b></article>
                <article><small>● 在线</small><b>28</b></article>
                <article><small>● 离线</small><b>8</b></article>
                <article><small>⚠ 告警</small><b>3</b></article>
            </div>
            <div class="filters">
                <select>
                    <option>全部房间</option></select
                ><select>
                    <option>全部类型</option></select
                ><select>
                    <option>全部状态</option></select
                ><input placeholder="搜索设备名称" />
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>设备名称</th>
                            <th>所属房间</th>
                            <th>当前状态</th>
                            <th>电量 / 温度</th>
                            <th>更新时间</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="row in deviceRows" :key="row[0]">
                            <td>{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td :class="row[2] === '在线' ? 'good' : 'warn'">
                                ● {{ row[2] }}
                            </td>
                            <td>{{ row[3] }}</td>
                            <td>{{ row[4] }}</td>
                            <td>
                                <em
                                    :class="
                                        row[5] === '正常'
                                            ? 'good-tag'
                                            : 'warn-tag'
                                    "
                                    >{{ row[5] }}</em
                                >
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}
.summary article {
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    padding: 14px;
}
.summary b {
    display: block;
    font-size: 24px;
}
.filters {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 14px 0;
}
.filters input,
.filters select {
    height: 38px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 0 11px;
}
.table-wrap {
    overflow: auto;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
th,
td {
    border-bottom: 1px solid var(--color-border-default);
    padding: 10px;
    text-align: left;
    white-space: nowrap;
}
.good {
    color: var(--color-success);
}
.warn {
    color: var(--color-warning);
}
.good-tag,
.warn-tag {
    border-radius: 10px;
    padding: 3px 8px;
    font-style: normal;
}
.good-tag {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.warn-tag {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}
@media (max-width: 760px) {
    .summary {
        grid-template-columns: 1fr 1fr;
    }
    .filters {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
