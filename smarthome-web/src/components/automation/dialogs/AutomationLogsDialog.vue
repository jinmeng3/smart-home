<script setup lang="ts">
import { ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";

defineProps<{
    modelValue: boolean;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const expandedLog = ref(1);

const logs = [
    {
        id: 1,
        time: "2026-08-08 10:15:23",
        name: "回家联动",
        source: "位置触发",
        result: "成功",
        duration: "2.4s",
    },
    {
        id: 2,
        time: "2026-08-08 07:00:11",
        name: "晨间唤醒联动",
        source: "定时触发",
        result: "成功",
        duration: "3.1s",
    },
    {
        id: 3,
        time: "2026-08-07 23:00:05",
        name: "夜间回家照明",
        source: "手动触发",
        result: "成功",
        duration: "1.8s",
    },
    {
        id: 4,
        time: "2026-08-07 19:42:12",
        name: "离家安防联动",
        source: "位置触发",
        result: "失败",
        duration: "0.9s",
    },
];

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        icon="log"
        title="执行日志"
        description="查看自动化规则的执行记录与结果，便于排查与优化"
        width="860px"
        confirm-text="关闭"
        @update:model-value="close"
        @confirm="close"
    >
        <div class="log-filters">
            <input type="date" value="2026-08-08" /><select>
                <option>规则名称</option></select
            ><select>
                <option>执行结果：全部</option></select
            ><button type="button">搜索</button>
        </div>
        <div class="log-table">
            <header>
                <span>执行时间</span><span>规则名称</span><span>触发来源</span
                ><span>执行结果</span><span>耗时</span><span>详情</span>
            </header>
            <template v-for="log in logs" :key="log.id"
                ><button
                    class="log-row"
                    type="button"
                    @click="expandedLog = expandedLog === log.id ? 0 : log.id"
                >
                    <span>{{ log.time }}</span
                    ><b>{{ log.name }}</b
                    ><span>{{ log.source }}</span
                    ><em :class="{ fail: log.result === '失败' }"
                        >◉ {{ log.result }}</em
                    ><span>{{ log.duration }}</span
                    ><span>{{ expandedLog === log.id ? "⌃" : "⌄" }}</span>
                </button>
                <div v-if="expandedLog === log.id" class="log-detail">
                    <div>
                        <b>触发详情</b>
                        <p>设备“小明的手机”到达“家”半径 100m</p>
                        <b>条件检查</b>
                        <p>✓ 时间条件　✓ 设备在线　✓ 位置条件</p>
                    </div>
                    <div>
                        <b>执行动作（共 4 个）</b>
                        <p>✓ 玄关灯开启　✓ 客厅灯带开启</p>
                        <p>✓ 空调 26°C　✓ 客厅窗帘打开</p>
                    </div>
                </div></template
            >
        </div>
    </BaseSmartModal>
</template>

<style scoped>
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
.log-filters {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr auto;
    gap: 8px;
    margin-bottom: 14px;
}
.log-filters button {
    border-radius: 8px;
    padding: 0 18px;
    color: #fff;
    background: var(--color-primary-600);
}
.log-table {
    overflow: hidden;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
}
.log-table header,
.log-row {
    display: grid;
    width: 100%;
    grid-template-columns: 1.35fr 1.3fr 1fr 0.8fr 0.5fr 0.35fr;
    align-items: center;
    gap: 8px;
    padding: 11px 14px;
    text-align: left;
}
.log-table header {
    color: var(--color-text-tertiary);
    background: var(--color-surface-subtle);
    font-size: 12px;
    font-weight: 700;
}
.log-row {
    border-top: 1px solid var(--color-border-subtle);
    background: var(--color-card-bg);
    font-size: 12px;
}
.log-row em {
    color: var(--color-success);
    font-style: normal;
}
.log-row em.fail {
    color: var(--color-danger);
}
.log-detail {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin: 0 10px 10px;
    padding: 16px;
    border: 1px solid var(--color-primary-200);
    border-radius: 9px;
    background: var(--color-primary-50);
    font-size: 12px;
}
.log-detail p {
    margin: 8px 0;
    color: var(--color-text-tertiary);
}
@media (max-width: 760px) {
    .log-detail {
        grid-template-columns: 1fr;
    }
}
</style>
