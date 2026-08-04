<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import type { Room } from "../../types/room";

export interface RoomEnvironmentItem {
    name: string;
    value: string;
    tone: string;
    points: string;
}

defineProps<{
    room: Room;
    environment: RoomEnvironmentItem[];
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
            <div class="detail-heading">
                <span>{{ room.name.slice(0, 1) }}</span>
                <div>
                    <h3>
                        {{ room.name }}
                        <small>{{ room.comfort >= 84 ? "舒适" : "良好" }}</small>
                    </h3>
                    <p><b></b>在线</p>
                </div>
            </div>
            <dl>
                <div><dt>所在楼层</dt><dd>{{ room.floor }}</dd></div>
                <div><dt>面积</dt><dd>{{ room.area }} m²</dd></div>
                <div><dt>在线设备</dt><dd>{{ room.onlineCount }} / {{ room.deviceCount }} 个</dd></div>
                <div><dt>当前场景</dt><dd>休闲模式</dd></div>
                <div><dt>最近活动</dt><dd>10 分钟前（打开台灯）</dd></div>
            </dl>
            <div class="detail-actions">
                <button class="primary" type="button" @click="$emit('open', 'devices')">
                    <SvgIcon name="power" size="sm" />进入控制
                </button>
                <button type="button" @click="$emit('open', 'edit')">
                    <SvgIcon name="edit" size="sm" />编辑房间
                </button>
            </div>
        </section>
        <section class="environment-overview" @click="$emit('open', 'environment')">
            <h2><SvgIcon name="sensor" size="sm" />环境概览 <small>实时更新</small></h2>
            <div class="detail-environment">
                <p v-for="item in environment" :key="item.name">
                    <span>{{ item.name }}</span><strong>{{ item.value }}</strong>
                </p>
            </div>
        </section>
        <section>
            <h2><SvgIcon name="scene" size="sm" />快捷操作</h2>
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
    font-size: 15px;
    font-weight: 900;
}
.room-detail h2 svg {
    color: var(--color-primary-600);
}
.room-detail h2 > small {
    margin-left: auto;
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 750;
}
.detail-heading {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--color-border);
}
.detail-heading > span {
    display: grid;
    width: 48px;
    height: 48px;
    flex: 0 0 48px;
    place-items: center;
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        var(--color-primary-100),
        var(--color-primary-50)
    );
    color: var(--color-primary-700);
    font-size: 18px;
    font-weight: 900;
    box-shadow: 0 6px 16px var(--color-focus-ring);
}
.detail-heading > div {
    min-width: 0;
    flex: 1;
}
.detail-heading h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 900;
}
.detail-heading h3 small {
    margin-left: 6px;
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 2px 8px;
    color: var(--color-success);
    font-size: 11px;
    font-weight: 800;
}
.detail-heading p {
    margin: 5px 0 0;
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-weight: 750;
}
.detail-heading p b {
    display: inline-block;
    width: 7px;
    height: 7px;
    margin-right: 4px;
    border-radius: 50%;
    background: var(--color-success);
}
.room-detail dl {
    display: grid;
    gap: 2px;
    margin: 14px 0;
}
.room-detail dl div {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    padding: 8px 0;
    font-size: 12px;
}
.room-detail dl div + div {
    border-top: 1px solid var(--color-border-subtle);
}
.room-detail dt {
    color: var(--color-text-tertiary);
    font-weight: 750;
}
.room-detail dd {
    margin: 0;
    color: var(--color-text-secondary);
    font-weight: 900;
    text-align: right;
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
    font-size: 12px;
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
    font-size: 11px;
    font-weight: 750;
}
.detail-environment strong {
    margin-top: 3px;
    color: var(--color-text-primary);
    font-size: 14px;
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
    font-size: 12px;
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
