<script setup lang="ts">
import { computed, ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import type { Room } from "../../../types/room";

const props = defineProps<{
    modelValue: boolean;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const logKeyword = ref("");
const logPage = ref(1);

const title = "房间活动日志";
const description = `查看${props.room?.name ?? "房间"}最近的设备操作、环境变化与自动化执行记录`;

const logs = computed(() =>
    [
        ["2026-08-04 10:15:32", "手动操作", "灯光开启", "成功", "灯光　客厅"],
        [
            "2026-08-04 10:12:08",
            "语音助手",
            "空调切换制冷 24°C",
            "成功",
            "空调　温度",
        ],
        ["2026-08-04 09:58:41", "手机 App", "窗帘打开", "成功", "窗帘　遮阳"],
        [
            "2026-08-04 09:30:00",
            "自动化",
            "自动化执行“休闲模式”",
            "成功",
            "场景　自动化",
        ],
        [
            "2026-08-04 08:45:21",
            "环境监测",
            "PM2.5 变化提醒",
            "提醒",
            "环境　PM2.5",
        ],
    ].filter((row) => row.join(" ").includes(logKeyword.value.trim())),
);

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="title"
        :description="description"
        confirm-text="关闭"
        width="large"
        @cancel="close"
        @update:model-value="close"
    >
        <div class="logs-dialog">
            <div class="dialog-filters">
                <label>日期范围<input value="2026-07-29 ~ 2026-08-04" /></label
                ><label
                    >日志类型<select>
                        <option>全部类型</option>
                    </select></label
                ><label
                    >设备名称<select>
                        <option>全部设备</option>
                    </select></label
                ><label
                    >搜索<input v-model="logKeyword" placeholder="搜索事件内容"
                /></label>
            </div>
            <div class="data-table">
                <div class="table-head">
                    <span>时间</span><span>来源</span><span>事件内容</span
                    ><span>执行结果</span><span>标签</span>
                </div>
                <article v-for="row in logs" :key="row[0]">
                    <time>{{ row[0] }}</time
                    ><span>{{ row[1] }}</span
                    ><strong>{{ row[2] }}</strong
                    ><span class="success">● {{ row[3] }}</span
                    ><small>{{ row[4] }}</small>
                </article>
            </div>
            <div class="pagination">
                <span>共 32 条记录</span><button type="button">‹</button
                ><button
                    v-for="page in [1, 2, 3, 4]"
                    :key="page"
                    :class="{ active: logPage === page }"
                    type="button"
                    @click="logPage = page"
                >
                    {{ page }}</button
                ><button type="button">›</button>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.dialog-filters {
    display: grid;
    grid-template-columns: 1.2fr 1fr 1fr 1.1fr;
    gap: 10px;
    margin-bottom: 12px;
}
.dialog-filters label {
    display: grid;
    gap: 6px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
}
.dialog-filters input,
.dialog-filters select {
    width: 100%;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
    color: var(--color-text-primary);
}

.dialog-filters select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}
.data-table {
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}
.table-head,
.data-table article {
    display: grid;
    grid-template-columns: 1.15fr 1fr 1.6fr 1.1fr 1.2fr;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    font-size: 11px;
}
.table-head {
    background: var(--color-surface-subtle);
    font-weight: 900;
}
.data-table article {
    border-top: 1px solid var(--color-border-subtle);
}
.data-table small {
    color: var(--color-primary-600);
}
.success {
    color: var(--color-success) !important;
}
.pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    margin-top: 12px;
}
.pagination span {
    margin-right: auto;
    color: var(--color-text-tertiary);
    font-size: 11px;
}
.pagination button {
    min-width: 30px;
    height: 30px;
    border: 1px solid var(--color-border);
    border-radius: 7px;
    background: var(--color-card-bg);
}
.pagination button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
@media (max-width: 760px) {
    .dialog-filters {
        grid-template-columns: 1fr;
    }
    .data-table {
        overflow-x: auto;
    }
    .data-table > * {
        min-width: 700px;
    }
}
</style>
