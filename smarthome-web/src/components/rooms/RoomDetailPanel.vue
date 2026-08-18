<script setup lang="ts">
import { computed, ref } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Room } from "../../types/room";

export interface RoomEnvironmentItem {
    name: string;
    value: string;
    tone: string;
    points: string;
    statusLabel?: string;
}

const statusLabels: Record<string, string> = {
    ONLINE: "在线",
    OFFLINE: "离线",
    RUNNING: "运行中",
    WARNING: "异常",
};

const formatRecentActivity = (activity?: string) =>
    activity?.replace(
        /DeviceStatus\.(ONLINE|OFFLINE|RUNNING|WARNING)/g,
        (_, status: string) => statusLabels[status] ?? status,
    ) ?? "";

const props = defineProps<{
    room: Room | null;
    environment: RoomEnvironmentItem[];
    currentScene?: string;
    recentActivity?: string;
    recentActivityTime?: string;
}>();

const emit = defineEmits<{
    quick: [action: string];
    open: [dialog: "edit" | "devices" | "environment" | "logs"];
    send: [content: string];
}>();

/* === 输入框 === */
const inputValue = ref("");
const inputRef = ref<HTMLTextAreaElement | null>(null);

const submitInput = () => {
    const trimmed = inputValue.value.trim();
    if (!trimmed) return;
    emit("send", trimmed);
    inputValue.value = "";
    if (inputRef.value) {
        inputRef.value.style.height = "auto";
    }
};

const onInputKeydown = (event: KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        submitInput();
    }
};

const autoResize = () => {
    const el = inputRef.value;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 80)}px`;
};

/* === 房间摘要文本 === */
const roomSummary = computed(() => {
    if (!props.room) return "";
    const name = props.room.name;
    const online = props.room.onlineCount;
    const total = props.room.deviceCount;
    const comfort = props.room.comfort >= 84 ? "舒适" : "良好";
    return `${name}环境整体${comfort}，${online}/${total} 台设备在线。`;
});

/* === 环境指标摘要 === */
const envSummary = computed(() => {
    const parts: string[] = [];
    for (const item of props.environment) {
        if (item.statusLabel) {
            parts.push(`${item.name} ${item.statusLabel}`);
        }
    }
    return parts.length > 0 ? parts.join("，") + "。" : "";
});

/* === 建议 === */
interface Suggestion {
    text: string;
    action: string;
    label: string;
    secondary?: { label: string; action: string };
}

const suggestions = computed<Suggestion[]>(() => {
    const list: Suggestion[] = [];
    for (const item of props.environment) {
        if (item.name === "温度" && item.statusLabel === "偏热") {
            list.push({
                text: "温度偏高，是否开启空调降温？",
                action: "air_conditioner",
                label: "开启空调",
                secondary: { label: "暂不处理", action: "" },
            });
        }
        if (item.name === "光照" && item.statusLabel === "明亮") {
            list.push({
                text: "光照较强，是否关闭窗帘？",
                action: "curtains",
                label: "关闭窗帘",
                secondary: { label: "暂不处理", action: "" },
            });
        }
        if (item.name === "PM2.5" && (item.statusLabel === "良" || item.statusLabel === "差")) {
            list.push({
                text: "空气质量需要关注，是否开启空气净化器？",
                action: "all_lights",
                label: "开启净化",
                secondary: { label: "忽略", action: "" },
            });
        }
        if (item.name === "湿度" && item.statusLabel === "干燥") {
            list.push({
                text: "空气偏干，建议开启加湿器。",
                action: "all_lights",
                label: "开启加湿",
                secondary: { label: "知道了", action: "" },
            });
        }
    }
    return list.slice(0, 2);
});

const quickActions = [
    { label: "全开灯光", icon: "light", action: "all_lights" },
    { label: "关闭全部", icon: "power", action: "all_off" },
    { label: "离家模式", icon: "scene", action: "away_mode" },
];

const hasRecentActivity = computed(
    () => props.recentActivityTime && props.recentActivity,
);

/* === 环境指标颜色 === */
const envCardColors: Record<string, [string, string]> = {
    "温度": ["#f97316", "#fff7ed"],
    "湿度": ["#0ea5e9", "#f0f9ff"],
    "PM2.5": ["#10b981", "#ecfdf5"],
    "光照": ["#f59e0b", "#fffbeb"],
    "噪音": ["#8b5cf6", "#f5f3ff"],
};

const getEnvStyle = (name: string) => {
    const colors = envCardColors[name];
    return colors ? { '--mc': colors[0], '--ms': colors[1] } : {};
};

/* === 暴露给父组件用于 collapsed 状态 === */
const envFirst = computed(() => props.environment[0]);
const envSecond = computed(() => props.environment[1]);
const alertCount = computed(() => {
    let count = 0;
    for (const item of props.environment) {
        if (item.statusLabel === "差" || item.statusLabel === "偏热" || item.statusLabel === "潮湿") {
            count++;
        }
    }
    return count;
});
</script>

<template>
    <div class="ra-content">
        <template v-if="room">
            <!-- 助手状态卡 -->
            <section class="assistant-card" :key="'card-' + room.id">
                <p class="ac-summary">{{ roomSummary }}</p>
                <p v-if="envSummary" class="ac-env">{{ envSummary }}</p>
                <div class="ac-metrics">
                    <article
                        v-for="item in environment"
                        :key="item.name"
                        class="ac-metric"
                        :style="getEnvStyle(item.name)"
                        role="button"
                        tabindex="0"
                        @click="$emit('open', 'environment')"
                        @keydown.enter="$emit('open', 'environment')"
                    >
                        <span class="ac-metric-value">{{ item.value }}</span>
                        <span v-if="item.statusLabel" class="ac-metric-label">{{ item.statusLabel }}</span>
                    </article>
                </div>
            </section>

            <!-- 建议卡 -->
            <section
                v-for="(sug, idx) in suggestions"
                :key="'sug-' + idx"
                class="suggestion-card"
                :style="{ '--sug-delay': `${idx * 80}ms` }"
            >
                <p class="sug-text">{{ sug.text }}</p>
                <div class="sug-actions">
                    <button
                        class="action-btn"
                        type="button"
                        @click="sug.action ? $emit('quick', sug.action) : undefined"
                    >
                        {{ sug.label }}
                    </button>
                    <button
                        v-if="sug.secondary"
                        class="action-btn is-secondary"
                        type="button"
                    >
                        {{ sug.secondary.label }}
                    </button>
                </div>
            </section>

            <!-- 快捷指令 -->
            <section class="quick-section">
                <h4 class="qs-title"><span class="title-icon is-orange"><SvgIcon name="light" size="sm" /></span>快捷指令</h4>
                <div class="qs-grid">
                    <button
                        v-for="act in quickActions"
                        :key="act.action"
                        class="qs-btn"
                        :class="`qs-btn-${act.action}`"
                        type="button"
                        @click="$emit('quick', act.action)"
                    >
                        <SvgIcon :name="act.icon" size="sm" />
                        <span>{{ act.label }}</span>
                    </button>
                    <button
                        class="qs-btn qs-btn-edit"
                        type="button"
                        @click="$emit('open', 'edit')"
                    >
                        <SvgIcon name="edit" size="sm" />
                        <span>编辑房间</span>
                    </button>
                </div>
            </section>

            <!-- 最近执行 -->
            <section v-if="hasRecentActivity" class="recent-section" :key="'recent-' + room.id">
                <h4 class="qs-title"><span class="title-icon is-green"><SvgIcon name="clock" size="sm" /></span>最近执行</h4>
                <div class="recent-row">
                    <span class="recent-check">
                        <SvgIcon name="check-circle" size="sm" />
                    </span>
                    <span class="recent-time">{{ recentActivityTime }}</span>
                    <span class="recent-desc">{{ formatRecentActivity(recentActivity) }}</span>
                </div>
            </section>
        </template>

        <!-- 空状态 -->
        <div v-else class="ra-empty">
            <SvgIcon name="room" size="lg" />
            <p>暂无房间数据</p>
        </div>

        <!-- 输入区（sticky 固定于底部） -->
        <div class="ra-composer">
            <form class="composer-form" @submit.prevent="submitInput">
                <textarea
                    ref="inputRef"
                    v-model="inputValue"
                    rows="1"
                    class="composer-input"
                    :placeholder="room ? `问问${room.name}助手……` : '暂无房间'"
                    :disabled="!room"
                    @keydown="onInputKeydown"
                    @input="autoResize"
                ></textarea>
                <button
                    class="composer-send"
                    type="submit"
                    :disabled="!inputValue.trim() || !room"
                    :aria-label="inputValue.trim() ? '发送' : '输入问题'"
                >
                <SvgIcon name="arrow-right" />
                </button>
            </form>
        </div>
    </div>
</template>

<style scoped>
.ra-content {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
    min-height: 100%;
}

/* === 助手状态卡 === */
.assistant-card {
    border: 1px solid var(--color-border);
    border-radius: 16px;
    background: var(--color-card-bg);
    padding: 16px 18px;
    animation: card-enter 220ms var(--motion-ease-out) both;
}

@keyframes card-enter {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

.ac-summary {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 700;
    line-height: 1.6;
}

.ac-env {
    margin: 6px 0 0;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
    line-height: 1.5;
}

.ac-metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--color-border-subtle);
}

.ac-metric {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    min-height: 88px;
    border: 1px solid color-mix(in srgb, var(--mc, var(--color-primary-500)) 20%, transparent);
    border-radius: 12px;
    background: var(--ms, var(--color-surface-subtle));
    padding: 12px 8px;
    cursor: pointer;
    transition: border-color 120ms var(--motion-ease), transform 120ms var(--motion-ease);
}

.ac-metric:hover {
    border-color: var(--mc, var(--color-primary-300));
    transform: translateY(-1px);
}

.ac-metric:focus-visible {
    outline: 2px solid var(--mc, var(--color-primary-500));
    outline-offset: 1px;
}

.ac-metric-value {
    color: var(--mc, var(--color-text-primary));
    font-size: 24px;
    font-weight: 900;
    line-height: 1.2;
    letter-spacing: -0.01em;
}

.ac-metric-label {
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
}

/* === 建议卡 === */
.suggestion-card {
    border: 1px solid color-mix(in srgb, #8b5cf6 20%, transparent);
    border-radius: 14px;
    background: linear-gradient(135deg, rgb(239 246 255 / 95%), rgb(245 243 255 / 95%));
    padding: 14px 16px;
    animation: sug-enter 240ms var(--motion-ease-out) both;
    animation-delay: var(--sug-delay, 0ms);
}

@keyframes sug-enter {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

.sug-text {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 700;
    line-height: 1.5;
}

.sug-actions {
    display: flex;
    gap: 6px;
    margin-top: 10px;
    animation: actions-fade-in 200ms var(--motion-ease) both;
}

@keyframes actions-fade-in {
    from { opacity: 0; transform: translateY(4px); }
    to { opacity: 1; transform: translateY(0); }
}

.action-btn {
    display: inline-flex;
    height: 36px;
    align-items: center;
    gap: 6px;
    border-radius: 8px;
    border: 1px solid color-mix(in srgb, #8b5cf6 30%, transparent);
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    padding: 0 14px;
    color: #fff;
    font-size: 13px;
    font-weight: 800;
    cursor: pointer;
    transition:
        background-color 120ms var(--motion-ease),
        border-color 120ms var(--motion-ease),
        transform 120ms var(--motion-ease);
}

.action-btn:hover {
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    transform: translateY(-1px);
}

.action-btn:active {
    transform: scale(0.97);
}

.action-btn:focus-visible {
    outline: 2px solid #8b5cf6;
    outline-offset: 1px;
}

.action-btn.is-secondary {
    border: 1px solid var(--color-border);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}

.action-btn.is-secondary:hover {
    border-color: var(--color-border-strong);
    color: var(--color-text-primary);
    background: var(--color-surface-hover);
}

/* === 快捷指令 === */
.quick-section {
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px 16px;
    animation: card-enter 240ms var(--motion-ease-out) both;
}

.qs-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 10px;
    color: var(--color-text-primary);
    font-size: 15px;
    font-weight: 800;
}

.qs-title svg {
    width: 16px;
    height: 16px;
}

.title-icon {
    display: grid;
    width: 28px;
    height: 28px;
    flex: 0 0 28px;
    place-items: center;
    border-radius: 7px;
}

.title-icon svg {
    width: 14px;
    height: 14px;
}

.title-icon.is-blue {
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.title-icon.is-green {
    background: var(--color-success-soft);
    color: var(--color-success);
}

.title-icon.is-orange {
    background: var(--color-warning-soft);
    color: var(--color-warning);
}

.title-icon.is-purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}

.qs-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}

.qs-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 46px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 0 14px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 800;
    cursor: pointer;
    transition:
        border-color 120ms var(--motion-ease),
        background-color 120ms var(--motion-ease),
        color 120ms var(--motion-ease),
        transform 120ms var(--motion-ease);
}

.qs-btn svg {
    width: 20px;
    height: 20px;
    flex: 0 0 20px;
    color: var(--color-primary-600);
}

.qs-btn:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    transform: translateY(-1px);
}

.qs-btn:active {
    transform: scale(0.97);
}

.qs-btn:focus-visible {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 1px;
}

.qs-btn-all_lights {
    border-color: color-mix(in srgb, #f59e0b 30%, transparent);
}

.qs-btn-all_lights svg {
    color: #f59e0b;
}

.qs-btn-all_lights:hover {
    border-color: #f59e0b;
    background: #fffbeb;
    color: #b45309;
}

.qs-btn-all_off svg {
    color: var(--color-text-muted);
}

.qs-btn-all_off:hover {
    border-color: var(--color-danger);
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

.qs-btn-all_off:hover svg {
    color: var(--color-danger);
}

.qs-btn-away_mode {
    border-color: color-mix(in srgb, #3b82f6 30%, transparent);
}

.qs-btn-away_mode svg {
    color: #3b82f6;
}

.qs-btn-away_mode:hover {
    border-color: #3b82f6;
    background: #eff6ff;
    color: #1d4ed8;
}

.qs-btn-edit svg {
    color: var(--color-text-muted);
}

.qs-btn-edit:hover svg {
    color: var(--color-primary-600);
}

/* === 最近执行 === */
.recent-section {
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 14px 16px;
    animation: card-enter 260ms var(--motion-ease-out) both;
}

.recent-row {
    display: flex;
    align-items: center;
    gap: 6px;
}

.recent-check {
    flex: 0 0 auto;
    color: var(--color-success);
}

.recent-check svg {
    width: 16px;
    height: 16px;
}

.recent-time {
    flex: 0 0 auto;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
}

.recent-desc {
    min-width: 0;
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 700;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* === 空状态 === */
.ra-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex: 1;
    min-height: 120px;
    color: var(--color-text-tertiary);
}

.ra-empty svg {
    width: 36px;
    height: 36px;
    color: var(--color-primary-300);
}

.ra-empty p {
    margin: 0;
    font-size: 13px;
    font-weight: 700;
}

/* === 输入区（sticky 固定于底部） === */
.ra-composer {
    position: sticky;
    bottom: 0;
    z-index: 2;
    margin-top: auto;
    padding-top: 8px;
    background: var(--color-card-bg);
}

.composer-form {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 46px;
    border: 1px solid var(--color-border);
    border-radius: 22px;
    background: var(--color-card-bg);
    padding: 4px 4px 4px 14px;
    transition:
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.composer-form:focus-within {
    border-color: #8b5cf6;
    box-shadow: 0 0 0 3px rgb(139 92 246 / 18%);
}

.composer-input {
    min-width: 0;
    flex: 1;
    resize: none;
    border: 0;
    background: transparent;
    padding: 6px 0;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 700;
    line-height: 1.5;
    outline: none;
    max-height: 80px;
}

.composer-input::placeholder {
    color: var(--color-text-muted);
    font-weight: 700;
}

.composer-send {
    display: grid;
    width: 36px;
    height: 36px;
    flex: 0 0 36px;
    place-items: center;
    border: none;
    border-radius: 50%;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed);
    color: #fff;
    cursor: pointer;
    transition:
        background-color 120ms var(--motion-ease),
        transform 120ms var(--motion-ease),
        box-shadow 120ms var(--motion-ease);
}

.composer-send:hover:not(:disabled) {
    background: linear-gradient(135deg, #7c3aed, #6d28d9);
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgb(139 92 246 / 30%);
}

.composer-send:active:not(:disabled) {
    transform: scale(0.95);
}

.composer-send:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

/* SvgIcon 接管图标渲染 */

/* === 响应式 === */
@media (max-width: 720px) {
    .ac-metrics {
        grid-template-columns: repeat(2, 1fr);
    }
    .qs-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (prefers-reduced-motion: reduce) {
    .assistant-card,
    .suggestion-card,
    .quick-section,
    .recent-section,
    .sug-actions {
        animation: none;
    }
    .action-btn,
    .qs-btn,
    .composer-send,
    .composer-form,
    .ac-metric {
        transition-duration: 1ms;
    }
    .action-btn:hover,
    .qs-btn:hover,
    .composer-send:hover:not(:disabled),
    .ac-metric:hover {
        transform: none;
    }
    .action-btn:active,
    .qs-btn:active,
    .composer-send:active:not(:disabled) {
        transform: none;
    }
}
</style>