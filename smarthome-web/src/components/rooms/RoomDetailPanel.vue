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
            <h2>房间详情</h2>
            <div class="detail-heading">
                <span>{{ room.name.slice(0, 1) }}</span>
                <div>
                    <h3>{{ room.name }} <small>舒适</small></h3>
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
            <h2>环境概览 <small>实时更新</small></h2>
            <div class="detail-environment">
                <p v-for="item in environment" :key="item.name">
                    <span>{{ item.name }}</span><strong>{{ item.value }}</strong>
                </p>
            </div>
        </section>
        <section>
            <h2>快捷操作</h2>
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
    padding: 15px;
    box-shadow: var(--shadow-card);
}
.room-detail h2 {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 0 13px;
    font-size: 14px;
}
.room-detail h2 > small {
    color: var(--color-text-tertiary);
    font-size: 9px;
}
.detail-heading {
    display: flex;
    align-items: center;
    gap: 10px;
}
.detail-heading > span {
    display: grid;
    width: 48px;
    height: 48px;
    place-items: center;
    border-radius: 12px;
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    font-weight: 900;
}
.detail-heading h3 {
    margin: 0;
    font-size: 14px;
}
.detail-heading h3 small {
    border-radius: 999px;
    background: var(--color-success-soft);
    padding: 2px 6px;
    color: var(--color-success);
    font-size: 9px;
}
.detail-heading p {
    margin: 5px 0 0;
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.detail-heading p b {
    display: inline-block;
    width: 6px;
    height: 6px;
    margin-right: 4px;
    border-radius: 50%;
    background: var(--color-success);
}
.room-detail dl {
    margin: 13px 0;
}
.room-detail dl div {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    border-bottom: 1px solid var(--color-border-subtle);
    padding: 8px 0;
    font-size: 10px;
}
.room-detail dt {
    color: var(--color-text-tertiary);
}
.room-detail dd {
    margin: 0;
    color: var(--color-text-secondary);
    font-weight: 800;
    text-align: right;
}
.detail-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
}
.detail-actions button {
    display: inline-flex;
    min-height: 34px;
    align-items: center;
    justify-content: center;
    gap: 5px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    color: var(--color-text-secondary);
    font-size: 10px;
    font-weight: 800;
}
.detail-actions button.primary {
    background: var(--color-primary-600) !important;
    color: white !important;
}
.environment-overview {
    cursor: pointer;
}
.detail-environment {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
}
.detail-environment p {
    margin: 0;
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 9px;
}
.detail-environment span,
.detail-environment strong {
    display: block;
}
.detail-environment span {
    color: var(--color-text-tertiary);
    font-size: 9px;
}
.detail-environment strong {
    margin-top: 3px;
    font-size: 12px;
}
.detail-quick {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
}
.detail-quick button {
    display: flex;
    min-width: 0;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    border-radius: 8px;
    background: var(--color-primary-50);
    padding: 9px 4px;
    color: var(--color-primary-700);
    font-size: 9px;
    font-weight: 800;
}
</style>
