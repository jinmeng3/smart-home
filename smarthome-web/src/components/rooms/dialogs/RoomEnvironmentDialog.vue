<script setup lang="ts">
import { ref } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import type { Room } from "../../../types/room";

const props = defineProps<{
    modelValue: boolean;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: boolean];
}>();

const trendRange = ref("今日");

const title = "房间环境详情";
const description = `查看${props.room?.name ?? "房间"}的实时环境指标、趋势变化与舒适度分析`;

const close = () => emit("update:modelValue", false);
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="title"
        :description="description"
        confirm-text="导出报告"
        width="large"
        @cancel="close"
        @update:model-value="close"
    >
        <div class="environment-dialog">
            <div class="environment-summary">
                <article>
                    <strong>{{ room?.name }}</strong
                    ><small>● 在线　当前房间</small>
                </article>
                <article>
                    <span>舒适度</span
                    ><strong
                        >{{ room?.comfort ?? 83 }} <small>分</small></strong
                    >
                </article>
                <article>
                    <span>环境状态</span><strong>良好</strong
                    ><small>各项指标在舒适范围内</small>
                </article>
            </div>
            <div class="metric-grid">
                <article
                    v-for="item in [
                        {
                            n: '温度',
                            v: `${room?.temperature}°C`,
                            r: '20.0 ~ 26.0°C',
                            c: '#3b82f6',
                        },
                        {
                            n: '湿度',
                            v: `${room?.humidity}%`,
                            r: '40% ~ 60%',
                            c: '#60a5fa',
                        },
                        {
                            n: 'PM2.5',
                            v: `${room?.pm25} μg/m³`,
                            r: '0 ~ 35 μg/m³',
                            c: '#22c55e',
                        },
                        {
                            n: '光照',
                            v: `${room?.illuminance} lux`,
                            r: '100 ~ 500 lux',
                            c: '#f59e0b',
                        },
                        {
                            n: '噪音',
                            v: `${room?.noise} dB`,
                            r: '30 ~ 60 dB',
                            c: '#8b5cf6',
                        },
                    ]"
                    :key="item.n"
                >
                    <small>{{ item.n }}</small
                    ><strong>{{ item.v }}</strong
                    ><svg viewBox="0 0 100 24" :style="{ stroke: item.c }">
                        <polyline
                            points="0,17 15,11 28,15 42,7 58,15 72,5 86,13 100,8"
                        /></svg
                    ><span>{{ item.r }}</span>
                </article>
            </div>
            <section class="trend-card">
                <header>
                    <h3>环境趋势</h3>
                    <div>
                        <button
                            v-for="range in ['今日', '近 7 天', '近 30 天']"
                            :key="range"
                            :class="{ active: trendRange === range }"
                            type="button"
                            @click="trendRange = range"
                        >
                            {{ range }}
                        </button>
                    </div>
                </header>
                <svg
                    class="trend-chart"
                    viewBox="0 0 760 180"
                    preserveAspectRatio="none"
                >
                    <g>
                        <line
                            v-for="y in [25, 65, 105, 145]"
                            :key="y"
                            x1="20"
                            :y1="y"
                            x2="740"
                            :y2="y"
                        />
                    </g>
                    <polyline
                        class="temperature"
                        points="20,90 100,75 180,72 260,78 340,66 420,57 500,61 580,59 660,78 740,74"
                    />
                    <polyline
                        class="humidity"
                        points="20,125 100,116 180,119 260,116 340,127 420,122 500,120 580,111 660,116 740,119"
                    />
                </svg>
            </section>
            <div class="suggestions">
                <article>
                    <SvgIcon name="air-quality" /><span
                        ><b>开启新风</b
                        ><small>PM2.5 良好，建议定期开启新风</small></span
                    >
                </article>
                <article>
                    <SvgIcon name="automation" /><span
                        ><b>适当通风</b
                        ><small>湿度适中，建议每日通风</small></span
                    >
                </article>
                <article>
                    <SvgIcon name="scene" /><span
                        ><b>夜间降低噪音</b
                        ><small>建议降低电视音量</small></span
                    >
                </article>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.environment-summary {
    display: grid;
    grid-template-columns: 1.2fr 0.8fr 1fr;
    gap: 10px;
}
.environment-summary article {
    display: flex;
    min-height: 72px;
    justify-content: center;
    flex-direction: column;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 12px;
}
.environment-summary article:first-child strong {
    font-size: 18px;
}
.environment-summary small {
    color: var(--color-text-tertiary);
}
.metric-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 9px;
    margin: 12px 0;
}
.metric-grid article {
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 11px;
}
.metric-grid article > * {
    display: block;
}
.metric-grid strong {
    margin: 6px 0;
    font-size: 18px;
}
.metric-grid svg {
    width: 100%;
    height: 25px;
    fill: none;
    stroke-width: 2;
}
.metric-grid span,
.metric-grid small {
    color: var(--color-text-tertiary);
    font-size: 9px;
}
.trend-card {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 13px;
}
.trend-card header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.trend-card header div {
    display: flex;
    gap: 5px;
}
.trend-card button {
    min-width: 30px;
    height: 30px;
    border: 1px solid var(--color-border);
    border-radius: 7px;
    background: var(--color-card-bg);
}
.trend-card button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.trend-chart {
    width: 100%;
    height: 185px;
}
.trend-chart g {
    stroke: var(--color-border-subtle);
}
.trend-chart polyline {
    fill: none;
    stroke-width: 3;
}
.trend-chart .temperature {
    stroke: var(--color-primary-600);
}
.trend-chart .humidity {
    stroke: #60a5fa;
}
.suggestions {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 9px;
    margin-top: 12px;
}
.suggestions article {
    display: flex;
    gap: 9px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    padding: 11px;
    color: var(--color-primary-600);
}
.suggestions span,
.suggestions small {
    display: block;
}
.suggestions b {
    color: var(--color-text-primary);
}
.suggestions small {
    margin-top: 4px;
    color: var(--color-text-tertiary);
}
@media (max-width: 760px) {
    .metric-grid,
    .suggestions {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
