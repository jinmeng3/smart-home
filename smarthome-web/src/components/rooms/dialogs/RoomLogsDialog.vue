<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import { getRoomLogs } from "../../../api/room";
import { useLatestRequest } from "../../../composables/useLatestRequest";
import type { Room } from "../../../types/room";
import type { RoomLog } from "../../../types/room";

const props = defineProps<{
    modelValue: boolean;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const logKeyword = ref("");
const logPage = ref(1);
const logTotal = ref(0);
const logs = ref<RoomLog[]>([]);
const pageSize = 10;
const { loading, run } = useLatestRequest();

const totalPages = Math.max(1, Math.ceil(logTotal.value / pageSize));

const load = async () => {
    if (!props.room) return;
    await run(
        () =>
            getRoomLogs(props.room!.id, {
                keyword: logKeyword.value.trim() || undefined,
                page: logPage.value,
                page_size: pageSize,
            }),
        (result) => {
            logs.value = result.items;
            logTotal.value = result.total;
        },
        () => {
            logs.value = [];
            logTotal.value = 0;
        },
    );
};

const goPage = (page: number) => {
    if (page < 1 || page > totalPages || page === logPage.value) return;
    logPage.value = page;
    void load();
};

const close = () => emit("update:modelValue", false);

watch([logKeyword, () => props.modelValue], () => {
    logPage.value = 1;
    if (props.modelValue) void load();
});

onMounted(() => {
    if (props.modelValue) void load();
});
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="`房间活动日志`"
        :description="`查看${props.room?.name ?? '房间'}最近的设备操作、环境变化与自动化执行记录`"
        confirm-text="关闭"
        width="large"
        @cancel="close"
        @update:model-value="close"
    >
        <div class="logs-dialog">
            <div class="dialog-filters">
                <label
                    >搜索<input
                        v-model="logKeyword"
                        placeholder="搜索事件内容"
                /></label>
            </div>
            <div class="data-table">
                <div class="table-head">
                    <span>时间</span><span>来源</span><span>事件内容</span
                    ><span>执行结果</span><span>标签</span>
                </div>
                <template v-if="loading">
                    <div class="table-state">加载中…</div>
                </template>
                <template v-else-if="logs.length === 0">
                    <div class="table-state">暂无日志记录</div>
                </template>
                <article v-for="log in logs" :key="log.id">
                    <time>{{ log.occurredAt }}</time
                    ><span>{{ log.source }}</span
                    ><strong>{{ log.event }}</strong
                    ><span
                        :class="
                            log.result === 'success'
                                ? 'success'
                                : log.result === 'failed'
                                  ? 'failed'
                                  : ''
                        "
                        >● {{ log.result }}</span
                    ><small>{{ (log.tags ?? []).join("、") }}</small>
                </article>
            </div>
            <div class="pagination">
                <span>共 {{ logTotal }} 条记录</span>
                <button
                    type="button"
                    :disabled="logPage <= 1"
                    @click="goPage(logPage - 1)"
                >
                    ‹
                </button>
                <button
                    v-for="page in totalPages > 5 ? [logPage] : Array.from({ length: totalPages }, (_, i) => i + 1)"
                    :key="page"
                    :class="{ active: logPage === page }"
                    type="button"
                    @click="goPage(page)"
                >
                    {{ page }}
                </button>
                <button
                    type="button"
                    :disabled="logPage >= totalPages"
                    @click="goPage(logPage + 1)"
                >
                    ›
                </button>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.dialog-filters {
    display: grid;
    grid-template-columns: 1fr;
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
.table-state {
    padding: 28px 12px;
    color: var(--color-text-tertiary);
    text-align: center;
    font-size: 12px;
}
.success {
    color: var(--color-success) !important;
}
.failed {
    color: var(--color-danger) !important;
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