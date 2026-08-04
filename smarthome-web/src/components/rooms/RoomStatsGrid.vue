<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    roomCount: number;
    onlineCount: number;
    comfortScore: number;
}>();
</script>

<template>
    <section class="stats-grid">
        <article>
            <i class="blue"><SvgIcon name="home" /></i>
            <span
                >房间数量<strong>{{ roomCount }} <small>个</small></strong
                ><em>较上月 ↑ 2</em></span
            >
        </article>
        <article>
            <i class="green"><SvgIcon name="online-device" /></i>
            <span
                >在线设备<strong>{{ onlineCount }} <small>个</small></strong
                ><em>在线率 86.4%</em></span
            >
        </article>
        <article>
            <i class="orange"><SvgIcon name="notification" /></i>
            <span
                >当前告警<strong>2 <small>条</small></strong
                ><em>待处理告警</em></span
            >
        </article>
        <article>
            <i class="purple"><SvgIcon name="comfort" /></i>
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
    gap: 12px;
}
.stats-grid article {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 12px;
    border: 1px solid var(--color-border);
    border-radius: 13px;
    background: var(--color-card-bg);
    padding: 14px;
    box-shadow: var(--shadow-card);
}
.stats-grid i {
    display: grid;
    width: 42px;
    height: 42px;
    flex: 0 0 42px;
    place-items: center;
    border-radius: 11px;
    font-style: normal;
}
.stats-grid i.blue {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.stats-grid i.green {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.stats-grid i.orange {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}
.stats-grid i.purple {
    background: #f3e8ff;
    color: #8b5cf6;
}
.stats-grid span {
    min-width: 0;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 750;
}
.stats-grid strong {
    display: block;
    margin-top: 3px;
    color: var(--color-text-primary);
    font-size: 20px;
}
.stats-grid strong small {
    font-size: 11px;
}
.stats-grid em {
    display: block;
    margin-top: 2px;
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-style: normal;
}
@media (max-width: 1450px) {
    .stats-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
</style>
