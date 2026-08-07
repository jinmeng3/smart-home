<script setup lang="ts">
import { computed, ref } from "vue";
import { useAsyncAction } from "../composables/useAsyncAction";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { ElMessage } from "element-plus";
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
import RoomControlDialogs, {
    type RoomDialog,
} from "../components/rooms/RoomControlDialogs.vue";
import RoomStatsGrid from "../components/rooms/RoomStatsGrid.vue";
import RoomCard from "../components/rooms/RoomCard.vue";
import RoomControlPanel from "../components/rooms/RoomControlPanel.vue";
import RoomDetailPanel from "../components/rooms/RoomDetailPanel.vue";
import { getDeviceTypeIcon } from "../components/device/deviceMeta";
import type {
    Room,
    RoomDeviceCard,
    RoomDetail,
    RoomStats,
} from "../types/room";
import type { RoomEnvironmentItem } from "../components/rooms/RoomDetailPanel.vue";
import { getErrorMessage } from "../utils/error";

const deriveDevices = (room: Room): RoomDeviceCard[] => {
    if (!room.device || room.device.length === 0) return [];
    return room.device.map((d) => ({
        id: d.id,
        key: d.type,
        icon: d.icon || getDeviceTypeIcon(d.type),
        color: d.color,
        name: d.name,
        detail: d.brand || "",
        status: d.status as RoomDeviceCard["status"],
    }));
};

const rooms = ref<Room[]>([]);
const selectedId = ref<number>();
const loading = ref(false);
const activeCategory = ref("全部设备");
const temperature = ref(24);
const keyword = ref("");
const floor = ref("");
const roomType = ref("");
const activeDialog = ref<RoomDialog>(null);
const roomStats = ref<RoomStats | null>(null);
const roomDetailMap = ref<Record<number, RoomDetail>>({});
const environmentData = ref<RoomEnvironmentItem[]>([]);
const detailRequests = new Map<number, Promise<RoomDetail>>();
const deleteDialogOpen = ref(false);
const deletingRoom = ref<Room | null>(null);

const roomGridExpanded = ref(false);

const toggleRoomGrid = () => {
    roomGridExpanded.value = !roomGridExpanded.value;
};

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
    return environmentData.value;
});

const selectedDetail = computed<RoomDetail | null>(() => {
    if (!selectedId.value) return null;
    return roomDetailMap.value[selectedId.value] ?? null;
});

const load = async () => {
    loading.value = true;

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
            environmentData.value = [];
        }
    } finally {
        loading.value = false;
    }
};

const metricConfig: Record<string, { name: string; unit: string; tone: string }> = {
    temperature: { name: "温度", unit: "°C", tone: "blue" },
    humidity: { name: "湿度", unit: "%", tone: "blue" },
    pm25: { name: "PM2.5", unit: " μg/m³", tone: "green" },
    illuminance: { name: "光照", unit: " lux", tone: "orange" },
    noise: { name: "噪音", unit: " dB", tone: "purple" },
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
                items.push({
                    name: cfg.name,
                    value: `${val ?? 0}${cfg.unit}`,
                    tone: cfg.tone,
                    points: "",
                });
            }
        }
        if (selectedId.value === roomId) {
            environmentData.value = items;
        }
    } catch {
        if (selectedId.value === roomId) {
            environmentData.value = [];
        }
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

        const newStatus = device.status === "online" || device.status === "running" ? "offline" : "online";

        const updated = await updateRoomDevice(
            selected.value.id,
            device.id,
            newStatus,
        );
        replaceRoom(updated);
    },
).run;

const handleRoomUpdated = async (room: Room) => {
  loading.value = true;
  try {
    const updated = await updateRoom(room.id, {
      name: room.name,
      floor: room.floor,
      room_type: room.roomType,
      icon: room.icon ?? "room",
      theme_color: room.themeColor ?? "#3478f6",
      version: room.version ?? undefined,
    });
    replaceRoom(updated);
    ElMessage.success("房间已更新");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "房间更新失败"));
  } finally {
    loading.value = false;
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
  loading.value = true;
  try {
    const room = await createRoom({
      name: payload.name,
      floor: payload.floor,
      room_type: payload.roomType,
      icon: payload.icon,
      theme_color: payload.themeColor,
      device_ids: payload.deviceIds,
    });
    rooms.value = [...rooms.value, room];
    await selectRoom(room);
    ElMessage.success("房间已创建");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "房间创建失败"));
  } finally {
    loading.value = false;
  }
};

const handleRoomDeleteClick = (room: Room) => {
  deletingRoom.value = room;
  deleteDialogOpen.value = true;
};

const { loading: roomDeleting, run: confirmDeleteRoom } = useAsyncAction(
    async () => {
        if (!deletingRoom.value) return;

        await deleteRoom(deletingRoom.value.id);
        rooms.value = rooms.value.filter((r) => r.id !== deletingRoom.value!.id);

        if (selectedId.value === deletingRoom.value.id) {
            selectedId.value = rooms.value[0]?.id;

            if (selectedId.value) {
                await loadEnvironment(selectedId.value);
            } else {
                environmentData.value = [];
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
        <main class="workspace page-shell page-enter">
            <PageHeader title="房间控制" description="按房间查看设备状态、环境数据与快捷控制">
                <div class="page-tools">
                    <label><SvgIcon name="search" size="sm" /><input v-model="keyword" placeholder="搜索房间、设备或场景" /></label>
                    <select v-model="floor" @change="load">
                        <option value="">全部楼层</option><option>1F</option><option>2F</option>
                    </select>
                    <select v-model="roomType" @change="load">
                        <option value="">全部类型</option><option value="living">客厅</option><option value="bedroom">卧室</option><option value="study">书房</option>
                    </select>
                    <button class="primary" type="button" @click="activeDialog = 'create'"><SvgIcon name="plus" size="sm" />添加房间</button>
                </div>
            </PageHeader>

            <RoomStatsGrid
                v-show="!roomGridExpanded"
                :room-count="rooms.length"
                :online-count="online"
                :comfort-score="comfort"
                :room-count-change="roomStats?.room_count_change ?? 0"
                :online-rate="roomStats?.online_rate ?? 0"
                :alert-count="roomStats?.alert_count ?? 0"
                :pending-alert-count="roomStats?.pending_alert_count ?? 0"
            />

            <div v-if="rooms.length === 0 && !loading" class="room-empty-state">
                <SvgIcon name="room" size="lg" />
                <h3>暂无房间数据</h3>
                <p>请添加您的第一个房间，开始管理智能家居设备</p>
                <button class="primary" type="button" @click="activeDialog = 'create'">
                    <SvgIcon name="plus" size="sm" />添加房间
                </button>
            </div>

            <section v-if="rooms.length > 0" :class="['room-grid', 'card-grid-enter', { 'room-grid-expanded': roomGridExpanded }]">
                <RoomCard
                    v-for="room in visibleRooms"
                    :key="room.id"
                    :room="room"
                    :selected="selected?.id === room.id"
                    :devices="deriveDevices(room)"
                    @select="selectRoom"
                    @toggle="toggleDevice"
                    @delete="handleRoomDeleteClick"
                />
            </section>

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
                    :loading="loading"
                    :devices="selected ? deriveDevices(selected) : []"
                    :environment="environment"
                    :temperature="temperature"
                    :active-category="activeCategory"
                    @select="selectRoom"
                    @toggle="toggleDevice"
                    @update:temperature="temperature = $event"
                    @update:active-category="activeCategory = $event"
                    @open="activeDialog = $event"
                />
            </div>
        </main>

        <RoomDetailPanel
            :room="selected ?? null"
            :environment="environment"
            :current-scene="selectedDetail?.current_scene ?? undefined"
            :recent-activity="selectedDetail?.recent_activity ?? undefined"
            :recent-activity-time="selectedDetail?.recent_activity_time ?? undefined"
            @quick="quick"
            @open="activeDialog = $event"
        />

        <RoomControlDialogs
            v-model="activeDialog"
            :room="selected"
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
                <div class="delete-device-summary">
                    <span class="delete-device-thumb" aria-hidden="true">
                        <SvgIcon name="room" />
                    </span>
                    <div>
                        <strong>{{ deletingRoom.name }}</strong>
                        <p class="delete-room-meta">
                            <span><SvgIcon name="home" size="sm" />{{ deletingRoom.floor }}</span>
                            <span class="meta-sep"></span>
                            <span><SvgIcon name="online-device" size="sm" />{{ deletingRoom.onlineCount }}/{{ deletingRoom.deviceCount }} 个设备在线</span>
                        </p>
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
    overflow: hidden;
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
    max-height: 320px;
    overflow-y: auto;
    scrollbar-gutter: stable;
}

.room-grid-expanded::-webkit-scrollbar {
    width: 6px;
}

.room-grid-expanded::-webkit-scrollbar-thumb {
    border-radius: 3px;
    background: var(--color-border);
}

.room-grid-expanded::-webkit-scrollbar-track {
    background: transparent;
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
    transition: transform 300ms ease;
}

.chevron-icon.is-expanded {
    transform: rotate(180deg);
}

.room-panel-wrapper {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
}

.room-panel-wrapper:deep(.quick-control) {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
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
}

@media (max-width: 720px) {
    .room-grid-expanded {
        max-height: 280px;
    }
}

/* ── 删除房间弹窗 ─────────────────────────────── */
.delete-dialog-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 22px;
    border-bottom: 1px solid var(--color-danger-border);
    background: linear-gradient(
        180deg,
        var(--color-card-bg),
        var(--color-danger-soft)
    );
}
.delete-dialog-icon {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    background: var(--color-danger-soft);
    color: var(--color-danger);
}
.delete-dialog-header h2,
.delete-dialog-header p {
    margin: 0;
}
.delete-dialog-header h2 {
    color: var(--color-text-primary);
    font-size: 20px;
    font-weight: 900;
}
.delete-dialog-header p {
    margin-top: 4px;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 700;
}
.delete-dialog-close {
    display: grid;
    width: 34px;
    height: 34px;
    margin-left: auto;
    place-items: center;
    border-radius: 8px;
    color: var(--color-text-tertiary);
}
.delete-dialog-close:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}
.delete-dialog-body {
    display: grid;
    gap: 14px;
    padding: 20px 22px;
}
.delete-device-summary {
    display: flex;
    align-items: center;
    gap: 12px;
}
.delete-device-thumb {
    display: grid;
    width: 44px;
    height: 44px;
    flex: 0 0 44px;
    place-items: center;
    border-radius: 12px;
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.delete-device-summary strong {
    color: var(--color-text-primary);
    font-size: 16px;
    font-weight: 900;
}
.delete-device-summary p {
    margin: 4px 0 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}
.delete-room-meta {
    display: flex;
    align-items: center;
    gap: 4px;
    margin: 4px 0 0;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}
.delete-room-meta svg {
    color: var(--color-text-muted);
    margin-right: 2px;
}
.delete-room-meta .meta-sep {
    display: inline-block;
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--color-border);
}
.delete-dialog-warning {
    margin: 0;
    border: 1px solid var(--color-danger-border);
    border-radius: 10px;
    background: var(--color-danger-soft);
    padding: 12px 14px;
    color: var(--color-danger);
    line-height: 1.6;
}
.delete-dialog-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 14px 22px;
    border-top: 1px solid var(--color-border-subtle);
    background: var(--color-workspace-background);
}
.delete-dialog-footer span {
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 700;
}
.delete-dialog-footer > div {
    display: flex;
    gap: 8px;
}
.delete-cancel-button,
.delete-confirm-button {
    display: inline-flex;
    height: 38px;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border-radius: 8px;
    padding: 0 16px;
    font-size: 13px;
    font-weight: 900;
}
.delete-cancel-button {
    border: 1px solid var(--color-border-default);
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
}
.delete-confirm-button {
    border: 1px solid var(--color-danger);
    background: var(--color-danger);
    color: var(--color-text-on-primary);
}
.delete-cancel-button:hover {
    background: var(--color-surface-hover);
}
.delete-confirm-button:hover {
    background: color-mix(in srgb, var(--color-danger) 88%, black);
}
.delete-confirm-button:disabled svg {
    animation: spin 1s linear infinite;
}
@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}
</style>
