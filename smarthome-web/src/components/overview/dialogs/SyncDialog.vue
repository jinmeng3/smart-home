<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import { useModalConfirm } from "../../../composables/useModalConfirm";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
    "update:modelValue": [value: boolean];
    synced: [];
}>();

const syncOptions = reactive([
    "名称与房间归属",
    "电量与在线状态",
    "检测新接入设备",
]);

const { loading, confirm } = useModalConfirm(() => {
    emit("synced");
    ElMessage.success("同步设备状态操作成功");
    emit("update:modelValue", false);
});
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="同步设备状态"
        description="刷新并同步全屋设备的最新状态与连接信息"
        icon="refresh"
        :width="720"
        :loading="loading"
        confirm-text="开始同步"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="sync-layout">
            <section class="box">
                <b>同步范围</b>
                <p class="section-label">设备范围</p>
                <div class="chips wide">
                    <button
                        v-for="item in [
                            '全部设备',
                            '在线设备',
                            '离线设备',
                            '常用设备',
                        ]"
                        :key="item"
                        type="button"
                        :class="{ active: item === '全部设备' }"
                    >
                        {{ item }}
                    </button>
                </div>
                <p class="section-label">设备来源</p>
                <div class="chips wide">
                    <button
                        v-for="item in [
                            'Home Assistant',
                            'Zigbee 网关',
                            '蓝牙设备',
                            'Matter 设备',
                        ]"
                        :key="item"
                        type="button"
                        :class="{ active: item === 'Home Assistant' }"
                    >
                        {{ item }}
                    </button>
                </div>
                <p class="section-label">同步选项</p>
                <label
                    v-for="item in syncOptions"
                    :key="item"
                    class="switch-row"
                    ><span>{{ item }}<small>更新设备的最新信息</small></span
                    ><input type="checkbox" checked
                /></label>
            </section>
            <aside class="side-stack">
                <div class="box sync-summary">
                    <b>同步概览</b>
                    <p>当前设备总数 <strong>36</strong></p>
                    <p>在线 <strong>28</strong></p>
                    <p>离线 <strong>8</strong></p>
                    <p>预计新增 <strong>2</strong></p>
                </div>
                <div class="box">
                    <b>同步历史</b>
                    <p>今天 09:55　手动同步　<em class="good-tag">成功</em></p>
                    <p>昨天 22:10　自动同步　<em class="good-tag">成功</em></p>
                </div>
            </aside>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.box {
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 16px;
}
.sync-layout {
    display: grid;
    grid-template-columns: 1.65fr 1fr;
    gap: 16px;
}
.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
}
.chips button {
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 7px 12px;
}
.chips button.active {
    border-color: var(--color-primary-400);
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.switch-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px;
}
.switch-row input {
    width: 38px;
    height: 20px;
    accent-color: var(--color-primary-500);
}
.switch-row small {
    display: block;
    color: var(--color-text-tertiary);
}
.side-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.sync-summary p {
    display: flex;
    gap: 8px;
    margin: 10px 0;
    border-bottom: 1px solid var(--color-border-default);
    padding-bottom: 8px;
}
.sync-summary strong {
    margin-left: auto;
}
.section-label {
    margin-top: 16px;
    color: var(--color-text-secondary);
    font-size: 12px;
}
.good-tag {
    border-radius: 10px;
    padding: 3px 8px;
    font-style: normal;
    background: var(--color-success-soft);
    color: var(--color-success);
}
@media (max-width: 760px) {
    .sync-layout {
        grid-template-columns: 1fr;
    }
}
</style>
