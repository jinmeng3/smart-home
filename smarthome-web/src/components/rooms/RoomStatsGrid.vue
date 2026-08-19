<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    roomCount: number;
    onlineCount: number;
    comfortScore: number;
    roomCountChange: number;
    onlineRate: number;
    alertCount: number;
    pendingAlertCount: number;
}>();
</script>

<template>
    <section class="stats-grid">
        <article>
            <i class="tone-chip is-blue"><SvgIcon name="home" /></i>
            <span
                >房间数量<strong>{{ roomCount }} <small>个</small></strong
                ><em>{{ roomCountChange >= 0 ? `较上月 ↑ ${roomCountChange}` : `较上月 ↓ ${Math.abs(roomCountChange)}` }}</em></span
            >
        </article>
        <article>
            <i class="tone-chip is-green"><SvgIcon name="online-device" /></i>
            <span
                >在线设备<strong>{{ onlineCount }} <small>个</small></strong
                ><em>在线率 {{ onlineRate }}%</em></span
            >
        </article>
        <article>
            <i :class="['tone-chip', alertCount > 0 ? 'is-orange' : 'is-neutral']"><SvgIcon name="notification" /></i>
            <span
                >当前告警<strong :class="alertCount > 0 ? '' : 'tone-muted'">{{ alertCount }} <small>条</small></strong
                ><em>{{ pendingAlertCount > 0 ? '待处理告警' : '无待处理告警' }}</em></span
            >
        </article>
        <article>
            <i class="tone-chip is-purple"><SvgIcon name="comfort" /></i>
            <span
                >平均舒适度<strong>{{ comfortScore }} <small>分</small></strong
                ><em>舒适度良好</em></span
            >
        </article>
    </section>
</template>

<style scoped>
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
}
.stats-grid article {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 10px 12px;
    box-shadow: var(--shadow-card);
}
.stats-grid i {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border-radius: 10px;
    font-style: normal;
}
.stats-grid span {
    min-width: 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}
.stats-grid strong {
    display: block;
    margin-top: 1px;
    color: var(--color-text-primary);
    font-size: 19px;
    font-weight: 900;
    letter-spacing: -0.01em;
}
.stats-grid strong small {
    font-size: 13px;
    font-weight: 700;
}
.stats-grid em {
    display: block;
    margin-top: 1px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-style: normal;
}
@media (max-width: 1450px) {
    .stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

.tone-chip.is-neutral {
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.stats-grid strong.tone-muted {
    color: var(--color-text-secondary);
}
</style>
