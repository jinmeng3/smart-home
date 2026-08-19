<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useAutomationsStore, buildAutomationSteps } from "../stores/automations";
import { useAutomationModeController } from "../composables/useAutomationModeController";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { useCardGridEnter } from "../composables/useCardGridEnter";
import { useGsapFlip } from "../composables/useGsapFlip";
import AutomationDialogs from "../components/automation/AutomationDialogs.vue";
import ConfirmActionDialog from "../components/common/ConfirmActionDialog.vue";
import ConfirmEntitySummary from "../components/common/ConfirmEntitySummary.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import StatsCard from "../components/common/StatsCard.vue";

const store = useAutomationsStore();
const {
    automations,
    filters,
    runningId,
    selectedId,
    selectedAutomation: selected,
    selectedDetail,
    executions,
    stats,
    stepStatuses,
    visible,
} = storeToRefs(store);
const controller = useAutomationModeController(store);

const flowSteps = computed(() =>
    selected.value ? buildAutomationSteps(selected.value, selectedDetail.value) : [],
);

const records = computed(() =>
    executions.value.slice(0, 4).map((record) => ({
        id: record.id,
        time: new Intl.DateTimeFormat("zh-CN", {
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        }).format(new Date(record.startedAt)),
        name: selected.value?.name ?? "自动化",
        result: record.status === "success" ? "成功" : record.status === "failed" ? "失败" : "执行中",
        success: record.status === "success",
        duration: record.durationMs === null ? "--" : `${(record.durationMs / 1000).toFixed(1)}s`,
    })),
);

const cardsExpanded = ref(false);
const visibleCards = computed(() =>
    cardsExpanded.value ? visible.value : visible.value.slice(0, 3),
);

/** 最近一次运行的反馈：success / error，短暂显示后清除 */
const runFeedbacks = ref<Record<number, "success" | "error">>({});
const runFeedbackTimers = new Map<number, ReturnType<typeof setTimeout>>();
const showRunFeedback = (id: number, result: "success" | "error") => {
    runFeedbacks.value = { ...runFeedbacks.value, [id]: result };
    const prev = runFeedbackTimers.get(id);
    if (prev) clearTimeout(prev);
    runFeedbackTimers.set(
        id,
        setTimeout(() => {
            const next = { ...runFeedbacks.value };
            delete next[id];
            runFeedbacks.value = next;
            runFeedbackTimers.delete(id);
        }, 1200),
    );
};
const handleRunRule = async (item: any) => {
    try {
        await controller.runRule(item);
        showRunFeedback(item.id, "success");
    } catch {
        showRunFeedback(item.id, "error");
    }
};

/** 复制规则后高亮新副本名称一次 */
const highlightedRuleId = ref<number | null>(null);
let highlightTimer: ReturnType<typeof setTimeout> | undefined;
const handleCopyRule = async (item: any) => {
    try {
        await controller.copyRule(item);
        // 复制完成后高亮新副本（通常排在原规则之后）
        const newRule = store.automations.find(
            (rule) => rule.id !== item.id && rule.name.includes(`${item.name} 副本`),
        );
        highlightedRuleId.value = newRule?.id ?? null;
        if (highlightedRuleId.value !== null) {
            if (highlightTimer) clearTimeout(highlightTimer);
            highlightTimer = setTimeout(() => {
                highlightedRuleId.value = null;
                highlightTimer = undefined;
            }, 1600);
        }
    } catch {
        // 错误提示由 controller 内部处理
    }
};

/** 批量启用：只对实际变化的可见卡片播放一次高亮 */
const batchChangedIds = ref<Set<number>>(new Set());
let batchHighlightTimer: ReturnType<typeof setTimeout> | undefined;
const handleBatchEnable = async (ruleIds: number[]) => {
    const before = new Map(automations.value.map((r) => [r.id, r.enabled]));
    try {
        await controller.batchEnable(ruleIds);
        const changed = automations.value
            .filter((r) => before.get(r.id) !== r.enabled)
            .map((r) => r.id);
        batchChangedIds.value = new Set(changed);
        if (batchHighlightTimer) clearTimeout(batchHighlightTimer);
        batchHighlightTimer = setTimeout(() => {
            batchChangedIds.value = new Set();
            batchHighlightTimer = undefined;
        }, 1400);
    } catch {
        // 错误提示由 controller 内部处理
    }
};

const loadAutomations = async () => {
    await store.loadAutomations();
};

useAuthenticatedLoader(loadAutomations);

const { root, play: playCardGrid } = useCardGridEnter();

/* === GSAP Flip 自动化卡片增删重排 === */
const cardsGridRef = ref<HTMLElement | null>(null);
const { captureAndFlip: flipCards } = useGsapFlip({
    container: cardsGridRef,
    itemSelector: ".cards > article",
    duration: 240,
});

// 卡片入场 stagger：数据加载完成后 + 展开/收起状态变更时
onMounted(() => void playCardGrid());
watch(() => visibleCards.value.length, (n) => { if (n > 0) void playCardGrid(); });
watch(cardsExpanded, () => { void nextTick(() => playCardGrid()); });

// 卡片增删/筛选变化时播放 Flip，保持位置连续
watch(
    () => visible.value.length,
    () => {
        void flipCards();
    },
);
</script>

<template>
    <div class="app-page-layout">
        <main ref="root" class="automation page-shell">
            <header class="automation-page-header">
                <div class="automation-page-title">
                    <span
                        class="page-header-icon"
                        style="background: var(--tone-indigo-soft); color: var(--tone-indigo)"
                        aria-hidden="true"
                    >
                        <SvgIcon name="automation" />
                    </span>
                    <div>
                        <h1>自动化</h1>
                        <p>管理家庭自动化规则、触发条件与执行状态</p>
                    </div>
                </div>
                <div class="filters">
                    <label class="filters-search"
                        ><SvgIcon name="search" /><input
                            v-model="filters.keyword"
                            type="search"
                            placeholder="搜索自动化规则" /></label
                    ><select v-model="filters.triggerType" title="触发类型">
                        <option value="">全部触发</option>
                        <option>位置触发</option>
                        <option>时间触发</option>
                        <option>设备状态</option></select
                    ><select v-model="filters.enabled" title="启用状态">
                        <option value="all">全部状态</option>
                        <option value="true">已启用</option>
                        <option value="false">已停用</option></select
                    ><button class="primary" @click="controller.openCreateDialog()">
                        <SvgIcon name="plus" />创建自动化</button
                    ><button @click="controller.openImportDialog()">
                        <SvgIcon name="upload" />导入规则
                    </button>
                </div>
            </header>
            <Transition name="stats-fade">
                <section v-if="!cardsExpanded" class="stats card-grid-enter">
                    <StatsCard
                        icon="check-circle"
                        label="已启用规则"
                        :value="stats.enabled"
                        :detail="`共 ${stats.total} 条规则`"
                        tone="blue"
                    />
                    <StatsCard
                        icon="power"
                        label="运行中"
                        :value="stats.running"
                        detail="正在执行"
                        tone="green"
                    />
                    <StatsCard
                        icon="calendar"
                        label="今日执行次数"
                        :value="`${stats.executionsToday} 次`"
                            detail="来自后端执行记录"
                        tone="orange"
                    />
                    <StatsCard
                        icon="warning"
                        label="异常规则"
                        :value="stats.abnormal"
                        detail="需要处理"
                        tone="red"
                    />
                </section>
            </Transition>
            <section
                ref="cardsGridRef"
                class="cards card-grid-enter"
                :class="{ 'is-expanded': cardsExpanded }"
            >
                <div v-if="!visible.length" class="cards-empty">
                    暂无匹配规则
                </div>
                <article
                    v-for="item in visibleCards"
                    :key="item.id"
                    :class="{
                        selected: item.id === selectedId,
                        disabled: !item.enabled,
                        'is-copy-highlight': item.id === highlightedRuleId,
                        'is-batch-changed': batchChangedIds.has(item.id),
                    }"
                    @click="store.selectAutomation(item.id)"
                >
                    <header>
                        <i :class="item.tone"><SvgIcon :name="item.icon" /></i
                        ><span
                            ><b :class="{ 'name-highlight': item.id === highlightedRuleId }">{{ item.name }}</b
                            ><em>{{ item.enabled ? "已启用" : "已停用" }}</em
                            ><small>{{ item.description }}</small></span
                        ><button
                            type="button"
                            title="更多操作"
                            @click.stop="controller.openEditDialog(item)"
                        >
                            ⋮
                        </button>
                    </header>
                    <div class="devices">
                        <i class="dev-light"><SvgIcon name="light" size="sm" /></i
                        ><i class="dev-curtain"
                            ><SvgIcon name="curtain" size="sm" /></i
                        ><i class="dev-temp"
                            ><SvgIcon name="temperature" size="sm" /></i
                        ><span>等 {{ item.devices }} 个设备</span>
                    </div>
                    <footer>
                        <button
                            class="run-rule-btn"
                            :disabled="runningId === item.id"
                            @click.stop="handleRunRule(item)"
                        >
                            <SvgIcon
                                v-if="runFeedbacks[item.id] === 'success'"
                                name="check"
                                size="sm"
                            /><SvgIcon
                                v-else-if="runFeedbacks[item.id] === 'error'"
                                name="warning"
                                size="sm"
                            /><SvgIcon
                                v-else-if="runningId === item.id"
                                name="refresh"
                                size="sm"
                                class="is-spinning"
                            /><SvgIcon v-else name="power" size="sm"
                            />{{ runningId === item.id ? "执行中" : "执行" }}</button
                        ><button @click.stop="controller.openEditDialog(item)">
                            <SvgIcon name="edit" size="sm" />编辑</button
                        ><button
                            class="card-copy"
                            type="button"
                            title="复制规则"
                            @click.stop="handleCopyRule(item)"
                        >
                            <SvgIcon name="layers" size="sm" />复制
                        </button
                        ><label class="switch"
                            ><input
                                :checked="item.enabled"
                                type="checkbox"
                                @change="
                                    controller.toggleRule(
                                        item,
                                        ($event.target as HTMLInputElement).checked,
                                    )
                                " /><span></span
                        ></label>
                        <button
                            class="card-delete"
                            type="button"
                            title="删除自动化"
                            @click.stop="controller.removeRule(item)"
                        >
                            <SvgIcon name="delete" size="sm" />
                        </button>
                    </footer>
                </article>
            </section>
            <div v-if="visible.length > 3" class="cards-footer">
                <button
                    class="automation-view-all"
                    type="button"
                    @click="cardsExpanded = !cardsExpanded"
                >
                    {{ cardsExpanded ? "收起规则" : `查看全部规则（${visible.length}）` }}
                    <span
                        class="chevron-icon"
                        :class="{ 'is-expanded': cardsExpanded }"
                    >
                        <SvgIcon name="chevron-down" />
                    </span>
                </button>
            </div>
            <section class="panel flow">
                <header>
                    <div class="flow-heading">
                        <span class="flow-heading-icon"><SvgIcon name="automation" /></span>
                        <span>
                            <h2>自动化流程</h2>
                            <small>{{ selected ? `${selected.name} · ${flowSteps.length} 个步骤` : "选择规则后查看执行链路" }}</small>
                        </span>
                    </div>
                    <a @click="controller.openLogsDialog()">查看更多 ›</a>
                </header>
                <div class="flow-body">
                    <!-- 切换规则时标题与步骤列表 180–220ms 交叉淡入 -->
                    <Transition name="step-crossfade" mode="out-in">
                        <div
                            v-if="flowSteps.length"
                            :key="selected?.id ?? 'none'"
                            class="steps"
                        >
                            <div
                                v-for="(step, index) in flowSteps"
                                :key="step.id"
                                :class="`is-${stepStatuses[step.id] ?? 'pending'}`"
                            >
                                <div class="step-card">
                                    <span class="step-index">{{ String(index + 1).padStart(2, "0") }}</span>
                                    <i :class="`is-${step.tone}`">
                                        <SvgIcon :name="step.icon" />
                                        <span v-if="index === 0" class="step-trigger-badge">触发</span>
                                    </i>
                                    <b>{{ step.name }}</b>
                                    <small>{{ step.description }}</small>
                                    <span class="step-status">
                                        {{ (stepStatuses[step.id] ?? "pending") === "completed" ? "已完成" : (stepStatuses[step.id] ?? "pending") === "running" ? "执行中" : "等待执行" }}
                                    </span>
                                </div>
                                <div v-if="index < flowSteps.length - 1" class="step-connector">
                                    <SvgIcon name="chevron-right" size="sm" />
                                </div>
                            </div>
                        </div>
                        <div v-else key="empty" class="flow-empty">
                            <span><SvgIcon name="automation" /></span>
                            <strong>暂无可展示的自动化流程</strong>
                            <small>请选择一条规则，或创建包含执行动作的自动化</small>
                        </div>
                    </Transition>
                    <div class="records">
                        <h3>最近执行</h3>
                        <div class="records-list">
                            <div v-for="row in records" :key="row.id" class="record-row">
                                <time>{{ row.time }}</time>
                                <span class="record-name">{{ row.name }}</span>
                                <span class="record-result" :class="{ 'is-success': row.success }">
                                    <SvgIcon :name="row.success ? 'check-circle' : 'warning'" size="sm" />{{ row.result }}
                                </span>
                                <em class="record-duration">{{ row.duration }}</em>
                            </div>
                            <div v-if="!records.length" class="records-empty">暂无执行记录</div>
                        </div>
                    </div>
                </div>
            </section>
        </main>
        <aside class="right page-shell">
            <section class="panel detail">
                <template v-if="selected">
                    <header>
                        <h2>▣ 规则详情</h2>
                        <SvgIcon name="scan" size="sm" />
                    </header>
                    <div class="detail-title">
                        <i :class="selected.tone"
                            ><SvgIcon :name="selected.icon" /></i
                        ><span
                            ><h3>{{ selected.name }}</h3>
                            <em>{{ selected.enabled ? "已启用" : "已停用" }}</em>
                            <p>{{ selected.description }}</p></span
                        >
                    </div>
                    <dl>
                        <div>
                            <dt>触发条件</dt>
                            <dd>{{ selected.description }}</dd>
                        </div>
                        <div>
                            <dt>执行方式</dt>
                            <dd>{{ selectedDetail?.triggers[0]?.type === "manual" ? "手动执行" : "自动执行" }}</dd>
                        </div>
                        <div>
                            <dt>关联房间</dt>
                            <dd>{{ selectedDetail?.note || "未设置" }}</dd>
                        </div>
                        <div>
                            <dt>关联设备</dt>
                            <dd class="link">{{ selected.devices }} 个设备</dd>
                        </div>
                        <div>
                            <dt>创建时间</dt>
                            <dd>{{ selectedDetail?.createdAt ? new Date(selectedDetail.createdAt).toLocaleString('zh-CN') : '--' }}</dd>
                        </div>
                        <div>
                            <dt>更新时间</dt>
                            <dd>{{ selectedDetail?.updatedAt ? new Date(selectedDetail.updatedAt).toLocaleString('zh-CN') : '--' }}</dd>
                        </div>
                    </dl>
                    <footer>
                        <button
                            class="primary"
                            :disabled="runningId === selected.id"
                            @click="controller.runRule(selected)"
                        >
                            ▶ {{ runningId === selected.id ? "执行中…" : "执行" }}</button
                        ><button @click="controller.openEditDialog(selected)">
                            <SvgIcon name="edit" size="sm" />编辑</button
                        ><button @click="controller.copyRule(selected)">
                            <SvgIcon name="layers" size="sm" />复制</button
                        ><button class="danger" @click="controller.removeRule(selected)">
                            <SvgIcon name="delete" size="sm" />删除
                        </button>
                    </footer>
                </template>
                <div v-else class="detail-empty">
                    <SvgIcon name="automation" size="lg" />
                    <p>选择规则后查看详情</p>
                </div>
            </section>
            <section class="panel">
                <h2>▣ 快捷操作</h2>
                <div class="quick">
                    <button
                        class="tone-blue"
                        @click="controller.openBatchDialog()"
                    >
                        <SvgIcon name="power" />批量启用<small
                            >启用多个规则</small
                        ></button
                    ><button
                        class="tone-purple"
                        @click="controller.openScheduleDialog()"
                    >
                        <SvgIcon name="clock" />定时设置<small
                            >统一定时管理</small
                        ></button
                    ><button class="tone-teal" @click="controller.runAction('sort')">
                        <SvgIcon name="layers" />排序管理<small
                            >自定义排序</small
                        ></button
                    ><button
                        class="tone-orange"
                        @click="controller.openLogsDialog()"
                    >
                        <SvgIcon name="log" />查看日志<small
                            >执行记录与日志</small
                        >
                    </button>
                </div>
            </section>
            <section class="panel templates">
                <header>
                    <h2>▣ 推荐模板</h2>
                    <a>更多 ›</a>
                </header>
                <p
                    v-for="item in [
                        [
                            'home',
                            '节能回家',
                            '节能模式 + 舒适回家流程',
                            'green',
                        ],
                        [
                            'security',
                            '夜间安防',
                            '夜间自动布防与照明联动',
                            'purple',
                        ],
                        [
                            'illumination',
                            '晨间唤醒',
                            '灯光、窗帘、空调联动唤醒',
                            'orange',
                        ],
                    ]"
                    :key="item[1]"
                >
                    <i :class="item[3]"><SvgIcon :name="item[0]" /></i
                    ><span
                        ><b>{{ item[1] }}</b
                        ><small>{{ item[2] }}</small></span
                    ><button type="button" @click="controller.useTemplate(item[1])">使用</button>
                </p>
                <a class="browse">浏览更多模板 ›</a>
            </section>
        </aside>
        <AutomationDialogs
            v-model="controller.activeDialog.value"
            :rule="selected ?? undefined"
            :rules="automations"
            :executions="executions"
            :selected-rule-name="selected?.name"
            @save="controller.saveRule"
            @batch="handleBatchEnable"
            @imported="controller.importRules"
            @scheduled="controller.scheduleRules"
        />

        <ConfirmActionDialog
            v-if="controller.deleteDialogOpen.value"
            :loading="controller.deleting.value"
            :model-value="controller.deleteDialogOpen.value"
            title="删除自动化"
            description="此操作将从规则列表中移除该自动化。"
            warning="删除后无法恢复，关联的触发条件、执行动作与执行日志也会一并清除。"
            @cancel="controller.cancelRemoveRule"
            @confirm="controller.confirmRemoveRule"
            @update:model-value="controller.deleteDialogOpen.value = $event"
        >
            <section
                v-if="controller.deletingRule.value"
                class="rule-delete-dialog-body"
            >
                <ConfirmEntitySummary
                    :description="controller.deletingRule.value.description"
                    :icon="controller.deletingRule.value.icon"
                    :title="controller.deletingRule.value.name"
                    :tone="controller.deletingRule.value.tone"
                />
            </section>
        </ConfirmActionDialog>
    </div>
</template>

<style scoped>
.page-shell {
    overflow: auto;
}
.automation {
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding: 20px;
}
.automation-page-header {
    display: grid;
    grid-template-columns: minmax(210px, auto) minmax(0, 1fr);
    gap: 18px;
    align-items: start;
}
.automation-page-title {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 12px;
}

.automation-page-title .page-header-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
}

.automation-page-title h1 {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 24px;
    font-weight: 900;
    line-height: 1.15;
}
.automation-page-title p {
    margin: 8px 0 0;
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 750;
}
@media (max-width: 1180px) {
    .automation-page-header {
        grid-template-columns: 1fr;
    }
}
.stats-fade-enter-active,
.stats-fade-leave-active {
    transition: opacity 250ms ease, transform 250ms ease;
}
.stats-fade-enter-from,
.stats-fade-leave-to {
    opacity: 0;
    transform: translateY(-8px);
}
.filters {
    display: flex;
    flex-wrap: nowrap;
    min-width: 0;
    align-items: center;
    gap: 8px;
}
.filters-search {
    display: flex;
    min-width: 90px;
    flex: 1 1 140px;
    height: 38px;
    align-items: center;
    gap: 8px;
    border: 1px solid var(--color-border);
    border-radius: 9px;
    background: var(--color-card-bg);
    padding: 0 12px;
    color: var(--color-text-tertiary);
    box-shadow: var(--shadow-card);
    transition:
        border-color 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease);
}
.filters-search:focus-within {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
}
.filters-search input {
    min-width: 0;
    flex: 1;
    border: 0;
    background: transparent;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    outline: none;
}
.filters select {
    width: auto;
    flex: 0 0 96px;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 9px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    padding: 0 9px;
    font-size: 12px;
    font-weight: 800;
    outline: none;
    box-shadow: var(--shadow-card);
}
.filters select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}
.filters button {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    gap: 7px;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 9px;
    background: var(--color-card-bg);
    padding: 0 13px;
    font-size: 13px;
    font-weight: 900;
    white-space: nowrap;
    box-shadow: var(--shadow-card);
    transition:
        transform 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}
.filters button:hover {
    transform: translateY(-1px);
}
.filters .primary,
.primary {
    border-color: var(--color-primary-600);
    background: var(--color-primary-600);
    color: #fff;
}
.stats {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
}
.cards header > i,
.detail-title > i,
.templates p > i {
    display: grid;
    width: 50px;
    height: 50px;
    flex: none;
    place-items: center;
    border-radius: 50%;
}
.blue {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.green {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}
.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.red {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.cards {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}
.cards.is-expanded {
    max-height: 380px;
    overflow-y: auto;
    scrollbar-gutter: stable;
}
.cards.is-expanded::-webkit-scrollbar {
    width: 6px;
}
.cards.is-expanded::-webkit-scrollbar-thumb {
    border-radius: 3px;
    background: var(--color-border);
}
.cards.is-expanded::-webkit-scrollbar-track {
    background: transparent;
}
.cards article {
    min-width: 0;
    border: 1px solid var(--color-border-default);
    border-radius: 13px;
    background: var(--color-card-bg);
    padding: 13px;
    cursor: pointer;
}
.cards article.selected {
    border: 1.5px solid var(--color-primary-600);
    box-shadow: 0 0 0 1px var(--color-primary-200);
}
.cards header {
    display: flex;
    gap: 11px;
}
.cards header > i {
    width: 44px;
    height: 44px;
}
.cards header span {
    display: grid;
    grid-template-columns: auto auto;
    min-width: 0;
    flex: 1;
    align-content: start;
    gap: 2px 7px;
}
.cards header b {
    overflow: hidden;
    font-size: 17px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.cards header em {
    width: max-content;
    border-radius: 5px;
    background: var(--color-success-soft);
    padding: 3px 8px;
    color: var(--color-success);
    font-size: 12px;
    font-style: normal;
}
.cards header small {
    grid-column: span 2;
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 13px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.devices {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 13px 0;
}
.devices i {
    display: grid;
    width: 30px;
    height: 30px;
    place-items: center;
    border-radius: 6px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.devices i.dev-curtain {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
}
.devices i.dev-temp {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.devices span {
    color: var(--color-text-tertiary);
    font-size: 13px;
}
.cards footer {
    display: flex;
    gap: 8px;
    border-top: 1px solid var(--color-border-subtle);
    padding-top: 10px;
}
.cards footer > button {
    height: 34px;
    border: 1px solid var(--color-border-default);
    border-radius: 6px;
    padding: 0 10px;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
}

/* 运行按钮：图标 + 文案横向对齐 */
.cards footer .run-rule-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

/* 复制规则后新副本卡片与名称一次性高亮 */
.cards article.is-copy-highlight,
.cards article.is-batch-changed {
    border-color: var(--color-primary-400);
    box-shadow: 0 0 0 3px var(--color-focus-ring);
    animation: copy-card-highlight 1600ms var(--motion-ease) 1 both;
}

.cards article .name-highlight {
    color: var(--color-primary-700);
    animation: copy-name-highlight 1600ms var(--motion-ease) 1 both;
}

@keyframes copy-card-highlight {
    0%, 100% { box-shadow: 0 0 0 0 transparent; border-color: var(--color-border-default); }
    20%, 70% { box-shadow: 0 0 0 3px var(--color-focus-ring); border-color: var(--color-primary-400); }
}

@keyframes copy-name-highlight {
    0%, 100% { color: var(--color-text-primary); }
    20%, 70% { color: var(--color-primary-700); }
}
.cards footer .card-delete {
    display: grid;
    width: 34px;
    flex: 0 0 34px;
    place-items: center;
    padding: 0;
    color: var(--color-text-tertiary);
}
.cards footer .card-delete:hover {
    border-color: var(--color-danger);
    background: var(--color-danger-soft);
    color: var(--color-danger);
}
.cards footer button:disabled {
    cursor: default;
    opacity: 0.55;
}
.cards footer button:disabled svg {
    animation: spin 900ms linear infinite;
}
.cards article.disabled {
    opacity: 0.7;
}
.cards .cards-empty {
    grid-column: 1 / -1;
    display: grid;
    min-height: 180px;
    place-items: center;
    border: 1px dashed var(--color-border);
    border-radius: 13px;
    color: var(--color-text-tertiary);
    font-weight: 800;
}
.cards-footer {
    display: flex;
    justify-content: center;
}
.cards-footer .automation-view-all {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    width: fit-content;
    border: none;
    background: none;
    padding: 4px 8px;
    border-radius: 6px;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
    cursor: pointer;
    transition: background-color 150ms;
}
.cards-footer .automation-view-all:hover {
    background: var(--color-primary-50);
}
.cards-footer .chevron-icon {
    display: inline-flex;
    transition: transform 300ms ease;
}
.cards-footer .chevron-icon.is-expanded {
    transform: rotate(180deg);
}
.switch {
    margin-left: auto;
}
.switch input {
    display: none;
}
.switch span {
    display: block;
    width: 40px;
    height: 23px;
    border-radius: 20px;
    background: var(--color-border-strong);
    padding: 2px;
}
.switch span:after {
    display: block;
    width: 19px;
    height: 19px;
    border-radius: 50%;
    background: #fff;
    content: "";
    transition: 0.2s;
}
.switch input:checked + span {
    background: var(--color-primary-600);
}
.switch input:checked + span:after {
    transform: translateX(17px);
}
.panel {
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px;
}
.panel h2 {
    font-size: 16px;
    font-weight: 900;
}
.panel header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.flow-heading {
    display: flex;
    align-items: center;
    gap: 10px;
}
.flow-heading > span:last-child {
    display: grid;
    gap: 2px;
}
.flow-heading small {
    color: var(--color-text-tertiary);
    font-size: 11px;
}
.flow-heading-icon {
    display: grid;
    width: 36px;
    height: 36px;
    place-items: center;
    border-radius: 11px;
    background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-700));
    color: white;
    box-shadow: 0 6px 16px var(--color-focus-ring);
}
.panel a,
.link {
    color: var(--color-primary-600) !important;
    font-size: 12px;
    font-weight: 800;
    cursor: pointer;
}
.flow-body {
    display: grid;
    grid-template-columns: 1fr 1fr;
    margin-top: 12px;
    gap: 0;
}

/* 切换规则时流程区交叉淡入：180–220ms */
.step-crossfade-leave-active {
    transition: opacity 140ms var(--motion-ease-in), transform 140ms var(--motion-ease-in);
}
.step-crossfade-enter-active {
    transition: opacity 220ms var(--motion-ease-out), transform 220ms var(--motion-ease-out);
}
.step-crossfade-leave-to {
    opacity: 0;
    transform: translateX(6px);
}
.step-crossfade-enter-from {
    opacity: 0;
    transform: translateX(-6px);
}
.steps {
    display: flex;
    align-items: center;
    min-width: 0;
    overflow-x: auto;
    padding: 12px 6px 16px;
    gap: 0;
    scrollbar-width: thin;
}
.steps > div {
    display: flex;
    min-width: 150px;
    flex: 1;
    align-items: center;
    gap: 0;
    transition: transform 180ms var(--motion-ease);
}
.steps > div.is-running {
    transform: translateY(-2px);
}
.steps > div.is-running .step-card i {
    background: var(--color-info-soft);
    color: var(--color-info);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-info) 20%, transparent);
}
.steps > div.is-running .step-card i svg {
    animation: spin 900ms linear infinite;
}
.steps > div.is-completed .step-card i {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.step-card {
    position: relative;
    display: flex;
    min-height: 156px;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-subtle);
    padding: 17px 10px 12px;
    border-radius: 12px;
    background: linear-gradient(180deg, var(--color-card-bg), var(--color-surface-subtle));
    box-shadow: 0 5px 14px color-mix(in srgb, var(--color-text-primary) 5%, transparent);
    transition: background-color 180ms;
    width: 100%;
}

.step-card:hover {
    border-color: var(--color-primary-200);
    box-shadow: 0 9px 20px color-mix(in srgb, var(--color-primary-600) 10%, transparent);
    transform: translateY(-2px);
}

.step-index {
    position: absolute;
    top: 8px;
    left: 10px;
    color: var(--color-text-muted);
    font-size: 10px;
    font-weight: 900;
    letter-spacing: 0.08em;
}

.step-card i {
    position: relative;
    display: grid;
    width: 44px;
    height: 44px;
    place-items: center;
    border-radius: 14px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    transition: box-shadow 180ms;
}
.step-card i.is-blue {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.step-card i.is-orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.step-card i.is-teal {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
}
.step-card i.is-purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}

.step-trigger-badge {
    position: absolute;
    top: -4px;
    right: -4px;
    padding: 2px 6px;
    border-radius: 4px;
    background: var(--color-primary-600);
    color: #fff;
    font-size: 9px;
    font-weight: 900;
    line-height: 1.4;
}

.step-card b {
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-primary);
}
.step-card small {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
}

.step-status {
    margin-top: auto;
    border-radius: 999px;
    background: var(--color-workspace-background);
    padding: 3px 8px;
    color: var(--color-text-tertiary);
    font-size: 10px;
    font-weight: 800;
}
.steps > div.is-running .step-status {
    background: var(--color-info-soft);
    color: var(--color-info);
}
.steps > div.is-completed .step-status {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.step-connector {
    flex-shrink: 0;
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    margin: 0 -2px;
    border: 1px solid var(--color-primary-100);
    border-radius: 50%;
    background: var(--color-card-bg);
    color: var(--color-primary-500);
    box-shadow: var(--shadow-card);
    z-index: 1;
}

.flow-empty {
    display: flex;
    min-height: 172px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border: 1px dashed var(--color-border-default);
    border-radius: 13px;
    color: var(--color-text-tertiary);
    text-align: center;
}
.flow-empty > span {
    display: grid;
    width: 42px;
    height: 42px;
    place-items: center;
    border-radius: 13px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.flow-empty strong { color: var(--color-text-secondary); font-size: 13px; }
.flow-empty small { font-size: 11px; }

.records {
    border-left: 1px solid var(--color-border-subtle);
    padding-left: 16px;
}
.records h3 {
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-primary);
    margin: 0 0 10px;
}

.records-growth {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 12px;
    padding: 10px 12px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 10px;
    background: var(--color-card-bg);
}

.growth-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}

.growth-item em {
    color: var(--color-text-tertiary);
    font-size: 10px;
    font-weight: 600;
    font-style: normal;
}

.growth-item strong {
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 900;
    line-height: 1.2;
}

.growth-item small {
    font-size: 10px;
    font-weight: 800;
}

.growth-up {
    color: var(--color-success);
}

.growth-neutral {
    color: var(--color-text-muted);
}

.records-list {
    display: flex;
    flex-direction: column;
}

.record-row {
    display: grid;
    grid-template-columns: 82px 1fr 60px 34px;
    gap: 6px;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid var(--color-border-subtle);
    font-size: 12px;
    transition: background-color 150ms;
}

.record-row:last-child {
    border-bottom: 0;
}

.record-row:hover {
    background: var(--color-surface-subtle);
    margin: 0 -4px;
    padding: 7px 4px;
    border-radius: 6px;
}

.record-row time {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
}

.record-name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-weight: 700;
    font-size: 13px;
}

.record-result {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 12px;
    font-weight: 800;
}

.record-result.is-success {
    color: var(--color-success);
}

.record-result > svg {
    width: 12px;
    height: 12px;
}

.record-duration {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 600;
    font-style: normal;
    text-align: right;
}

.records-empty {
    padding: 16px 0;
    color: var(--color-text-tertiary);
    text-align: center;
    font-size: 12px;
}
.right {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px;
}
.detail-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 15px 0;
}
.detail-title span {
    display: grid;
    grid-template-columns: auto auto;
    min-width: 0;
}
.detail-title h3 {
    font-size: 20px;
}
.detail-title em {
    width: max-content;
    margin-left: 8px;
    border-radius: 5px;
    background: var(--color-success-soft);
    padding: 2px 6px;
    color: var(--color-success);
    font-size: 12px;
    font-style: normal;
}
.detail-title p {
    grid-column: span 2;
    color: var(--color-text-tertiary);
    font-size: 13px;
}
.detail dl div {
    display: grid;
    grid-template-columns: 82px 1fr;
    padding: 7px 0;
    font-size: 13px;
}
.detail dt {
    color: var(--color-text-tertiary);
}
.detail dd {
    color: var(--color-text-secondary);
}
.detail footer {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
    margin-top: 14px;
}
.detail footer button {
    height: 40px;
    border: 1px solid var(--color-border-default);
    border-radius: 7px;
    font-size: 13px;
    font-weight: 900;
}
.detail footer .danger {
    border-color: var(--color-danger);
    color: var(--color-danger);
}
.detail footer .danger:hover {
    background: var(--color-danger-soft);
}
.detail-empty {
    display: flex;
    min-height: 200px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: var(--color-text-tertiary);
    text-align: center;
}
.detail-empty svg {
    width: 40px;
    height: 40px;
    color: var(--color-primary-300);
}
.detail-empty p {
    margin: 0;
    font-size: 14px;
    font-weight: 700;
}
.quick {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 12px;
}
.quick button {
    display: grid;
    min-height: 62px;
    grid-template-columns: 28px 1fr;
    align-items: center;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    padding: 10px;
    text-align: left;
    font-size: 13px;
    font-weight: 900;
}
.quick svg {
    grid-row: span 2;
    color: var(--color-primary-600);
}
.quick button.tone-blue svg {
    color: var(--color-primary-600);
}
.quick button.tone-purple svg {
    color: var(--tone-purple);
}
.quick button.tone-teal svg {
    color: var(--tone-teal);
}
.quick button.tone-orange svg {
    color: var(--tone-orange);
}
.quick small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 500;
}
.templates p {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
}
.templates p > i {
    width: 34px;
    height: 34px;
}
.templates p span {
    display: flex;
    min-width: 0;
    flex: 1;
    flex-direction: column;
    font-size: 13px;
}
.templates p small {
    overflow: hidden;
    color: var(--color-text-tertiary);
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.templates p button {
    border: 1px solid var(--color-border-default);
    border-radius: 6px;
    padding: 5px 10px;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
}
.browse {
    display: block;
    margin-top: 12px;
    text-align: center;
}

/* === 删除确认弹窗 === */
.dialog-header .dialog-icon svg {
    animation: icon-pulse 1.6s ease-in-out infinite;
}

.rule-delete-dialog-body {
    display: grid;
    gap: 14px;
}

.rule-delete-summary {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 16px 18px;
    border: 1px solid var(--color-primary-200);
    border-radius: 16px;
    background: linear-gradient(
        135deg,
        var(--color-card-bg),
        var(--color-primary-50)
    );
    box-shadow: var(--shadow-card);
}

.rule-delete-thumb {
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    border-radius: 50%;
    box-shadow: 0 6px 16px var(--color-focus-ring);
}

.rule-delete-summary-info {
    min-width: 0;
    flex: 1;
}

.rule-delete-summary-info strong {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 800;
}

.rule-delete-summary-info p {
    margin: 4px 0 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--color-text-secondary);
    font-size: 13px;
}

.rule-delete-warning {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    margin: 0;
    border-radius: 12px;
    background: color-mix(
        in srgb,
        var(--color-danger-soft) 62%,
        transparent
    );
    padding: 12px 16px;
    color: var(--color-danger);
    font-size: 14px;
    font-weight: 700;
    line-height: 1.5;
}

.rule-delete-warning svg {
    flex: 0 0 auto;
    margin-top: 2px;
    opacity: 0.85;
}

.rule-delete-cancel-button,
.rule-delete-confirm-button {
    min-width: 96px;
    height: 38px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 900;
    transition:
        transform 140ms var(--motion-ease),
        box-shadow 140ms var(--motion-ease),
        border-color 140ms,
        background-color 140ms;
}

.rule-delete-cancel-button {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.rule-delete-confirm-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border: 1px solid var(--color-danger);
    background: linear-gradient(
        180deg,
        color-mix(in srgb, var(--color-danger) 92%, #fff),
        var(--color-danger)
    );
    color: var(--color-text-on-primary);
    box-shadow: 0 4px 12px var(--color-danger-border);
}

.rule-delete-cancel-button:hover {
    border-color: var(--color-text-secondary);
    color: var(--color-text-primary);
}

.rule-delete-confirm-button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px var(--color-danger-border);
}

.rule-delete-cancel-button:active,
.rule-delete-confirm-button:active {
    transform: translateY(0);
}

.rule-delete-confirm-button:disabled svg {
    animation: spin 900ms linear infinite;
}

@media (prefers-reduced-motion: reduce) {
    .dialog-header .dialog-icon svg,
    .rule-delete-confirm-button:disabled svg,
    .cards footer button:disabled svg,
    .steps > div.is-running i svg {
        animation: none;
    }

    .cards-footer .chevron-icon {
        transition: none;
    }
}
@media (max-width: 1200px) {
    .stats {
        grid-template-columns: repeat(2, 1fr);
    }
    .cards {
        grid-template-columns: repeat(2, 1fr);
    }
    .flow-body {
        grid-template-columns: 1fr;
    }
    .records {
        border: 0;
        border-top: 1px solid var(--color-border-subtle);
        padding: 10px 0 0;
    }
}
</style>
