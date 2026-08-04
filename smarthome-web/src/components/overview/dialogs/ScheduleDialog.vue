<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import { useModalConfirm } from "../../../composables/useModalConfirm";

defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();

const autoSync = ref(true);

const schedules = reactive([
    {
        time: "07:00",
        name: "起床模式",
        detail: "窗帘打开 · 卧室灯亮 · 空调制热 24°C",
        color: "#ff9418",
    },
    {
        time: "19:00",
        name: "回家模式",
        detail: "玄关灯亮 · 空调制冷 26°C · 新风开启",
        color: "#3478f6",
    },
    {
        time: "22:00",
        name: "离家模式",
        detail: "关闭灯光 · 安防布防 · 监控夜视",
        color: "#20b86a",
    },
    {
        time: "23:00",
        name: "睡眠模式",
        detail: "灯光渐暗 · 窗帘关闭 · 安防设防",
        color: "#825bea",
    },
]);

const { loading, confirm } = useModalConfirm(() => {
    ElMessage.success("编辑家庭日程操作成功");
    emit("update:modelValue", false);
});
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        title="编辑家庭日程"
        description="管理家庭日程与自动化计划"
        :width="720"
        :loading="loading"
        confirm-text="保存计划"
        @confirm="confirm"
        @update:model-value="emit('update:modelValue', false)"
    >
        <div class="schedule-dialog">
            <div class="date-bar">
                ▣　2025年5月20日 星期二 <span>‹　›</span>
            </div>
            <div class="schedule-list">
                <article v-for="item in schedules" :key="item.time">
                    <time>{{ item.time }}</time
                    ><i :style="{ background: item.color }" /><b>{{
                        item.name
                    }}</b
                    ><small>{{ item.detail }}</small
                    ><button type="button">✎</button
                    ><button type="button">♲</button>
                </article>
            </div>
            <section class="setting-row">
                <div><b>重复设置</b><small>选择重复执行的星期</small></div>
                <div class="chips">
                    <button
                        v-for="day in [
                            '周一',
                            '周二',
                            '周三',
                            '周四',
                            '周五',
                            '周六',
                            '周日',
                        ]"
                        :key="day"
                        type="button"
                        :class="{ active: day !== '周日' }"
                    >
                        {{ day }}
                    </button>
                </div>
                <label
                    >启用自动执行 <input v-model="autoSync" type="checkbox"
                /></label>
            </section>
            <section>
                <b>关联房间 / 设备</b>
                <div class="chips">
                    <button
                        v-for="item in [
                            '客厅',
                            '玄关',
                            '主卧',
                            '空调',
                            '灯光',
                            '窗帘',
                        ]"
                        :key="item"
                        type="button"
                        class="active"
                    >
                        {{ item }}
                    </button>
                </div>
            </section>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.date-bar {
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 14px;
    font-weight: 800;
}
.date-bar span {
    float: right;
}
.schedule-list article {
    display: grid;
    grid-template-columns: 55px 8px 90px 1fr 34px 34px;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 11px;
}
.schedule-list i {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}
.schedule-list button {
    border: 1px solid var(--color-border-default);
    border-radius: 7px;
    background: var(--color-panel-background);
    padding: 5px;
}
.setting-row {
    display: grid;
    grid-template-columns: 130px 1fr auto;
    align-items: center;
    margin: 14px 0;
    border-top: 1px solid var(--color-border-default);
    border-bottom: 1px solid var(--color-border-default);
    padding: 12px 0;
}
.setting-row small,
.chips small {
    display: block;
    color: var(--color-text-tertiary);
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
.setting-row input {
    width: 38px;
    height: 20px;
    accent-color: var(--color-primary-500);
}
@media (max-width: 760px) {
    .schedule-list article {
        grid-template-columns: 50px 8px 1fr auto auto;
    }
    .schedule-list small {
        grid-column: 3/-1;
    }
    .setting-row {
        grid-template-columns: 1fr;
    }
}
</style>
