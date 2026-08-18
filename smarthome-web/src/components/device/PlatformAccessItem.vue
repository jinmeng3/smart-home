<script setup lang="ts">
import { computed } from "vue";
import SvgIcon from "../common/SvgIcon.vue";
import { platformIconMap } from "./deviceMeta";
import type { DevicePlatformInfo } from "../../types/device";

const props = defineProps<{
    platform: DevicePlatformInfo;
    expanded: boolean;
    syncing?: boolean;
}>();

const emit = defineEmits<{
    toggle: [];
    sync: [];
    manage: [];
}>();

const toneMap: Record<string, string> = {
    "Home Assistant": "orange",
    Matter: "blue",
    Zigbee: "green",
    MQTT: "purple",
};

const platformIcon = computed(
    () => platformIconMap[props.platform.name] ?? "platform",
);

const statusLabelMap: Record<string, string> = {
    connected: "已连接",
    syncing: "正在同步",
    authorization_required: "需要授权",
    error: "连接异常",
    disabled: "未配置",
};

const statusToneClass = computed(() => {
    switch (props.platform.status) {
        case "connected":
            return "is-connected";
        case "disabled":
            return "is-disabled";
        case "error":
            return "is-error";
        case "syncing":
            return "is-syncing";
        default:
            return "is-connecting";
    }
});

const statusLabel = computed(
    () => statusLabelMap[props.platform.status] ?? props.platform.status,
);
</script>

<template>
    <div class="platform-item" :class="{ 'is-expanded': expanded }">
        <button
            class="platform-row"
            type="button"
            :aria-expanded="expanded"
            @click="emit('toggle')"
        >
            <span
                class="platform-icon tone-chip"
                :class="`is-${toneMap[platform.name] ?? 'blue'}`"
            >
                <SvgIcon :name="platformIcon" size="sm" />
            </span>
            <span class="platform-main">
                <strong>{{ platform.name }}</strong>
                <span class="platform-meta" :class="statusToneClass">
                    <i class="platform-dot"></i>
                    {{ statusLabel }} · {{ platform.deviceCount }} 台设备
                </span>
            </span>
            <SvgIcon
                name="chevron-down"
                size="sm"
                class="platform-chevron"
                :class="{ 'is-open': expanded }"
            />
        </button>

        <Transition name="platform-detail">
            <div v-if="expanded" class="platform-detail">
                <dl class="platform-detail-grid">
                    <div>
                        <dt>设备</dt>
                        <dd>{{ platform.deviceCount }} 台</dd>
                    </div>
                    <div>
                        <dt>最近同步</dt>
                        <dd>{{ syncing ? "同步中…" : "—" }}</dd>
                    </div>
                </dl>
                <div class="platform-detail-actions">
                    <button
                        class="platform-action-btn is-sync"
                        type="button"
                        :disabled="syncing"
                        @click="emit('sync')"
                    >
                        <SvgIcon
                            :class="{ 'is-spinning': syncing }"
                            name="refresh"
                            size="sm"
                        />
                        {{ syncing ? "正在同步" : "立即同步" }}
                    </button>
                    <button
                        class="platform-action-btn"
                        type="button"
                        @click="emit('manage')"
                    >
                        管理接入
                    </button>
                </div>
            </div>
        </Transition>
    </div>
</template>

<style scoped>
.platform-item {
    border: 1px solid var(--color-border-subtle);
    border-radius: 11px;
    background: color-mix(in srgb, var(--color-panel-background) 82%, transparent);
    transition:
        background-color 140ms ease,
        border-color 140ms ease,
        box-shadow 140ms ease;
}

.platform-item.is-expanded {
    border-color: var(--color-primary-200);
    background: var(--color-panel-background);
    box-shadow: 0 7px 20px color-mix(in srgb, var(--color-text-primary) 5%, transparent);
}

.platform-row {
    display: grid;
    width: 100%;
    grid-template-columns: 28px minmax(0, 1fr) auto;
    align-items: center;
    gap: 9px;
    padding: 9px 10px;
    text-align: left;
    border-radius: 10px;
    transition: background-color 120ms var(--motion-ease);
}

.platform-row:hover {
    background: color-mix(in srgb, var(--color-surface-hover) 72%, transparent);
}

.platform-icon {
    display: grid;
    width: 32px;
    height: 32px;
    place-items: center;
    border-radius: 9px;
    font-size: 12px;
    font-weight: 900;
}

.platform-main {
    min-width: 0;
    display: grid;
    gap: 2px;
}

.platform-main strong {
    overflow: hidden;
    font-size: 13px;
    font-weight: 900;
    color: var(--color-text-secondary);
    text-overflow: ellipsis;
    white-space: nowrap;
}

.platform-meta {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-tertiary);
}

.platform-dot {
    width: 6px;
    height: 6px;
    flex: 0 0 6px;
    border-radius: 999px;
    background: currentColor;
}

.platform-meta.is-connected {
    color: var(--color-success);
}

.platform-meta.is-disabled {
    color: var(--color-text-muted);
}

.platform-meta.is-error {
    color: var(--color-danger);
}

.platform-meta.is-syncing {
    color: var(--color-primary-600);
}

.platform-meta.is-connecting {
    color: var(--color-warning);
}

.platform-chevron {
    width: 24px;
    height: 24px;
    padding: 4px;
    border-radius: 7px;
    color: var(--color-text-muted);
    transition: transform 180ms var(--motion-ease), background-color 140ms ease;
}

.platform-row:hover .platform-chevron {
    background: var(--color-surface-subtle);
}

.platform-chevron.is-open {
    transform: rotate(180deg);
}

/* 平台详情展开 */
.platform-detail {
    display: grid;
    gap: 8px;
    margin: 0 8px 8px;
    padding: 10px 12px;
    border-top: 1px solid var(--color-border-subtle);
}

.platform-detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 12px;
    margin: 0;
}

.platform-detail-grid div {
    display: grid;
    gap: 1px;
}

.platform-detail-grid dt {
    font-size: 11px;
    font-weight: 700;
    color: var(--color-text-muted);
}

.platform-detail-grid dd {
    margin: 0;
    font-size: 12px;
    font-weight: 800;
    color: var(--color-text-secondary);
}

.platform-detail-actions {
    display: flex;
    gap: 6px;
}

.platform-action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    height: 28px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 7px;
    padding: 0 10px;
    background: var(--color-panel-secondary);
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
    transition: background-color 120ms var(--motion-ease), color 120ms ease;
}

.platform-action-btn:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.platform-action-btn.is-sync {
    color: var(--color-primary-600);
}

.platform-action-btn.is-sync:hover {
    background: var(--color-primary-50);
}

.platform-action-btn:disabled {
    opacity: 0.6;
    cursor: default;
}

svg.is-spinning {
    animation-duration: 800ms;
}

/* 高度 + 透明度展开动画 */
.platform-detail-enter-active,
.platform-detail-leave-active {
    transition:
        opacity 200ms ease,
        transform 200ms var(--motion-ease);
    overflow: hidden;
}

.platform-detail-enter-from {
    opacity: 0;
    transform: translateY(-4px);
}

.platform-detail-leave-to {
    opacity: 0;
    transform: translateY(-4px);
}

@media (prefers-reduced-motion: reduce) {
    .platform-detail-enter-active,
    .platform-detail-leave-active {
        transition-duration: 1ms;
    }
    svg.is-spinning {
        animation-duration: 1.5s;
    }
}
</style>
