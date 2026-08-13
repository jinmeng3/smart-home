<script setup lang="ts">
import { computed, ref } from "vue";
import { useHomeStore } from "../../stores/home";
import BaseSwitch from "../BaseSwitch.vue";
import SvgIcon from "../common/SvgIcon.vue";
import { defineAsyncDialog, preloadDialog } from "../../utils/asyncDialog";

const loadScheduleDialog = () => import("../overview/dialogs/ScheduleDialog.vue");
const ScheduleDialog = defineAsyncDialog(loadScheduleDialog);

const store = useHomeStore();
const dialogVisible = ref(false);

const todayLabel = computed(() => {
    const now = new Date();
    const weekdays = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];
    return `${now.getMonth() + 1}月${now.getDate()}日 ${weekdays[now.getDay()]}`;
});

const automationTone = (id: string): string => {
    const map: Record<string, string> = {
        "wake-up": "orange",
        "arrive-home": "blue",
        sleep: "purple",
    };

    return map[id] ?? "teal";
};
</script>

<template>
    <section
        class="motion-card page-enter-stagger shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] px-3 py-2 shadow-soft"
        style="animation-delay: 180ms"
    >
        <!-- 标题行：标题 + 更多（同一行，标题占视觉重点） -->
        <header class="schedule-header">
            <h2 class="schedule-title">
                <span class="tone-chip is-orange">
                    <SvgIcon name="calendar" size="sm" />
                </span>
                家庭日程
            </h2>
            <button
                class="more-button"
                type="button"
                @focus="preloadDialog(loadScheduleDialog)"
                @mouseenter="preloadDialog(loadScheduleDialog)"
                @click="dialogVisible = true"
            >
                更多
                <SvgIcon name="chevron-right" size="sm" />
            </button>
        </header>

        <!-- 日期行：紧凑，左右切换按钮缩小 -->
        <div class="date-nav">
            <button class="date-arrow" type="button" aria-label="上一个日期">
                <SvgIcon name="chevron-left" size="sm" />
            </button>
            <div class="date-info">
                <span>{{ todayLabel }}</span>
                <span class="today-badge"><i></i>今天</span>
            </div>
            <button class="date-arrow" type="button" aria-label="下一个日期">
                <SvgIcon name="chevron-right" size="sm" />
            </button>
        </div>

        <!-- 计划列表 / 空状态 -->
        <div v-if="store.automations.length" class="schedule-list">
            <article
                v-for="automation in store.automations"
                :key="automation.id"
                :class="`is-${automationTone(automation.id)}`"
            >
                <time class="schedule-time">{{ automation.time }}</time>
                <span class="timeline-node" aria-hidden="true"></span>
                <div class="schedule-body">
                    <strong>{{ automation.name }}</strong>
                </div>
                <BaseSwitch v-model="automation.enabled" small />
            </article>
        </div>
        <p v-else class="schedule-empty">
            今天暂无计划
            <span v-if="store.enabledAutomationCount" class="schedule-empty-meta"
                >已开启 {{ store.enabledAutomationCount }} 个</span
            >
        </p>
    </section>

    <ScheduleDialog v-if="dialogVisible" v-model="dialogVisible" />
</template>

<style scoped>
.schedule-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 5px;
}

.schedule-title {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 15px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.schedule-title .tone-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    flex: none;
    border-radius: 8px;
}

.more-button {
    display: inline-flex;
    flex: none;
    align-items: center;
    gap: 2px;
    border: none;
    border-radius: 8px;
    background: none;
    padding: 4px 6px;
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 800;
    transition: background-color 160ms var(--motion-ease);
}

.more-button:hover {
    background: var(--color-primary-50);
}

/* 日期行：无独立大框，仅留白分隔 */
.date-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    padding: 1px 0 4px;
}

.date-arrow {
    display: grid;
    width: 22px;
    height: 22px;
    place-items: center;
    border: none;
    border-radius: 6px;
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    transition:
        background-color 160ms var(--motion-ease),
        color 160ms var(--motion-ease);
}

.date-arrow:hover {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.date-info {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 6px;
    overflow: hidden;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
    white-space: nowrap;
    text-overflow: ellipsis;
}

.today-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex: none;
    border-radius: 999px;
    background: var(--tone-success-soft);
    padding: 1px 7px;
    color: var(--tone-success);
    font-size: 10px;
    font-weight: 800;
}

.today-badge i {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
}

/* 计划列表：紧凑，无独立边框 */
.schedule-list {
    display: grid;
    border-top: 1px solid var(--color-border-subtle);
    padding-top: 4px;
}

.schedule-list article {
    display: grid;
    grid-template-columns: 44px 16px minmax(0, 1fr) auto;
    align-items: center;
    gap: 6px;
    padding: 6px 0;
}

.schedule-time {
    font-size: 12px;
    font-weight: 900;
    text-align: center;
    color: var(--color-text-secondary);
}

.timeline-node {
    width: 8px;
    height: 8px;
    justify-self: center;
    border-radius: 50%;
    background: var(--tone-primary);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 5px var(--tone-primary-soft);
}

.schedule-body {
    min-width: 0;
}

.schedule-body strong {
    display: block;
    overflow: hidden;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.schedule-list article.is-orange .schedule-time {
    color: var(--tone-orange);
}
.schedule-list article.is-orange .timeline-node {
    background: var(--tone-orange);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 5px var(--tone-orange-soft);
}
.schedule-list article.is-blue .schedule-time {
    color: var(--tone-info);
}
.schedule-list article.is-blue .timeline-node {
    background: var(--tone-info);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 5px var(--tone-info-soft);
}
.schedule-list article.is-purple .schedule-time {
    color: var(--tone-purple);
}
.schedule-list article.is-purple .timeline-node {
    background: var(--tone-purple);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 5px var(--tone-purple-soft);
}
.schedule-list article.is-teal .schedule-time {
    color: var(--tone-teal);
}
.schedule-list article.is-teal .timeline-node {
    background: var(--tone-teal);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 5px var(--tone-teal-soft);
}

/* 空状态 */
.schedule-empty {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0;
    border-top: 1px solid var(--color-border-subtle);
    padding-top: 6px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 800;
}

.schedule-empty-meta {
    color: var(--color-primary-600);
    font-size: 12px;
    font-weight: 800;
}
</style>
