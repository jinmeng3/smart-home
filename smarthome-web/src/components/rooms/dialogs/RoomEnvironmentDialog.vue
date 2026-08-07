<script setup lang="ts">
import { computed, ref, watch } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { getRoomEnvironmentLatest } from "../../../api/room";
import type { Room, RoomEnvironmentLatest } from "../../../types/room";
import { useLatestRequest } from "../../../composables/useLatestRequest";

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

// ── 环境指标获取 ──────────────────────────────────────────────────────────────────

const env = ref<RoomEnvironmentLatest>();
const { run } = useLatestRequest();
watch(
    () => props.room?.id,
    (id) => {
        env.value = undefined;
        if (id) {
            void run(
                () => getRoomEnvironmentLatest(id),
                (result) => {
                    env.value = result;
                },
                () => {
                    env.value = undefined;
                },
            );
        }
    },
    { immediate: true },
);

const metricValue = (name: string, fallback: number): number =>
    env.value?.values?.[name] ?? fallback;

// ── 舒适度等级 ──────────────────────────────────────────────────────────────────

const comfortLevel = computed(() => {
    const c = props.room?.comfort ?? 83;
    if (c >= 85) return { label: "优秀", color: "var(--color-success)", tone: "success" };
    if (c >= 70) return { label: "良好", color: "var(--tone-teal)", tone: "teal" };
    if (c >= 50) return { label: "一般", color: "var(--color-warning)", tone: "warning" };
    return { label: "较差", color: "var(--color-danger)", tone: "danger" };
});

const comfortPercent = computed(() => props.room?.comfort ?? 83);

// ── 环境指标配置 ─────────────────────────────────────────────────────────────────

interface MetricItem {
    n: string;
    v: string;
    raw: number;
    unit: string;
    range: [number, number];
    ideal: [number, number];
    color: string;
    tone: string;
    icon: string;
    trend: number[];
}

const metrics = computed<MetricItem[]>(() => [
    {
        n: "温度",
        v: `${metricValue("temperature", 0)}°C`,
        raw: metricValue("temperature", 24),
        unit: "°C",
        range: [10, 40],
        ideal: [20, 26],
        color: "#3b82f6",
        tone: "primary",
        icon: "temperature",
        trend: [24, 23, 23.5, 24.5, 25, 24, 23.8],
    },
    {
        n: "湿度",
        v: `${metricValue("humidity", 0)}%`,
        raw: metricValue("humidity", 55),
        unit: "%",
        range: [0, 100],
        ideal: [40, 60],
        color: "#0ea5e9",
        tone: "info",
        icon: "humidity",
        trend: [58, 56, 55, 54, 55, 57, 56],
    },
    {
        n: "PM2.5",
        v: `${metricValue("pm25", 0)} μg/m³`,
        raw: metricValue("pm25", 12),
        unit: "μg/m³",
        range: [0, 150],
        ideal: [0, 35],
        color: "#22c55e",
        tone: "success",
        icon: "air-quality",
        trend: [15, 13, 10, 12, 14, 11, 9],
    },
    {
        n: "光照",
        v: `${metricValue("illuminance", 0)} lux`,
        raw: metricValue("illuminance", 350),
        unit: "lux",
        range: [0, 1000],
        ideal: [100, 500],
        color: "#f59e0b",
        tone: "warning",
        icon: "illumination",
        trend: [320, 280, 300, 350, 380, 360, 340],
    },
    {
        n: "噪音",
        v: `${metricValue("noise", 0)} dB`,
        raw: metricValue("noise", 35),
        unit: "dB",
        range: [0, 120],
        ideal: [30, 60],
        color: "#8b5cf6",
        tone: "purple",
        icon: "noise",
        trend: [38, 35, 32, 33, 36, 34, 31],
    },
]);

const getStatus = (item: MetricItem) => {
    const v = item.raw;
    const [lo, hi] = item.ideal;
    if (v >= lo && v <= hi) return { label: "正常", color: "var(--color-success)" };
    if (v >= lo - 5 && v <= hi + 5) return { label: "临界", color: "var(--color-warning)" };
    return { label: "异常", color: "var(--color-danger)" };
};

const getPercent = (item: MetricItem) => {
    const [rMin, rMax] = item.range;
    const clamped = Math.max(rMin, Math.min(rMax, item.raw));
    return ((clamped - rMin) / (rMax - rMin)) * 100;
};

const getIdealFill = (item: MetricItem) => {
    const [rMin, rMax] = item.range;
    const [iLo, iHi] = item.ideal;
    const left = ((iLo - rMin) / (rMax - rMin)) * 100;
    const width = ((iHi - iLo) / (rMax - rMin)) * 100;
    return { left: `${left}%`, width: `${width}%` };
};

// ── 时间格式化 ──────────────────────────────────────────────────────────────────

const trendPoints = computed(() => {
    const base = metricValue("temperature", 24);
    const variation = 2;
    return Array.from({ length: 10 }, (_, i) => ({
        temp: base + Math.sin(i * 0.8) * variation + (i % 3 - 1) * 0.3,
        hum: metricValue("humidity", 55) + Math.cos(i * 0.6) * 3 + (i % 2) * 0.5,
    }));
});
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
            <!-- ─── 顶部概览 ─── -->
            <div class="overview-grid">
                <div class="overview-room">
                    <div class="room-badge">
                        <SvgIcon name="room" size="sm" />
                    </div>
                    <div class="room-info">
                        <strong>{{ room?.name }}</strong>
                        <span class="room-status">
                            <span class="status-dot" />
                            在线 · 当前房间
                        </span>
                    </div>
                </div>
                <div class="overview-comfort">
                    <div class="comfort-ring-wrap">
                        <svg class="comfort-ring" viewBox="0 0 40 40">
                            <circle
                                class="ring-bg"
                                cx="20"
                                cy="20"
                                r="17"
                                fill="none"
                                stroke-width="3"
                            />
                            <circle
                                class="ring-fill"
                                cx="20"
                                cy="20"
                                r="17"
                                fill="none"
                                stroke-width="3"
                                :stroke-dasharray="106.8"
                                :stroke-dashoffset="106.8 * (1 - comfortPercent / 100)"
                                :stroke="comfortLevel.color"
                            />
                        </svg>
                        <div class="comfort-value">
                            <strong>{{ room?.comfort ?? 83 }}</strong>
                            <small>分</small>
                        </div>
                    </div>
                    <div class="comfort-label">
                        <span class="comfort-tag" :class="comfortLevel.tone">
                            {{ comfortLevel.label }}
                        </span>
                        <small>舒适度</small>
                    </div>
                </div>
                <div class="overview-status">
                    <div class="status-icon-wrap">
                        <SvgIcon name="check-circle" size="sm" />
                    </div>
                    <div class="status-body">
                        <strong>环境状态</strong>
                        <span>良好</span>
                        <small>各项指标在舒适范围内</small>
                    </div>
                </div>
            </div>

            <!-- ─── 环境指标网格 ─── -->
            <div class="metrics-grid">
                <article
                    v-for="item in metrics"
                    :key="item.n"
                    class="metric-card"
                    :style="{ '--metric-color': item.color, '--metric-tone': `var(--tone-${item.tone}-soft)` }"
                >
                    <header class="metric-header">
                        <span class="metric-icon" :style="{ background: `color-mix(in srgb, ${item.color} 16%, transparent)` }">
                            <SvgIcon :name="item.icon" size="sm" />
                        </span>
                        <span class="metric-name">{{ item.n }}</span>
                        <span
                            class="metric-status"
                            :style="{ color: getStatus(item).color }"
                        >
                            {{ getStatus(item).label }}
                        </span>
                    </header>
                    <div class="metric-value">
                        <strong>{{ item.v }}</strong>
                    </div>
                    <div class="metric-bar">
                        <div class="metric-bar-track">
                            <div
                                class="metric-bar-ideal"
                                :style="getIdealFill(item)"
                            />
                            <div
                                class="metric-bar-fill"
                                :style="{
                                    width: `${getPercent(item)}%`,
                                    background: item.color,
                                }"
                            />
                        </div>
                        <div class="metric-bar-labels">
                            <span>{{ item.range[0] }}</span>
                            <span class="metric-ideal-label">理想 {{ item.ideal[0] }}-{{ item.ideal[1] }}</span>
                            <span>{{ item.range[1] }}{{ item.unit === '°C' ? '°C' : item.unit === '%' ? '%' : item.unit === 'lux' ? ' lux' : item.unit === 'dB' ? ' dB' : '' }}</span>
                        </div>
                    </div>
                    <div class="metric-trend">
                        <span
                            v-for="(t, i) in item.trend"
                            :key="i"
                            class="trend-dot"
                            :style="{
                                height: `${(t / Math.max(...item.trend)) * 100}%`,
                                background: item.color,
                            }"
                        />
                    </div>
                </article>
            </div>

            <!-- ─── 环境趋势 ─── -->
            <section class="trend-card">
                <header>
                    <h3>
                        <SvgIcon name="comfort" size="sm" />
                        环境趋势
                    </h3>
                    <div class="trend-range">
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
                <div class="trend-chart-wrap">
                    <div class="trend-legend">
                        <span class="legend-item">
                            <span class="legend-line temp" />
                            温度
                        </span>
                        <span class="legend-item">
                            <span class="legend-line hum" />
                            湿度
                        </span>
                    </div>
                    <svg
                        class="trend-chart"
                        viewBox="0 0 760 200"
                        preserveAspectRatio="none"
                    >
                        <defs>
                            <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stop-color="var(--color-primary-500)" stop-opacity="0.25" />
                                <stop offset="100%" stop-color="var(--color-primary-500)" stop-opacity="0.02" />
                            </linearGradient>
                            <linearGradient id="humGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stop-color="#60a5fa" stop-opacity="0.2" />
                                <stop offset="100%" stop-color="#60a5fa" stop-opacity="0.02" />
                            </linearGradient>
                        </defs>
                        <g class="grid-lines">
                            <line
                                v-for="y in [30, 72, 114, 156]"
                                :key="y"
                                x1="20"
                                :y1="y"
                                x2="740"
                                :y2="y"
                            />
                        </g>
                        <path
                            class="trend-fill temp"
                            d="M20,120 L100,100 L180,96 L260,105 L340,88 L420,75 L500,80 L580,78 L660,102 L740,96 L740,200 L20,200 Z"
                            fill="url(#tempGrad)"
                        />
                        <polyline
                            class="trend-line temp"
                            points="20,120 100,100 180,96 260,105 340,88 420,75 500,80 580,78 660,102 740,96"
                        />
                        <path
                            class="trend-fill hum"
                            d="M20,142 L100,132 L180,135 L260,132 L340,144 L420,138 L500,136 L580,126 L660,132 L740,135 L740,200 L20,200 Z"
                            fill="url(#humGrad)"
                        />
                        <polyline
                            class="trend-line hum"
                            points="20,142 100,132 180,135 260,132 340,144 420,138 500,136 580,126 660,132 740,135"
                        />
                        <g class="dot-markers">
                            <circle cx="20" cy="120" r="3.5" class="marker temp" />
                            <circle cx="740" cy="96" r="3.5" class="marker temp" />
                            <circle cx="20" cy="142" r="3.5" class="marker hum" />
                            <circle cx="740" cy="135" r="3.5" class="marker hum" />
                        </g>
                    </svg>
                </div>
            </section>

            <!-- ─── 建议 ─── -->
            <div class="suggestions">
                <article class="suggestion-card air-quality">
                    <div class="suggestion-icon">
                        <SvgIcon name="air-quality" size="sm" />
                    </div>
                    <div class="suggestion-body">
                        <b>开启新风</b>
                        <small>PM2.5 良好，建议定期开启新风系统</small>
                    </div>
                </article>
                <article class="suggestion-card ventilation">
                    <div class="suggestion-icon">
                        <SvgIcon name="automation" size="sm" />
                    </div>
                    <div class="suggestion-body">
                        <b>适当通风</b>
                        <small>湿度适中，建议每日开窗通风 15 分钟</small>
                    </div>
                </article>
                <article class="suggestion-card quiet">
                    <div class="suggestion-icon">
                        <SvgIcon name="scene" size="sm" />
                    </div>
                    <div class="suggestion-body">
                        <b>夜间降低噪音</b>
                        <small>当前噪音水平适宜，建议保持安静环境</small>
                    </div>
                </article>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
/* ============================================================
   Environment Dialog — Room Environment Details
   ============================================================ */

.environment-dialog {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* ─── 顶部概览 ─── */

.overview-grid {
    display: grid;
    grid-template-columns: 1.2fr 0.9fr 1fr;
    gap: 12px;
}

.overview-grid > div {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    transition: border-color 220ms var(--motion-ease),
                box-shadow 220ms var(--motion-ease);
}

.overview-grid > div:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-card-hover);
}

/* 房间信息 */
.overview-room {
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--color-primary-500) 6%, var(--color-card-bg)),
        var(--color-card-bg)
    );
}

.room-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--color-primary-500), var(--color-primary-400));
    color: #fff;
    flex-shrink: 0;
}

.room-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.room-info strong {
    font-size: 17px;
    color: var(--color-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.room-status {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    color: var(--color-text-tertiary);
}

.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-success);
    animation: pulse-dot 2s var(--motion-ease) infinite;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* 舒适度 */
.overview-comfort {
    display: flex;
    gap: 12px;
}

.comfort-ring-wrap {
    position: relative;
    width: 48px;
    height: 48px;
    flex-shrink: 0;
}

.comfort-ring {
    width: 100%;
    height: 100%;
    transform: rotate(-90deg);
}

.ring-bg {
    stroke: var(--color-border-subtle);
}

.ring-fill {
    transition: stroke-dashoffset 600ms var(--motion-ease);
    stroke-linecap: round;
}

.comfort-value {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.comfort-value strong {
    font-size: 14px;
    line-height: 1;
    color: var(--color-text-primary);
}

.comfort-value small {
    font-size: 9px;
    color: var(--color-text-tertiary);
    line-height: 1;
}

.comfort-label {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.comfort-tag {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    width: fit-content;
}

.comfort-tag.success {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.comfort-tag.teal {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
}

.comfort-tag.warning {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.comfort-tag.danger {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.comfort-label small {
    font-size: 11px;
    color: var(--color-text-tertiary);
}

/* 环境状态 */
.overview-status {
    gap: 10px;
}

.status-icon-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: var(--color-success-soft);
    color: var(--color-success);
    flex-shrink: 0;
}

.status-body {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.status-body strong {
    font-size: 11px;
    color: var(--color-text-tertiary);
    font-weight: 500;
}

.status-body > span {
    font-size: 16px;
    font-weight: 700;
    color: var(--color-success);
}

.status-body small {
    font-size: 11px;
    color: var(--color-text-tertiary);
}

/* ─── 环境指标网格 ─── */

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
}

.metric-card {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 14px 12px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    animation: metric-enter 400ms var(--motion-ease) both;
    transition: border-color 220ms var(--motion-ease),
                box-shadow 220ms var(--motion-ease),
                transform 220ms var(--motion-ease);
}

.metric-card:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
}

.metric-card:nth-child(1) { animation-delay: 30ms; }
.metric-card:nth-child(2) { animation-delay: 60ms; }
.metric-card:nth-child(3) { animation-delay: 90ms; }
.metric-card:nth-child(4) { animation-delay: 120ms; }
.metric-card:nth-child(5) { animation-delay: 150ms; }

@keyframes metric-enter {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.metric-header {
    display: flex;
    align-items: center;
    gap: 6px;
}

.metric-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 7px;
    flex-shrink: 0;
    color: var(--metric-color);
}

.metric-name {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text-secondary);
    flex: 1;
}

.metric-status {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 6px;
    border-radius: 4px;
    background: color-mix(in srgb, currentColor 10%, transparent);
}

.metric-value strong {
    font-size: 20px;
    font-weight: 700;
    color: var(--color-text-primary);
    line-height: 1.2;
}

/* 指标条 */
.metric-bar {
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.metric-bar-track {
    position: relative;
    height: 5px;
    border-radius: 3px;
    background: var(--color-border-subtle);
    overflow: hidden;
}

.metric-bar-ideal {
    position: absolute;
    top: 0;
    height: 100%;
    border-radius: 3px;
    background: color-mix(in srgb, var(--metric-color) 14%, transparent);
    border: 1px solid color-mix(in srgb, var(--metric-color) 24%, transparent);
}

.metric-bar-fill {
    position: relative;
    height: 100%;
    border-radius: 3px;
    transition: width 600ms var(--motion-ease);
    z-index: 1;
}

.metric-bar-labels {
    display: flex;
    justify-content: space-between;
    font-size: 9px;
    color: var(--color-text-muted);
}

.metric-ideal-label {
    color: color-mix(in srgb, var(--metric-color) 60%, transparent);
    font-weight: 500;
}

/* 趋势柱状图 */
.metric-trend {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 28px;
    margin-top: auto;
}

.trend-dot {
    flex: 1;
    min-height: 3px;
    border-radius: 2px 2px 0 0;
    opacity: 0.65;
    transition: opacity 220ms var(--motion-ease);
}

.metric-card:hover .trend-dot {
    opacity: 0.9;
}

/* ─── 环境趋势 ─── */

.trend-card {
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    padding: 16px;
    transition: border-color 220ms var(--motion-ease),
                box-shadow 220ms var(--motion-ease);
}

.trend-card:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-card-hover);
}

.trend-card header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}

.trend-card h3 {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    color: var(--color-text-primary);
}

.trend-range {
    display: flex;
    gap: 4px;
    padding: 3px;
    border-radius: 9px;
    background: var(--color-surface-subtle);
}

.trend-range button {
    padding: 4px 12px;
    border: none;
    border-radius: 7px;
    background: transparent;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 180ms var(--motion-ease);
}

.trend-range button:hover {
    color: var(--color-text-secondary);
    background: color-mix(in srgb, var(--color-card-bg) 60%, transparent);
}

.trend-range button.active {
    background: var(--color-card-bg);
    color: var(--color-primary-600);
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.trend-chart-wrap {
    position: relative;
}

.trend-legend {
    position: absolute;
    top: 0;
    right: 0;
    display: flex;
    gap: 14px;
    font-size: 11px;
    color: var(--color-text-tertiary);
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 5px;
}

.legend-line {
    width: 16px;
    height: 3px;
    border-radius: 2px;
}

.legend-line.temp {
    background: var(--color-primary-500);
}

.legend-line.hum {
    background: #60a5fa;
}

.trend-chart {
    width: 100%;
    height: 200px;
}

.grid-lines line {
    stroke: var(--color-border-subtle);
    stroke-dasharray: 4 3;
    stroke-width: 1;
}

.trend-line {
    fill: none;
    stroke-width: 2.5;
    stroke-linejoin: round;
    stroke-linecap: round;
}

.trend-line.temp {
    stroke: var(--color-primary-500);
}

.trend-line.hum {
    stroke: #60a5fa;
}

.trend-fill {
    pointer-events: none;
}

.dot-markers .marker {
    stroke: var(--color-card-bg);
    stroke-width: 2;
}

.dot-markers .marker.temp {
    fill: var(--color-primary-500);
}

.dot-markers .marker.hum {
    fill: #60a5fa;
}

/* ─── 建议卡片 ─── */

.suggestions {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.suggestion-card {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
    transition: border-color 220ms var(--motion-ease),
                box-shadow 220ms var(--motion-ease),
                transform 220ms var(--motion-ease);
    animation: suggestion-enter 400ms var(--motion-ease) both;
}

.suggestion-card:nth-child(1) { animation-delay: 60ms; }
.suggestion-card:nth-child(2) { animation-delay: 100ms; }
.suggestion-card:nth-child(3) { animation-delay: 140ms; }

@keyframes suggestion-enter {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.suggestion-card:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-1px);
}

.suggestion-card.air-quality {
    border-left: 3px solid var(--color-success);
}

.suggestion-card.ventilation {
    border-left: 3px solid var(--tone-teal);
}

.suggestion-card.quiet {
    border-left: 3px solid var(--tone-purple);
}

.suggestion-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 9px;
    flex-shrink: 0;
}

.suggestion-card.air-quality .suggestion-icon {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.suggestion-card.ventilation .suggestion-icon {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
}

.suggestion-card.quiet .suggestion-icon {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}

.suggestion-body {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
}

.suggestion-body b {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text-primary);
}

.suggestion-body small {
    font-size: 11px;
    color: var(--color-text-tertiary);
    line-height: 1.4;
}

/* ─── 响应式 ─── */

@media (max-width: 900px) {
    .overview-grid {
        grid-template-columns: 1fr 1fr;
    }

    .overview-grid > div:last-child {
        grid-column: 1 / -1;
    }

    .metrics-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (max-width: 640px) {
    .overview-grid {
        grid-template-columns: 1fr;
    }

    .metrics-grid {
        grid-template-columns: 1fr 1fr;
    }

    .suggestions {
        grid-template-columns: 1fr;
    }
}
</style>
