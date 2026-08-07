<script setup lang="ts">
import { computed, ref } from "vue";
import { useAuthStore } from "../stores/auth";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { ElMessage } from "element-plus";
import {
  createRoom,
  fetchRooms,
  fetchRoomDetail,
  fetchRoomStats,
  getRoomEnvironmentLatest,
  runRoomQuickAction,
  updateRoom,
  updateRoomDevice,
} from "../api/room";
import SvgIcon from "../components/common/SvgIcon.vue";
import PageHeader from "../components/common/PageHeader.vue";
import RoomControlDialogs, {
    type RoomDialog,
} from "../components/rooms/RoomControlDialogs.vue";
import RoomStatsGrid from "../components/rooms/RoomStatsGrid.vue";
import RoomCard from "../components/rooms/RoomCard.vue";
import RoomControlPanel from "../components/rooms/RoomControlPanel.vue";
import RoomDetailPanel from "../components/rooms/RoomDetailPanel.vue";
import type {
    Room,
    RoomDeviceCard,
    RoomDetail,
    RoomStats,
} from "../types/room";
import type { RoomEnvironmentItem } from "../components/rooms/RoomDetailPanel.vue";

const deviceCardConfig: Record<string, { icon: string; name: string }> = {
    light: { icon: "light", name: "吸顶灯" },
    television: { icon: "device-management", name: "电视" },
    airConditioner: { icon: "air-conditioner", name: "空调" },
    airPurifier: { icon: "sensor", name: "空气净化器" },
    socket: { icon: "plug", name: "智能插座" },
    curtain: { icon: "curtain", name: "窗帘" },
    camera: { icon: "camera", name: "摄像头" },
    lock: { icon: "lock", name: "门锁" },
};

const deriveDevices = (room: Room): RoomDeviceCard[] => {
    return Object.keys(deviceCardConfig).map((key) => {
        const config = deviceCardConfig[key];
        return {
            key,
            icon: config?.icon ?? "device-management",
            name: config?.name ?? key,
            detail: "",
        };
    });
};

const authStore = useAuthStore();

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
    if (!authStore.isAuthenticated) {
        authStore.openLogin();
        return;
    }

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
        
        // 加载所有房间的详情
        const detailPromises = result.items.map((room) =>
            fetchRoomDetail(room.id).then((detail) => ({ id: room.id, detail })),
        );
        const details = await Promise.all(detailPromises);
        roomDetailMap.value = Object.fromEntries(
            details.map(({ id, detail }) => [id, detail]),
        );
        
        // 加载选中房间的环境数据
        if (result.items[0]) {
            await loadEnvironment(result.items[0].id);
        }
    } finally {
        loading.value = false;
    }
};

const loadEnvironment = async (roomId: number) => {
    try {
        const env = await getRoomEnvironmentLatest(roomId);
        environmentData.value = [
            { name: "温度", value: `${env.values.temperature ?? 0}°C`, tone: "blue", points: "1,17 12,9 22,14 32,5 43,12 54,3 65,8" },
            { name: "湿度", value: `${env.values.humidity ?? 0}%`, tone: "blue", points: "1,16 12,18 22,10 32,14 43,6 54,9 65,3" },
            { name: "PM2.5", value: `${env.values.pm25 ?? 0} μg/m³`, tone: "green", points: "1,18 12,13 22,16 32,7 43,11 54,3 65,10" },
            { name: "光照", value: `${env.values.illuminance ?? 0} lux`, tone: "orange", points: "1,17 12,8 22,15 32,2 43,16 54,8 65,17" },
            { name: "噪音", value: `${env.values.noise ?? 0} dB`, tone: "purple", points: "1,17 12,13 22,16 32,9 43,12 54,8 65,2" },
        ];
    } catch {
        // 环境接口不可用时，使用房间数据构造
        const room = rooms.value.find((r) => r.id === roomId);
        if (room) {
            environmentData.value = [
                { name: "温度", value: `--°C`, tone: "blue", points: "" },
                { name: "湿度", value: `--%`, tone: "blue", points: "" },
                { name: "PM2.5", value: `-- μg/m³`, tone: "green", points: "" },
                { name: "光照", value: `-- lux`, tone: "orange", points: "" },
                { name: "噪音", value: `-- dB`, tone: "purple", points: "" },
            ];
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
    
    // 加载房间详情
    try {
        const detail = await fetchRoomDetail(room.id);
        roomDetailMap.value = { ...roomDetailMap.value, [room.id]: detail };
    } catch {
        // 忽略详情加载失败
    }
    
    // 加载环境数据
    await loadEnvironment(room.id);
};

const replaceRoom = (room: Room) => {
    rooms.value = rooms.value.map((item) =>
        item.id === room.id ? room : item,
    );
};

const toggleDevice = async (device: RoomDeviceCard) => {
    if (!selected.value) return;

    replaceRoom(
        await updateRoomDevice(
            selected.value.id,
            device.key,
            true,
        ),
    );
};

const handleRoomUpdated = async (room: Room) => {
  loading.value = true;
  try {
    const updated = await updateRoom(room.id, {
      name: room.name,
      floor: room.floor,
      room_type: room.roomType,
      icon: (room as any).icon ?? "room",
      theme_color: (room as any).themeColor ?? "#3478f6",
      version: (room as any).version ?? undefined,
    });
    replaceRoom(updated);
    ElMessage.success("房间已更新");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "房间更新失败");
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
    selectRoom(room);
    ElMessage.success("房间已创建");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "房间创建失败");
  } finally {
    loading.value = false;
  }
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
</style>
