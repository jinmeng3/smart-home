<script setup lang="ts">
import { computed, ref } from "vue";
import { useHomeStore } from "../../stores/home";
import BaseSwitch from "../BaseSwitch.vue";
import ScheduleDialog from "../overview/dialogs/ScheduleDialog.vue";
import SvgIcon from "../common/SvgIcon.vue";

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
        class="motion-card page-enter-stagger shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-card-bg)] p-3 shadow-soft"
        style="animation-delay: 180ms"
    >
        <header class="schedule-header">
            <h2 class="schedule-title">
                <span class="tone-chip is-orange">
                    <SvgIcon name="calendar" size="sm" />
                </span>
                家庭日程
                <small>/ 自动化计划</small>
            </h2>
            <button
                class="more-button"
                type="button"
                @click="dialogVisible = true"
            >
                更多
                <SvgIcon name="chevron-right" size="sm" />
            </button>
        </header>

        <div class="date-nav">
            <button class="date-arrow" type="button" aria-label="上一个日期">
                <SvgIcon name="chevron-left" size="sm" />
            </button>
            <div class="date-info">
                <strong>{{ todayLabel }}</strong>
                <span class="today-badge"><i></i>今天</span>
            </div>
            <button class="date-arrow" type="button" aria-label="下一个日期">
                <SvgIcon name="chevron-right" size="sm" />
            </button>
        </div>

        <div class="schedule-list">
            <article
                v-for="automation in store.automations"
                :key="automation.id"
                :class="`is-${automationTone(automation.id)}`"
            >
                <time class="schedule-time">{{ automation.time }}</time>
                <span class="timeline-node" aria-hidden="true"></span>
                <div class="schedule-body">
                    <strong>{{ automation.name }}</strong>
                    <p>{{ automation.description }}</p>
                </div>
                <BaseSwitch v-model="automation.enabled" small />
            </article>
        </div>

        <footer class="schedule-footer">
            <span>今日计划 <b>{{ store.automations.length }}</b> 个</span>
            <span>已开启 <b>{{ store.enabledAutomationCount }}</b> 个</span>
        </footer>

        <ScheduleDialog v-model="dialogVisible" />
    </section>
</template>

<style scoped>
.schedule-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 12px;
}

.schedule-title {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 14px;
    font-weight: 800;
    color: var(--color-text-primary);
}

.schedule-title small {
    overflow: hidden;
    font-size: 12px;
    font-weight: 700;
    color: var(--color-text-tertiary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.schedule-title .tone-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    flex: none;
    border-radius: 9px;
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

.date-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 6px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-panel-secondary);
    padding: 6px;
}

.date-arrow {
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border: none;
    border-radius: 8px;
    background: var(--color-panel-background);
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
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.today-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    background: var(--tone-success-soft);
    padding: 2px 8px;
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

.schedule-list {
    position: relative;
    display: grid;
    margin-top: 2px;
}

.schedule-list::before {
    content: "";
    position: absolute;
    top: 8px;
    bottom: 8px;
    left: calc(52px + 8px + 10px);
    width: 2px;
    transform: translateX(-50%);
    background: var(--color-border-strong);
}

.schedule-list article {
    display: grid;
    grid-template-columns: 52px 20px minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
    padding: 9px 0;
}

.schedule-time {
    font-size: 13px;
    font-weight: 900;
    text-align: center;
    color: var(--color-text-secondary);
}

.timeline-node {
    position: relative;
    z-index: 1;
    justify-self: center;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--tone-primary);
    box-shadow:
        0 0 0 3px var(--color-card-bg),
        0 0 0 6px var(--tone-primary-soft);
}

.schedule-body {
    min-width: 0;
}

.schedule-body strong {
    display: block;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-primary);
}

.schedule-body p {
    overflow: hidden;
    margin: 2px 0 0;
    font-size: 11px;
    line-height: 1.5;
    color: var(--color-text-tertiary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.schedule-list article.is-orange .schedule-time {
    color: var(--tone-orange);
}
.schedule-list article.is-orange .timeline-node {
    background: var(--tone-orange);
    box-shadow:
        0 0 0 3px var(--color-card-bg),
        0 0 0 6px var(--tone-orange-soft);
}
.schedule-list article.is-blue .schedule-time {
    color: var(--tone-info);
}
.schedule-list article.is-blue .timeline-node {
    background: var(--tone-info);
    box-shadow:
        0 0 0 3px var(--color-card-bg),
        0 0 0 6px var(--tone-info-soft);
}
.schedule-list article.is-purple .schedule-time {
    color: var(--tone-purple);
}
.schedule-list article.is-purple .timeline-node {
    background: var(--tone-purple);
    box-shadow:
        0 0 0 3px var(--color-card-bg),
        0 0 0 6px var(--tone-purple-soft);
}
.schedule-list article.is-teal .schedule-time {
    color: var(--tone-teal);
}
.schedule-list article.is-teal .timeline-node {
    background: var(--tone-teal);
    box-shadow:
        0 0 0 3px var(--color-card-bg),
        0 0 0 6px var(--tone-teal-soft);
}

.schedule-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 6px;
    border-top: 1px dashed var(--color-border-default);
    padding-top: 9px;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.schedule-footer b {
    color: var(--color-primary-600);
    font-size: 13px;
}
</style>
