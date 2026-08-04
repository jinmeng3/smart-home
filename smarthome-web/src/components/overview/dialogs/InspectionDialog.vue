<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const loading = ref(false);
const inspectionScope = ref("all");
const inspectionItems = reactive([
    "在线状态",
    "电量",
    "网络连接",
    "响应延迟",
    "固件版本",
    "异常告警",
]);

const confirm = async () => {
    loading.value = true;
    await new Promise((resolve) => window.setTimeout(resolve, 450));
    ElMessage.success("全屋巡检操作成功");
    loading.value = false;
    emit("update:modelValue", false);
};
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="全屋巡检"
        description="快速检测全屋设备、网络与自动化状态"
        :width="720"
        :loading="loading"
        confirm-text="开始巡检"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="inspection">
            <div class="inspection-top">
                <section class="box">
                    <b>巡检范围</b>
                    <div class="chips wide">
                        <button
                            v-for="item in [
                                ['all', '全部设备'],
                                ['light', '灯光'],
                                ['air', '空调'],
                                ['lock', '门锁'],
                                ['sensor', '传感器'],
                                ['automation', '自动化'],
                            ]"
                            :key="item[0]"
                            type="button"
                            :class="{ active: inspectionScope === item[0] }"
                            @click="inspectionScope = item[0]"
                        >
                            {{ item[1] }}
                        </button>
                    </div>
                    <b>巡检项目</b>
                    <div class="check-grid">
                        <label v-for="item in inspectionItems" :key="item"
                            ><input type="checkbox" checked />{{ item }}</label
                        >
                    </div>
                </section>
                <aside class="estimate">
                    <small>预计检测</small><strong>36</strong
                    ><span>台设备</span>
                    <hr />
                    <b>◷ 2 <small>分钟</small></b
                    ><span>预计耗时</span>
                </aside>
            </div>
            <section class="box issues">
                <b>最近问题预览 <small>（可能发现）</small></b>
                <p>⚠️ 厨房烟感电池电量低 <em>厨房</em></p>
                <p>⚠️ 阳台门磁长时间未关闭 <em>阳台</em></p>
                <p>♻ 主卧空调滤网需要清洁 <em>主卧</em></p>
            </section>
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
.inspection-top {
    display: grid;
    grid-template-columns: 1fr 140px;
    gap: 12px;
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
.wide {
    margin-bottom: 18px;
}
.check-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-top: 14px;
}
.check-grid input {
    accent-color: var(--color-primary-500);
}
.estimate {
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 16px;
}
.estimate strong {
    color: var(--color-primary-600);
    font-size: 30px;
}
.estimate hr {
    width: 80%;
    border: 0;
    border-top: 1px solid var(--color-border-default);
}
.issues {
    margin-top: 12px;
}
.issues p {
    display: flex;
    margin-top: 8px;
    border-top: 1px solid var(--color-border-default);
    padding-top: 8px;
}
.issues em {
    margin-left: auto;
}
@media (max-width: 760px) {
    .inspection-top {
        grid-template-columns: 1fr;
    }
}
</style>
