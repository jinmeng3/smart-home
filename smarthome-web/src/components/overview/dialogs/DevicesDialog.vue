<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const deviceRows = [
    ["客厅吸顶灯", "客厅", "灯光", "在线", "—", "10:15", "正常"],
    ["客厅空调", "客厅", "空调", "在线", "26°C", "10:15", "正常"],
    ["主卧空调", "主卧", "空调", "在线", "26°C", "10:14", "正常"],
    ["智能门锁", "玄关", "安防", "在线", "100%", "10:13", "正常"],
    ["空气净化器", "客厅", "环境", "在线", "68%", "10:12", "正常"],
    ["厨房烟感", "厨房", "安防", "在线", "18%", "10:10", "告警"],
    ["阳台门磁", "阳台", "安防", "在线", "100%", "10:09", "正常"],
    ["客厅摄像头", "客厅", "安防", "离线", "—", "09:58", "离线"],
];

const roomFilter = ref("全部房间");
const typeFilter = ref("全部类型");
const statusFilter = ref("全部状态");
const keyword = ref("");

const roomOptions = [...new Set(deviceRows.map((row) => row[1]))];
const typeOptions = [...new Set(deviceRows.map((row) => row[2]))];
const filteredRows = computed(() => {
    const query = keyword.value.trim().toLocaleLowerCase();

    return deviceRows.filter((row) =>
        (roomFilter.value === "全部房间" || row[1] === roomFilter.value) &&
        (typeFilter.value === "全部类型" || row[2] === typeFilter.value) &&
        (statusFilter.value === "全部状态" || row[3] === statusFilter.value) &&
        (!query || row.some((value) => value.toLocaleLowerCase().includes(query))),
    );
});

const onlineCount = computed(() => deviceRows.filter((row) => row[3] === "在线").length);
const alertCount = computed(() => deviceRows.filter((row) => row[6] === "告警").length);

const exportDevices = () => {
    const header = ["设备名称", "所属房间", "设备类型", "当前状态", "电量/温度", "更新时间", "健康状态"];
    const csv = [header, ...filteredRows.value]
        .map((row) => row.map((value) => `"${value.replaceAll('"', '""')}"`).join(","))
        .join("\n");
    const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");

    link.href = url;
    link.download = `设备列表-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    ElMessage.success(`已导出 ${filteredRows.value.length} 台设备`);
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="设备状态总览"
        description="查看在线、离线与异常设备的详细状态"
        :width="860"
        confirm-text="导出列表"
        @confirm="exportDevices"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="devices-dialog">
            <div class="summary">
                <article><small>总设备</small><b>{{ deviceRows.length }}</b></article>
                <article><small>● 在线</small><b>{{ onlineCount }}</b></article>
                <article><small>● 离线</small><b>{{ deviceRows.length - onlineCount }}</b></article>
                <article><small>⚠ 告警</small><b>{{ alertCount }}</b></article>
            </div>
            <div class="filters">
                <select v-model="roomFilter">
                    <option>全部房间</option>
                    <option v-for="room in roomOptions" :key="room">{{ room }}</option></select
                ><select v-model="typeFilter">
                    <option>全部类型</option>
                    <option v-for="type in typeOptions" :key="type">{{ type }}</option></select
                ><select v-model="statusFilter">
                    <option>全部状态</option>
                    <option>在线</option>
                    <option>离线</option></select
                ><input v-model="keyword" placeholder="搜索设备名称" />
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
                        <tr v-for="row in filteredRows" :key="row[0]">
                            <td>{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td :class="row[3] === '在线' ? 'good' : 'warn'">
                                ● {{ row[3] }}
                            </td>
                            <td>{{ row[4] }}</td>
                            <td>{{ row[5] }}</td>
                            <td>
                                <em
                                    :class="
                                        row[6] === '正常'
                                            ? 'good-tag'
                                            : 'warn-tag'
                                    "
                                    >{{ row[6] }}</em
                                >
                            </td>
                        </tr>
                        <tr v-if="filteredRows.length === 0">
                            <td class="empty" colspan="6">没有符合条件的设备</td>
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
.empty {
    height: 120px;
    color: var(--color-text-tertiary);
    text-align: center;
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
