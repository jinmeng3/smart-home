<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Room } from "../../types/room";

export interface RoomEnvironmentItem {
    name: string;
    value: string;
    tone: string;
    points: string;
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

defineProps<{
    room: Room | null;
    environment: RoomEnvironmentItem[];
    currentScene?: string;
    recentActivity?: string;
    recentActivityTime?: string;
}>();

defineEmits<{
    quick: [action: string];
    open: [dialog: "edit" | "devices" | "environment" | "logs"];
}>();
</script>

<template>
    <aside class="room-detail">
        <section>
            <h2><SvgIcon name="room" size="sm" />房间详情</h2>
            <template v-if="room">
                <div class="detail-heading">
                    <span class="detail-avatar">{{ room.name.slice(0, 1) }}</span>
                    <div>
                        <h3>
                            {{ room.name }}
                            <small
                                class="comfort-badge"
                                :class="room.comfort >= 84 ? 'is-comfort' : 'is-good'"
                            >
                                {{ room.comfort >= 84 ? "舒适" : "良好" }}
                            </small>
                        </h3>
                        <p class="online-status"><span class="status-pulse" />在线</p>
                    </div>
                </div>
                <dl>
                    <div class="field-row">
                        <dt><SvgIcon name="home" size="sm" />所在楼层</dt>
                        <dd class="tone-primary">{{ room.floor }}</dd>
                    </div>
                    <div class="field-row">
                        <dt><SvgIcon name="scan" size="sm" />面积</dt>
                        <dd class="tone-teal">{{ room.area }} m²</dd>
                    </div>
                    <div class="field-row">
                        <dt><SvgIcon name="online-device" size="sm" />在线设备</dt>
                        <dd class="tone-success">{{ room.onlineCount }} / {{ room.deviceCount }} 个</dd>
                    </div>
                    <div class="field-row">
                        <dt><SvgIcon name="scene" size="sm" />当前场景</dt>
                        <dd class="tone-purple">{{ currentScene || '休闲模式' }}</dd>
                    </div>
                    <div class="field-row recent-activity-row">
                        <dt><SvgIcon name="clock" size="sm" />最近活动</dt>
                        <dd v-if="recentActivityTime" class="recent-activity tone-orange">
                            <small>{{ recentActivityTime }}</small>
                            <span>{{ formatRecentActivity(recentActivity) }}</span>
                        </dd>
                        <dd v-else class="recent-activity-empty">暂无活动记录</dd>
                    </div>
                </dl>
                <div class="detail-actions">
                    <button class="primary" type="button" @click="$emit('open', 'devices')">
                        <SvgIcon name="power" size="sm" />进入控制
                    </button>
                    <button type="button" @click="$emit('open', 'edit')">
                        <SvgIcon name="edit" size="sm" />编辑房间
                    </button>
                </div>
            </template>
            <div v-else class="section-empty">
                <SvgIcon name="room" size="lg" />
                <p>暂无房间数据</p>
            </div>
        </section>
        <section class="environment-overview" @click="room && $emit('open', 'environment')">
            <h2><SvgIcon name="sensor" size="sm" />环境概览 <small>实时更新</small></h2>
            <template v-if="room">
                <div class="detail-environment">
                    <p v-for="item in environment" :key="item.name">
                        <span>{{ item.name }}</span><strong>{{ item.value }}</strong>
                    </p>
                </div>
            </template>
            <div v-else class="section-empty">
                <SvgIcon name="sensor" size="lg" />
                <p>暂无环境数据</p>
            </div>
        </section>
        <section>
            <h2><SvgIcon name="scene" size="sm" />快捷操作</h2>
            <template v-if="room">
                <div class="detail-quick">
                    <button type="button" @click="$emit('quick', 'all_lights')">
                        <SvgIcon name="light" />全开灯光
                    </button>
                    <button type="button" @click="$emit('quick', 'air_conditioner')">
                        <SvgIcon name="air-conditioner" />关闭空调
                    </button>
                    <button type="button" @click="$emit('quick', 'curtains')">
                        <SvgIcon name="curtain" />打开窗帘
                    </button>
                    <button type="button" @click="$emit('open', 'logs')">
                        <SvgIcon name="log" />查看日志
                    </button>
                </div>
            </template>
            <div v-else class="section-empty">
                <SvgIcon name="scene" size="lg" />
                <p>请先添加房间后操作</p>
            </div>
        </section>
    </aside>
</template>

<style scoped>
.room-detail {
    display: flex;
    min-width: 0;
    min-height: 0;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    border: 1px solid var(--color-border);
    border-radius: 18px;
    background: var(--color-page-bg);
    padding: 12px;
}
.room-detail > section {
    border: 1px solid var(--color-border);
    border-radius: 14px;
    background: var(--color-card-bg);
    padding: 16px;
    box-shadow: var(--shadow-card);
    transition:
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}
.room-detail h2 {
    display: flex;
    align-items: center;
    gap: 7px;
    margin: 0 0 14px;
    color: var(--color-text-primary);
    font-size: 18px;
    font-weight: 900;
}
.room-detail h2 svg {
    color: var(--color-primary-600);
}
.room-detail h2 > small {
    margin-left: auto;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 750;
}
.detail-heading {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--color-border);
}
.detail-heading .detail-avatar {
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        var(--color-primary-500),
        var(--color-primary-400)
    );
    color: #fff;
    font-size: 20px;
    font-weight: 900;
    box-shadow: 0 6px 16px var(--color-focus-ring);
}
.detail-heading > div {
    min-width: 0;
    flex: 1;
}
.detail-heading h3 {
    margin: 0;
    font-size: 19px;
    font-weight: 900;
    color: var(--color-text-primary);
}
.detail-heading h3 .comfort-badge {
    margin-left: 6px;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 13px;
    font-weight: 800;
    vertical-align: middle;
}
.detail-heading h3 .comfort-badge.is-comfort {
    background: linear-gradient(135deg, var(--color-success-soft), #f0fdf4);
    color: var(--color-success);
}
.detail-heading h3 .comfort-badge.is-good {
    background: linear-gradient(135deg, var(--tone-teal-soft), #ecfdfa);
    color: var(--tone-teal);
}
.detail-heading .online-status {
    margin: 5px 0 0;
    color: var(--color-success);
    font-size: 14px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 5px;
}
.detail-heading .online-status .status-pulse {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-success);
    animation: pulse-dot 2s var(--motion-ease) infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.room-detail dl {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 14px 0;
}
.room-detail dl .field-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    padding: 9px 0;
    font-size: 14px;
    transition: background 160ms var(--motion-ease);
    border-radius: 8px;
    padding-left: 8px;
    padding-right: 8px;
    margin: 0 -8px;
}
.room-detail dl .field-row:hover {
    background: var(--color-surface-hover);
}
.room-detail dl .field-row + .field-row {
    border-top: 1px solid var(--color-border-subtle);
}
.room-detail dt {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-weight: 700;
    font-size: 13px;
}
.room-detail dt svg {
    color: var(--color-text-muted);
    width: 14px;
    height: 14px;
}
.room-detail dt:hover svg {
    color: var(--color-text-tertiary);
}
.room-detail dd {
    margin: 0;
    font-weight: 800;
    text-align: right;
    font-size: 14px;
}
.room-detail dd.tone-primary {
    color: var(--color-primary-600);
}
.room-detail dd.tone-teal {
    color: var(--tone-teal);
}
.room-detail dd.tone-success {
    color: var(--color-success);
}
.room-detail dd.tone-purple {
    color: var(--tone-purple);
}
.room-detail dd.tone-orange {
    color: var(--tone-orange);
}
.room-detail dl .recent-activity-row {
    align-items: flex-start;
}
.recent-activity-row dt {
    flex: 0 0 auto;
    padding-top: 4px;
    white-space: nowrap;
}
.recent-activity,
.recent-activity-empty {
    min-width: 0;
    max-width: 68%;
}
.recent-activity {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
}
.recent-activity small {
    border-radius: 999px;
    background: var(--tone-orange-soft);
    padding: 2px 7px;
    color: var(--tone-orange);
    font-size: 11px;
    line-height: 1.4;
    white-space: nowrap;
}
.recent-activity span {
    max-width: 100%;
    color: var(--color-text-secondary);
    font-size: 13px;
    line-height: 1.55;
    overflow-wrap: anywhere;
}
.recent-activity-empty {
    color: var(--color-text-tertiary);
    font-size: 13px;
}
.detail-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.detail-actions button {
    display: inline-flex;
    min-height: 38px;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid var(--color-border);
    border-radius: 9px;
    color: var(--color-text-secondary);
    font-size: 14px;
    font-weight: 900;
    transition: 160ms var(--motion-ease);
}
.detail-actions button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    transform: translateY(-1px);
}
.detail-actions button.primary {
    border-color: var(--color-primary-600);
    background: var(--color-primary-600) !important;
    color: white !important;
}
.environment-overview {
    cursor: pointer;
}
.environment-overview:hover {
    border-color: var(--color-primary-200);
    box-shadow: var(--shadow-card-hover);
}
.detail-environment {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.detail-environment p {
    margin: 0;
    border-radius: 9px;
    background: var(--color-surface-subtle);
    padding: 10px 12px;
    transition: background 160ms var(--motion-ease);
}
.detail-environment p:hover {
    background: var(--color-primary-50);
}
.detail-environment span,
.detail-environment strong {
    display: block;
}
.detail-environment span {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 750;
}
.detail-environment strong {
    margin-top: 3px;
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
}
.detail-quick {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}
.detail-quick button {
    display: flex;
    min-width: 0;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    border-radius: 9px;
    background: var(--color-primary-50);
    padding: 12px 6px;
    color: var(--color-primary-700);
    font-size: 14px;
    font-weight: 800;
    transition: 160ms var(--motion-ease);
}
.detail-quick button:hover {
    background: var(--color-primary-100);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-1px);
}
.detail-quick button svg {
    width: 18px;
    height: 18px;
}
.section-empty {
    display: flex;
    min-height: 120px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border: 1px dashed var(--color-border);
    border-radius: 12px;
    padding: 24px 16px;
    color: var(--color-text-tertiary);
    text-align: center;
}
.section-empty svg {
    width: 36px;
    height: 36px;
    color: var(--color-primary-300);
}
.section-empty p {
    margin: 0;
    font-size: 14px;
    font-weight: 700;
}

@media (prefers-reduced-motion: reduce) {
    .room-detail > section,
    .detail-actions button,
    .detail-quick button {
        transition-duration: 1ms;
    }
    .detail-actions button:hover,
    .detail-quick button:hover {
        transform: none;
    }
}
</style>
