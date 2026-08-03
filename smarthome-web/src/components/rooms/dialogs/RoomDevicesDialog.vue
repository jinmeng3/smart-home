<script setup lang="ts">
import { computed, ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import type { Room } from "../../../types/room";

const props = defineProps<{
    modelValue: boolean;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const deviceKeyword = ref("");

const title = "房间设备管理";
const description = `统一管理${props.room?.name ?? "房间"}内的设备状态、分组与快捷控制`;

const deviceRows = computed(() => {
    const rows: Array<[string, string, string, string, string, string]> = [
        ["吸顶灯", "灯光", "开启", "亮度 80%", "今天 10:25", "light"],
        ["落地灯", "灯光", "开启", "亮度 60%", "今天 10:25", "light"],
        ["电视", "影音", "开启", "HDMI 1", "今天 10:24", "device-management"],
        ["空调", "环境", "开启", "24°C｜制冷", "今天 10:24", "air-conditioner"],
        ["窗帘电机", "窗帘", "开启", "打开 70%", "今天 10:24", "curtain"],
        ["空气净化器", "环境", "开启", "自动模式｜优", "今天 10:24", "sensor"],
        ["智能插座", "电源", "开启", "功率 35W", "今天 10:24", "plug"],
        [
            "温湿度传感器",
            "传感器",
            "正常",
            "温湿度传感器",
            "今天 10:24",
            "humidity",
        ],
    ];

    return rows.filter((row) => row[0].includes(deviceKeyword.value.trim()));
});

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="title"
        :description="description"
        confirm-text="保存设置"
        width="large"
        @cancel="close"
        @update:model-value="close"
    >
        <div class="devices-dialog">
            <header>
                <div class="room-summary">
                    <span><SvgIcon name="room" size="lg" /></span>
                    <div>
                        <h3>{{ room?.name }}</h3>
                        <small>● 在线</small>
                    </div>
                </div>
                <article>
                    <small>设备总数</small><strong>8 <i>个设备</i></strong>
                </article>
                <article>
                    <small>在线设备</small><strong>8 <i>/ 8</i></strong>
                </article>
                <article>
                    <small>常用分组</small><strong>6 <i>个分组</i></strong>
                </article>
            </header>
            <div class="device-toolbar">
                <input
                    v-model="deviceKeyword"
                    placeholder="搜索设备名称"
                /><select>
                    <option>全部类型</option></select
                ><select>
                    <option>全部状态</option></select
                ><button type="button">批量开关</button
                ><button type="button">分组管理</button
                ><button type="button">设为常用</button>
            </div>
            <div class="device-table">
                <div>
                    <span>设备名称</span><span>所属分组</span
                    ><span>当前状态</span><span>电量 / 模式</span
                    ><span>更新时间</span><span>快捷操作</span>
                </div>
                <article v-for="row in deviceRows" :key="row[0]">
                    <span
                        ><i><SvgIcon :name="row[5]" size="sm" /></i
                        >{{ row[0] }}</span
                    ><span>{{ row[1] }}</span
                    ><span class="success">● {{ row[2] }}</span
                    ><span>{{ row[3] }}</span
                    ><span>{{ row[4] }}</span
                    ><button type="button">●</button>
                </article>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.devices-dialog > header {
    display: grid;
    grid-template-columns: 1.2fr repeat(3, 1fr);
    gap: 10px;
}
.devices-dialog > header article,
.room-summary {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 11px;
}
.devices-dialog > header article {
    display: grid;
}
.devices-dialog > header small {
    color: var(--color-text-tertiary);
}
.devices-dialog > header strong {
    font-size: 20px;
}
.devices-dialog > header i {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-style: normal;
}
.room-summary > span {
    display: grid;
    width: 50px;
    height: 50px;
    place-items: center;
    border-radius: 9px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.room-summary h3 {
    margin: 0;
}
.room-summary small {
    color: var(--color-success) !important;
}
.device-toolbar {
    display: grid;
    grid-template-columns: 1.4fr 0.8fr 0.8fr repeat(3, auto);
    gap: 8px;
    margin: 12px 0;
}
.device-toolbar input,
.device-toolbar select {
    width: 100%;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
}
.device-toolbar button {
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 0 10px;
    background: var(--color-card-bg);
    font-size: 10px;
}
.device-table {
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}
.device-table > div,
.device-table article {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr 1.2fr 1.1fr 0.7fr;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    font-size: 10px;
}
.device-table > div {
    background: var(--color-surface-subtle);
    font-weight: 900;
}
.device-table article {
    border-top: 1px solid var(--color-border-subtle);
}
.device-table article > span:first-child {
    display: flex;
    align-items: center;
    gap: 7px;
    font-weight: 800;
}
.device-table article i {
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border-radius: 7px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    font-style: normal;
}
.device-table article button {
    width: 29px;
    height: 16px;
    border-radius: 999px;
    background: var(--color-primary-600);
    color: white;
}
.success {
    color: var(--color-success) !important;
}
@media (max-width: 760px) {
    .devices-dialog > header {
        grid-template-columns: 1fr 1fr;
    }
    .device-toolbar {
        grid-template-columns: 1fr 1fr;
    }
    .device-table {
        overflow-x: auto;
    }
    .device-table > * {
        min-width: 760px;
    }
}
</style>
