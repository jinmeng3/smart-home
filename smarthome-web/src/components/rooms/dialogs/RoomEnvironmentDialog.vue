<script setup lang="ts">
import { computed, ref, watch } from "vue";
import BaseSmartModal from "../../common/BaseSmartModal.vue";
import SvgIcon from "../../common/SvgIcon.vue";
import { getRoomEnvironmentLatest, getRoomEnvironmentTrends } from "../../../api/room";
import type { Room, RoomEnvironmentLatest, RoomEnvironmentTrend } from "../../../types/room";
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

// === 环境指标获取 ===

const env = ref<RoomEnvironmentLatest>();
const trend = ref<RoomEnvironmentTrend>();
const { run } = useLatestRequest();
watch(
    () => props.room?.id,
    (id) => {
        env.value = undefined;
        trend.value = undefined;
        if (id) {
            void run(
                () => getRoomEnvironmentLatest(id),
                (result) => { env.value = result; },
                () => { env.value = undefined; },
            );
            // 加载趋势数据，无采样时后端返回空数组，展示"暂无数据"
            void getRoomEnvironmentTrends(id, "temperature,humidity,pm25,illuminance,noise")
                .then((result) => { trend.value = result; })
                .catch(() => { trend.value = undefined; });
        }
    },
    { immediate: true },
);

const hasSamples = computed(() => !!env.value?.sampledAt && Object.keys(env.value?.values ?? {}).length > 0);
const hasTrends = computed(() => (trend.value?.items?.length ?? 0) > 0);

const metricValue = (name: string, fallback: number): number =>
    env.value?.values?.[name] ?? fallback;

// 从趋势数据中提取指定指标的数值序列
const trendValues = (metric: string): number[] => {
    if (!trend.value?.items?.length) return [];
    return trend.value.items
        .map((point) => point.values?.[metric])
        .filter((v): v is number => v !== undefined && v !== null);
};

// === 舒适度等级 ===

const comfortLevel = computed(() => {
    const c = props.room?.comfort ?? 83;
    if (c >= 85) return { label: "优秀", color: "var(--color-success)", tone: "success" };
    if (c >= 70) return { label: "良好", color: "var(--tone-teal)", tone: "teal" };
    if (c >= 50) return { label: "一般", color: "var(--color-warning)", tone: "warning" };
    return { label: "较差", color: "var(--color-danger)", tone: "danger" };
});

const comfortPercent = computed(() => props.room?.comfort ?? 83);

// === 环境指标配置 ===

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
        v: hasSamples.value ? `${metricValue("temperature", 0)}°C` : "暂无数据",
        raw: metricValue("temperature", 24),
        unit: "°C",
        range: [10, 40],
        ideal: [20, 26],
        color: "#3b82f6",
        tone: "primary",
        icon: "temperature",
        trend: trendValues("temperature"),
    },
    {
        n: "湿度",
        v: hasSamples.value ? `${metricValue("humidity", 0)}%` : "暂无数据",
        raw: metricValue("humidity", 55),
        unit: "%",
        range: [0, 100],
        ideal: [40, 60],
        color: "#0ea5e9",
        tone: "info",
        icon: "humidity",
        trend: trendValues("humidity"),
    },
    {
        n: "PM2.5",
        v: hasSamples.value ? `${metricValue("pm25", 0)} μg/m³` : "暂无数据",
        raw: metricValue("pm25", 12),
        unit: "μg/m³",
        range: [0, 150],
        ideal: [0, 35],
        color: "#22c55e",
        tone: "success",
        icon: "air-quality",
        trend: trendValues("pm25"),
    },
    {
        n: "光照",
        v: hasSamples.value ? `${metricValue("illuminance", 0)} lux` : "暂无数据",
        raw: metricValue("illuminance", 350),
        unit: "lux",
        range: [0, 1000],
        ideal: [100, 500],
        color: "#f59e0b",
        tone: "warning",
        icon: "illumination",
        trend: trendValues("illuminance"),
    },
    {
        n: "噪音",
        v: hasSamples.value ? `${metricValue("noise", 0)} dB` : "暂无数据",
        raw: metricValue("noise", 35),
        unit: "dB",
        range: [0, 120],
        ideal: [30, 60],
        color: "#8b5cf6",
        tone: "purple",
        icon: "noise",
        trend: trendValues("noise"),
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

// === 时间格式化 ===

const trendPoints = computed(() => {
    if (!hasTrends.value || !trend.value?.items) return [];
    return trend.value.items.map((point) => ({
        temp: point.values?.temperature ?? 0,
        hum: point.values?.humidity ?? 0,
    }));
});
</script>

<template>
    <BaseSmartModal
        :model-value="modelValue"
        :title="title"
        :description="description"
        :width="820"
        confirm-text="关闭"
        @cancel="close"
        @update:model-value="close"
    >
        <div class="environment-dialog">
            <div class="overview-grid">
                <div class="overview-room">
                    <div class="room-badge">
                        <SvgIcon name="room" size="sm" />
                    </div>
                    <div class="room-info">
                        <strong>{{ room?.name }}</strong>
                        <span>{{ room?.floor }} · {{ room?.roomType }}</span>
                    </div>
                </div>
                <div class="overview-status">
                    <div class="status-icon-wrap">
                        <SvgIcon name="check-circle" size="sm" />
                    </div>
                    <div class="status-body">
                        <strong>环境状态</strong>
                        <span>舒适度 {{ comfortLevel.label }}</span>
                    </div>
                </div>
            </div>

            <!-- 无采样数据时展示空态 -->
            <div v-if="!hasSamples && !env" class="empty-state">
                <SvgIcon name="air-quality" />
                <span>暂无环境采样数据</span>
            </div>

            <div v-else class="metrics-grid">
                <div
                    v-for="item in metrics"
                    :key="item.n"
                    class="metric-card"
                    :style="`--metric-color: ${item.color}`"
                >
                    <header class="metric-header">
                        <span class="metric-icon" :style="{ background: `color-mix(in srgb, ${item.color} 16%, transparent)` }">
                            <SvgIcon :name="item.icon" size="sm" />
                        </span>
                        <span class="metric-name">{{ item.n }}</span>
                        <span
                            class="metric-status"
                            :style="{ color: getStatus(item).color }"
                        >{{ getStatus(item).label }}</span>
                    </header>
                    <div class="metric-value">
                        <strong>{{ item.v }}</strong>
                    </div>
                    <div class="metric-bar">
                        <span class="bar-fill" :style="{ width: `${getPercent(item)}%`, background: item.color }"></span>
                        <span class="ideal-zone" :style="getIdealFill(item)"></span>
                    </div>
                    <div class="metric-trend" v-if="item.trend.length > 0">
                        <span class="trend-dot" v-for="(val, idx) in item.trend.slice(-8)" :key="idx"
                            :style="{ opacity: 0.3 + (idx / Math.max(item.trend.length, 1)) * 0.7 }"
                        ></span>
                    </div>
                    <div v-else class="metric-trend-empty">
                        <small>无趋势数据</small>
                    </div>
                </div>
            </div>

            <section class="trend-card">
                <header>
                    <h3>
                        <SvgIcon name="comfort" size="sm" />
                        环境趋势
                    </h3>
                    <div class="trend-range">
                        <button
                            v-for="range in ['今日', '3日', '7日']"
                            :key="range"
                            :class="{ active: trendRange === range }"
                            @click="trendRange = range"
                        >{{ range }}</button>
                    </div>
                </header>
                <div v-if="trendPoints.length > 0" class="trend-chart">
                    <div class="trend-line">
                        <div
                            v-for="(point, idx) in trendPoints"
                            :key="idx"
                            class="trend-point"
                            :style="{
                                left: `${(idx / (trendPoints.length - 1)) * 100}%`,
                                bottom: `${((point.temp - 10) / 30) * 100}%`,
                            }"
                        >
                            <span class="trend-tooltip">{{ point.temp }}°C</span>
                        </div>
                    </div>
                    <div class="trend-axis">
                        <span>温度趋势</span>
                    </div>
                </div>
                <div v-else class="trend-empty">
                    <small>暂无趋势数据，无采样时展示"暂无数据"</small>
                </div>
            </section>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.environment-dialog {
    display: grid;
    gap: 16px;
}
.overview-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 12px;
}
.overview-room,
.overview-status {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-card-bg);
}
.room-badge,
.status-icon-wrap {
    display: grid;
    width: 44px;
    height: 44px;
    place-items: center;
    border-radius: 50%;
    flex-shrink: 0;
}
.room-badge {
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.status-icon-wrap {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.room-info strong,
.status-body strong {
    display: block;
    font-size: 14px;
}
.room-info span,
.status-body span {
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding: 40px 0;
    color: var(--color-text-muted);
}
.empty-state > svg {
    width: 48px;
    height: 48px;
    opacity: 0.3;
}
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    gap: 12px;
}
.metric-card {
    padding: 14px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-card-bg);
}
.metric-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
}
.metric-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
}
.metric-name {
    flex: 1;
    font-size: 12px;
    font-weight: 700;
}
.metric-status {
    font-size: 11px;
    font-weight: 800;
}
.metric-value strong {
    display: block;
    font-size: 22px;
    margin: 6px 0 10px;
}
.metric-bar {
    position: relative;
    height: 6px;
    border-radius: 999px;
    background: var(--color-surface-subtle);
    overflow: hidden;
}
.bar-fill {
    position: absolute;
    height: 100%;
    border-radius: 999px;
    transition: width 400ms ease;
}
.ideal-zone {
    position: absolute;
    height: 100%;
    background: color-mix(in srgb, var(--color-success) 20%, transparent);
    border-radius: 2px;
}
.metric-trend {
    display: flex;
    gap: 3px;
    margin-top: 10px;
    align-items: flex-end;
    height: 20px;
}
.trend-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--metric-color, var(--color-primary-500));
}
.metric-trend-empty {
    margin-top: 10px;
    color: var(--color-text-tertiary);
}
.trend-card {
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    padding: 16px;
    background: var(--color-card-bg);
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
    gap: 8px;
    font-size: 14px;
}
.trend-range {
    display: flex;
    gap: 4px;
}
.trend-range button {
    padding: 3px 10px;
    border: 1px solid var(--color-border-default);
    border-radius: 6px;
    background: transparent;
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
}
.trend-range button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.trend-chart {
    position: relative;
    height: 120px;
}
.trend-line {
    position: relative;
    height: 100%;
}
.trend-point {
    position: absolute;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-primary-500);
    transform: translate(-50%, 50%);
}
.trend-tooltip {
    display: none;
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    padding: 2px 6px;
    border-radius: 4px;
    background: var(--color-text-primary);
    color: var(--color-page-background);
    font-size: 10px;
    white-space: nowrap;
}
.trend-point:hover .trend-tooltip {
    display: block;
}
.trend-axis {
    text-align: center;
    color: var(--color-text-tertiary);
    font-size: 11px;
    margin-top: 4px;
}
.trend-empty {
    text-align: center;
    color: var(--color-text-tertiary);
    padding: 20px 0;
}
@media (max-width: 760px) {
    .overview-grid {
        grid-template-columns: 1fr;
    }
    .metrics-grid {
        grid-template-columns: 1fr 1fr;
    }
}
</style>