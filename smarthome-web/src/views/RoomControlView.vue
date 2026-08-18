<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useAsyncAction } from "../composables/useAsyncAction";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { useCardGridEnter } from "../composables/useCardGridEnter";
import { ElMessage } from "element-plus";
import { ApiError } from "../api/client";
import { getErrorMessage } from "../utils/error";
import {
  createRoom,
  deleteRoom,
  fetchRooms,
  fetchRoomDetail,
  fetchRoomStats,
  getRoomEnvironmentLatest,
  runRoomQuickAction,
  updateRoom,
  updateRoomDevice,
} from "../api/room";
import ConfirmActionDialog from "../components/common/ConfirmActionDialog.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import PageHeader from "../components/common/PageHeader.vue";
import BaseCollapsibleRail from "../components/common/BaseCollapsibleRail.vue";
import RoomControlDialogs, {
    type RoomDialog,
} from "../components/rooms/RoomControlDialogs.vue";
import RoomStatsGrid from "../components/rooms/RoomStatsGrid.vue";
import RoomCard from "../components/rooms/RoomCard.vue";
import RoomControlPanel from "../components/rooms/RoomControlPanel.vue";
import RoomDetailPanel from "../components/rooms/RoomDetailPanel.vue";
import { toRoomDeviceCards, isDeviceActive } from "../utils/device";
import { metricConfig, metricLabels } from "../components/rooms/roomMeta";
import type {
    Room,
    RoomDeviceCard,
    RoomDetail,
    RoomStats,
} from "../types/room";
import type { RoomEnvironmentItem } from "../components/rooms/RoomDetailPanel.vue";

const rooms = ref<Room[]>([]);
const selectedId = ref<number>();
const pageLoading = ref(false);
const roomsLoading = ref(false);
const roomSaving = ref(false);
const activeCategory = ref("全部设备");
const temperature = ref(24);
const keyword = ref("");
const floor = ref("");
const roomType = ref("");
const activeDialog = ref<RoomDialog>(null);
const roomStats = ref<RoomStats | null>(null);
const roomDetailMap = ref<Record<number, RoomDetail>>({});
const environmentByRoomId = ref<Record<number, RoomEnvironmentItem[]>>({});
const detailRequests = new Map<number, Promise<RoomDetail>>();
const deleteDialogOpen = ref(false);
const deletingRoom = ref<Room | null>(null);

const roomGridExpanded = ref(false);

const toggleRoomGrid = () => {
    roomGridExpanded.value = !roomGridExpanded.value;
};

const devicesByRoomId = computed(() =>
    Object.fromEntries(
        rooms.value.map((room) => [
            room.id,
            toRoomDeviceCards(room.device ?? []),
        ]),
    ),
);

const selectedDevices = computed<RoomDeviceCard[]>(
    () => (selected.value ? devicesByRoomId.value[selected.value.id] ?? [] : []),
);

const selected = computed(
    () =>
        rooms.value.find((room) => room.id === selectedId.value) ??
        rooms.value[0],
);
const visibleRooms = computed(() => {
    const filtered = rooms.value.filter((room) => room.name.includes(keyword.value));
    if (roomGridExpanded.value) return filtered;
    return filtered.slice(0, 3);
});

/* === GSAP 房间网格入场 stagger === */
const { root, play: playRoomGrid } = useCardGridEnter({ selector: ".room-grid" });
watch(
    () => visibleRooms.value.length,
    () => {
        void playRoomGrid();
    },
);
const online = computed(() =>
    rooms.value.reduce((sum, room) => sum + room.onlineCount, 0),
);
const comfort = computed(() =>
    rooms.value.length
        ? Math.round(
              rooms.value.reduce((sum, room) => sum + room.comfort, 0) /
                  rooms.value.length,
          )
        : 0,
);

const environment = computed<RoomEnvironmentItem[]>(() => {
    const roomId = selectedId.value;
    return roomId ? environmentByRoomId.value[roomId] ?? [] : [];
});

const selectedDetail = computed<RoomDetail | null>(() => {
    if (!selectedId.value) return null;
    return roomDetailMap.value[selectedId.value] ?? null;
});

const load = async () => {
    pageLoading.value = true;

    try {
        const [result, stats] = await Promise.all([
            fetchRooms(floor.value, roomType.value),
            fetchRoomStats(),
        ]);
        rooms.value = result.items;
        roomStats.value = stats;
        selectedId.value = result.items[0]?.id;
        temperature.value = 24;
        
        const firstRoom = result.items[0];
        if (firstRoom) {
            await Promise.all([
                loadRoomDetail(firstRoom.id),
                loadEnvironment(firstRoom.id),
            ]);
        } else {
            environmentByRoomId.value = {};
        }
    } finally {
        pageLoading.value = false;
    }
};

const loadRooms = async () => {
    roomsLoading.value = true;
    try {
        const result = await fetchRooms(floor.value, roomType.value);
        rooms.value = result.items;
        if (!selectedId.value || !result.items.some((r) => r.id === selectedId.value)) {
            selectedId.value = result.items[0]?.id;
        }
    } finally {
        roomsLoading.value = false;
    }
};

const loadRoomDetail = async (roomId: number, refresh = false) => {
    if (!refresh && roomDetailMap.value[roomId]) return;

    let request = detailRequests.get(roomId);
    if (!request || refresh) {
        request = fetchRoomDetail(roomId);
        detailRequests.set(roomId, request);
    }

    try {
        const detail = await request;
        roomDetailMap.value = { ...roomDetailMap.value, [roomId]: detail };
    } finally {
        if (detailRequests.get(roomId) === request) {
            detailRequests.delete(roomId);
        }
    }
};

const loadEnvironment = async (roomId: number) => {
    try {
        const env = await getRoomEnvironmentLatest(roomId);
        const items: RoomEnvironmentItem[] = [];
        for (const [key, val] of Object.entries(env.values)) {
            const cfg = metricConfig[key];
            if (cfg) {
                const numVal = val ?? 0;
                const labelFn = metricLabels[key];
                items.push({
                    name: cfg.name,
                    value: `${numVal}${cfg.unit}`,
                    tone: cfg.tone,
                    points: "",
                    statusLabel: labelFn ? labelFn(numVal) : undefined,
                });
            }
        }
        environmentByRoomId.value = { ...environmentByRoomId.value, [roomId]: items };
    } catch {
        environmentByRoomId.value = { ...environmentByRoomId.value, [roomId]: [] };
    }
};

const quick = async (action: string) => {
    if (!selected.value) return;

    replaceRoom(await runRoomQuickAction(selected.value.id, action));
};

const selectRoom = async (room: Room) => {
    selectedId.value = room.id;
    temperature.value = 24;
    
    await Promise.all([
        loadRoomDetail(room.id).catch(() => undefined),
        loadEnvironment(room.id),
    ]);
};

const replaceRoom = (room: Room) => {
    rooms.value = rooms.value.map((item) =>
        item.id === room.id ? room : item,
    );
};

const toggleDevice = useAsyncAction(
    async (device: RoomDeviceCard) => {
        if (!selected.value) return;

        const newStatus = isDeviceActive(device.status) ? "offline" : "online";

        const updated = await updateRoomDevice(
            selected.value.id,
            device.id,
            newStatus,
        );
        replaceRoom(updated);
    },
).execute;

const handleRoomUpdated = async (room: Room) => {
  roomSaving.value = true;
  try {
    const updated = await updateRoom(room.id, {
      name: room.name,
      floor: room.floor,
      roomType: room.roomType,
      icon: room.icon ?? "room",
      themeColor: room.themeColor ?? "#3478f6",
      version: room.version ?? undefined,
    });
    replaceRoom(updated);
    ElMessage.success("房间已更新");
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      ElMessage.warning("房间已被其他会话修改，已为你重新加载最新数据");
      if (selectedId.value) {
        void loadRoomDetail(selectedId.value).then(() => {
          if (selected.value) replaceRoom(selected.value);
        }).catch(() => undefined);
      }
      return;
    }
    ElMessage.error(getErrorMessage(error, "房间更新失败"));
  } finally {
    roomSaving.value = false;
  }
};

const handleRoomCreated = async (
  payload: {
    name: string;
    floor: string;
    roomType: string;
    icon: string;
    themeColor: string;
    deviceIds: number[];
  },
) => {
  roomSaving.value = true;
  try {
    const room = await createRoom({
      name: payload.name,
      floor: payload.floor,
      roomType: payload.roomType,
      icon: payload.icon,
      themeColor: payload.themeColor,
      deviceIds: payload.deviceIds,
    });
    rooms.value = [...rooms.value, room];
    await selectRoom(room);
    activeDialog.value = null;
    ElMessage.success("房间已创建");
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      ElMessage.warning("创建失败，房间名或标识冲突，请重试");
      return;
    }
    ElMessage.error(getErrorMessage(error, "房间创建失败"));
  } finally {
    roomSaving.value = false;
  }
};

const handleRoomDeleteClick = (room: Room) => {
  deletingRoom.value = room;
  deleteDialogOpen.value = true;
};

const { pending: roomDeleting, execute: confirmDeleteRoom } = useAsyncAction(
    async () => {
        if (!deletingRoom.value) return;

        await deleteRoom(deletingRoom.value.id);
        rooms.value = rooms.value.filter((r) => r.id !== deletingRoom.value!.id);

        if (selectedId.value === deletingRoom.value.id) {
            selectedId.value = rooms.value[0]?.id;

            if (selectedId.value) {
                await loadEnvironment(selectedId.value);
            } else {
                environmentByRoomId.value = {};
            }
        }

        ElMessage.success("房间已删除");
        deleteDialogOpen.value = false;
        deletingRoom.value = null;
    },
    {
        onError: (error) =>
            ElMessage.error(getErrorMessage(error, "房间删除失败")),
    },
);

const cancelDeleteRoom = () => {
  deleteDialogOpen.value = false;
  deletingRoom.value = null;
};

useAuthenticatedLoader(load);
</script>

<template>
    <div class="app-page-layout">
        <main ref="root" class="workspace page-shell page-enter">
            <PageHeader
                title="房间控制"
                description="房间设备与环境控制"
                icon="room"
                tone="var(--color-teal-600)"
                soft="var(--color-teal-soft)"
            >
                <div class="page-tools">
                    <label><SvgIcon name="search" size="sm" /><input v-model="keyword" placeholder="搜索房间" /></label>
                    <select v-model="floor" @change="loadRooms">
                        <option value="">全部楼层</option><option>1F</option><option>2F</option>
                    </select>
                    <select v-model="roomType" @change="loadRooms">
                        <option value="">全部类型</option><option value="living">客厅</option><option value="bedroom">卧室</option><option value="study">书房</option>
                    </select>
                    <button class="primary" type="button" @click="activeDialog = 'create'"><SvgIcon name="plus" size="sm" />添加房间</button>
                </div>
            </PageHeader>

            <Transition name="stats-fade">
                <div v-if="!roomGridExpanded" key="stats">
                    <RoomStatsGrid
                        :room-count="rooms.length"
                        :online-count="online"
                        :comfort-score="comfort"
                        :room-count-change="roomStats?.roomCountChange ?? 0"
                        :online-rate="roomStats?.onlineRate ?? 0"
                        :alert-count="roomStats?.alertCount ?? 0"
                        :pending-alert-count="roomStats?.pendingAlertCount ?? 0"
                    />
                </div>
            </Transition>

            <div v-if="rooms.length === 0 && !pageLoading && !roomsLoading" class="room-empty-state">
                <SvgIcon name="room" size="lg" />
                <h3>暂无房间数据</h3>
                <p>请添加您的第一个房间，开始管理智能家居设备</p>
                <button class="primary" type="button" @click="activeDialog = 'create'">
                    <SvgIcon name="plus" size="sm" />添加房间
                </button>
            </div>

            <TransitionGroup
                v-if="rooms.length > 0"
                tag="section"
                :class="['room-grid', { 'room-grid-expanded': roomGridExpanded }]"
                name="room-grid"
                appear
            >
                <RoomCard
                    v-for="room in visibleRooms"
                    :key="room.id"
                    :room="room"
                    :selected="selected?.id === room.id"
                    :devices="devicesByRoomId[room.id] ?? []"
                    @select="selectRoom"
                    @toggle="toggleDevice"
                    @delete="handleRoomDeleteClick"
                />
            </TransitionGroup>

            <button v-if="rooms.length > 3" class="room-view-all" type="button" @click="toggleRoomGrid">
                {{ roomGridExpanded ? '收起房间' : `查看全部房间（${rooms.length}）` }}
                <span class="chevron-icon" :class="{ 'is-expanded': roomGridExpanded }">
                    <SvgIcon name="chevron-down" />
                </span>
            </button>

            <div class="room-panel-wrapper">
                <RoomControlPanel
                    :rooms="rooms"
                    :selected="selected"
                    :loading="pageLoading || roomsLoading"
                    :devices="selectedDevices"
                    :environment="environment"
                    :temperature="temperature"
                    :active-category="activeCategory"
                    :current-scene="selectedDetail?.currentScene ?? undefined"
                    @select="selectRoom"
                    @toggle="toggleDevice"
                    @update:temperature="temperature = $event"
                    @update:active-category="activeCategory = $event"
                    @open="activeDialog = $event"
                />
            </div>
        </main>

        <BaseCollapsibleRail
            :title="`${selected?.name ?? '房间'}助手`"
            :subtitle="selected ? `● ${selected.onlineCount}/${selected.deviceCount} 台在线 · 舒适度 ${selected.comfort}` : ''"
            storage-key="orion.room-assistant-rail-collapsed"
            expanded-width="344px"
        >
            <template #collapsed>
                <div class="rail-collapsed-content">
                    <img
                        src="/orion-sidebar-icon.svg"
                        alt="助手"
                        class="rail-mini-avatar"
                    />
                    <span
                        v-if="selected"
                        class="rail-mini-dot"
                        :title="`${selected.name} · ${selected.onlineCount} 台在线`"
                    ></span>
                    <span
                        v-if="environment[0]"
                        class="rail-mini-value"
                        :title="environment[0].value"
                    >{{ environment[0].value }}</span>
                    <span
                        v-if="selected"
                        class="rail-mini-num"
                        :title="`${selected.onlineCount} 台设备在线`"
                    >{{ selected.onlineCount }}</span>
                    <span
                        v-if="environment.some(e => e.statusLabel === '差' || e.statusLabel === '偏热' || e.statusLabel === '潮湿')"
                        class="rail-mini-alert"
                        title="有告警"
                    >!</span>
                </div>
            </template>

            <RoomDetailPanel
                :room="selected ?? null"
                :environment="environment"
                :current-scene="selectedDetail?.currentScene ?? undefined"
                :recent-activity="selectedDetail?.recentActivity ?? undefined"
                :recent-activity-time="selectedDetail?.recentActivityTime ?? undefined"
                @quick="quick"
                @open="activeDialog = $event"
            />
        </BaseCollapsibleRail>

        <RoomControlDialogs
            v-model="activeDialog"
            :room="selected"
            :submitting="roomSaving"
            @create="handleRoomCreated"
            @update="handleRoomUpdated"
        />

        <ConfirmActionDialog
            v-if="deleteDialogOpen"
            :model-value="deleteDialogOpen"
            :loading="roomDeleting"
            title="删除房间"
            description="此操作将删除房间及其关联的设备绑定。"
            warning="删除后将无法在房间控制、设备管理和快捷操作中继续管理该房间及其设备。"
            footer-hint="确认后会立即调用后端删除接口。"
            @cancel="cancelDeleteRoom"
            @confirm="confirmDeleteRoom"
            @update:model-value="deleteDialogOpen = $event"
        >
            <section v-if="deletingRoom" class="delete-dialog-body">
                <div class="delete-room-card" :style="{ '--theme-color': deletingRoom.themeColor || '#3478f6' }">
                    <span class="delete-room-avatar">
                        <SvgIcon name="room" />
                    </span>
                    <div class="delete-room-info">
                        <strong class="delete-room-name">{{ deletingRoom.name }}</strong>
                        <span class="delete-room-detail">
                            <SvgIcon name="home" size="sm" />{{ deletingRoom.floor }}
                            <span class="detail-sep"></span>
                            <SvgIcon name="online-device" size="sm" />{{ deletingRoom.onlineCount }}/{{ deletingRoom.deviceCount }} 台在线
                        </span>
                    </div>
                </div>
            </section>
        </ConfirmActionDialog>
    </div>
</template>

<style scoped>
.workspace {
    min-height: 0;
    flex: 1;
    overflow-x: hidden;
    overflow-y: auto;
    overscroll-behavior: contain;
    scrollbar-gutter: stable;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
}
.page-tools { display: flex; align-items: center; gap: 8px; }
.page-tools label { display: flex; min-width: 180px; height: 34px; align-items: center; gap: 6px; border: 1px solid var(--color-border); border-radius: 8px; background: var(--color-card-bg); padding: 0 9px; color: var(--color-text-tertiary); }
.page-tools input { min-width: 0; flex: 1; border: 0; outline: 0; font-size: 14px; }
.page-tools select { height: 34px; padding-left: 8px; border: 1px solid var(--color-border); border-radius: 8px; background: var(--color-card-bg); color: var(--color-text-primary); font-size: 14px; }

.page-tools select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}
.primary { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; background: var(--color-primary-600) !important; color: white !important; }
.page-tools .primary { height: 34px; padding: 0 12px; font-size: 11px; font-weight: 800; }

.room-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }

.room-grid-expanded {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
}

/* TransitionGroup room-grid animations */
/* 入场由 GSAP stagger 接管（useCardGridEnter），CSS 不再维护 nth-child 延迟表 */
.room-grid-leave-active {
    animation: room-grid-leave 180ms var(--motion-ease-in) both;
}
.room-grid-move {
    transition: transform 280ms var(--motion-ease-out);
}

@keyframes room-grid-leave {
    from { opacity: 1; transform: translateY(0) scale(1); }
    to { opacity: 0; transform: translateY(-8px) scale(0.96); }
}

.room-view-all {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    width: fit-content;
    margin: 0 auto;
    color: var(--color-primary-600);
    font-size: 13px;
    font-weight: 900;
    cursor: pointer;
    border: none;
    background: none;
    padding: 4px 8px;
    border-radius: 6px;
    transition: background-color 150ms;
}

.room-view-all:hover {
    background: var(--color-primary-50);
}

.chevron-icon {
    display: inline-flex;
    transition: transform 280ms var(--motion-ease-out);
}

.chevron-icon.is-expanded {
    transform: rotate(180deg);
}

.room-panel-wrapper {
    flex: 0 0 auto;
    min-height: max-content;
    display: flex;
    flex-direction: column;
}

.room-panel-wrapper:deep(.quick-control) {
    flex: 0 0 auto;
    min-height: max-content;
    overflow: visible;
}

/* Cross-fade for room panel switch */
.room-panel-wrapper:deep(.control-content) {
    animation: panel-enter 240ms var(--motion-ease) both;
}

.room-empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    flex: 1;
    min-height: 300px;
    border: 1px dashed var(--color-border);
    border-radius: 18px;
    background: var(--color-card-bg);
    color: var(--color-text-tertiary);
}
.room-empty-state svg {
    width: 48px;
    height: 48px;
    color: var(--color-primary-300);
}
.room-empty-state h3 {
    margin: 0;
    color: var(--color-text-secondary);
    font-size: 18px;
    font-weight: 900;
}
.room-empty-state p {
    margin: 0;
    font-size: 14px;
}
.room-empty-state button {
    margin-top: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 800;
}

@media (max-width: 1450px) {
    .page-header { display: grid; }
    .room-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
    .room-grid { grid-template-columns: 1fr; }
    .room-grid-expanded {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 620px) {
    .page-tools label { min-width: 120px; }
    .page-tools select:not(:first-of-type) { display: none; }
}

/* === 删除房间弹窗 === */
.delete-dialog-body {
    padding: 4px 0;
}

.delete-room-card {
    display: flex;
    align-items: center;
    gap: 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 14px 16px;
}

.delete-room-avatar {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--theme-color, #3478f6) 80%, white),
        color-mix(in srgb, var(--theme-color, #3478f6) 50%, white)
    );
    color: #fff;
    box-shadow: 0 4px 12px color-mix(in srgb, var(--theme-color, #3478f6) 24%, transparent);
}

.delete-room-avatar svg {
    width: 22px;
    height: 22px;
}

.delete-room-info {
    min-width: 0;
    flex: 1;
    display: grid;
    gap: 4px;
}

.delete-room-name {
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
    line-height: 1.3;
}

.delete-room-detail {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}

.delete-room-detail svg {
    color: var(--color-text-muted);
}

.detail-sep {
    display: inline-block;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--color-border);
}

@media (prefers-reduced-motion: reduce) {
    .room-grid-leave-active {
        animation: none;
    }
    .room-grid-move {
        transition: none;
    }
    .room-panel-wrapper:deep(.control-content) {
        animation: none;
    }
    .room-panel-wrapper:deep(.quick-control) {
        transition: none;
    }
    .chevron-icon {
        transition: none;
    }
}
/* === 统计卡片折叠动画（Vue Transition） === */
.stats-fade-leave-active {
    transition: opacity 180ms var(--motion-ease-in), transform 180ms var(--motion-ease-in);
}
.stats-fade-enter-active {
    transition: opacity 250ms var(--motion-ease-out), transform 250ms var(--motion-ease-out);
}
.stats-fade-leave-to {
    opacity: 0;
    transform: translateY(-6px);
}
.stats-fade-enter-from {
    opacity: 0;
    transform: translateY(6px);
}

@media (prefers-reduced-motion: reduce) {
    .stats-fade-leave-active,
    .stats-fade-enter-active {
        transition: none;
    }
}

/* === 可折叠房间助手侧栏 === */
@media (min-width: 1024px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

@media (min-width: 1024px) and (max-width: 1279px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

/* === 收起状态指示器 === */
.rail-collapsed-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    padding-top: 4px;
}

.rail-mini-avatar {
    width: 22px;
    height: 22px;
    border-radius: 50%;
}

.rail-mini-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--color-success);
    animation: pulse-dot 2s var(--motion-ease) infinite;
}

.rail-mini-value {
    color: var(--color-text-primary);
    font-size: 11px;
    font-weight: 900;
    line-height: 1;
    text-align: center;
}

.rail-mini-num {
    display: grid;
    min-width: 20px;
    height: 20px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-surface-subtle);
    color: var(--color-text-secondary);
    font-size: 10px;
    font-weight: 900;
}

.rail-mini-alert {
    display: grid;
    min-width: 18px;
    height: 18px;
    place-items: center;
    border-radius: 999px;
    background: var(--color-danger);
    color: #fff;
    font-size: 10px;
    font-weight: 900;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

@media (prefers-reduced-motion: reduce) {
    .rail-mini-dot {
        animation: none;
    }
}
</style>
