<script setup lang="ts">
import { computed, ref } from "vue";
import { useAuthStore } from "../stores/auth";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { ElMessage } from "element-plus";
import {
  createRoom,
  fetchRooms,
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
} from "../types/room";
import type { RoomEnvironmentItem } from "../components/rooms/RoomDetailPanel.vue";
import { commonDevices } from "../mock/rooms";

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

const selected = computed(
    () =>
        rooms.value.find((room) => room.id === selectedId.value) ??
        rooms.value[0],
);
const visibleRooms = computed(() =>
    rooms.value.filter((room) => room.name.includes(keyword.value)).slice(0, 3),
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
    const room = selected.value;

    if (!room) return [];

    return [
        { name: "温度", value: `${room.temperature}°C`, tone: "blue", points: "1,17 12,9 22,14 32,5 43,12 54,3 65,8" },
        { name: "湿度", value: `${room.humidity}%`, tone: "blue", points: "1,16 12,18 22,10 32,14 43,6 54,9 65,3" },
        { name: "PM2.5", value: `${room.pm25} μg/m³`, tone: "green", points: "1,18 12,13 22,16 32,7 43,11 54,3 65,10" },
        { name: "光照", value: `${room.illuminance} lux`, tone: "orange", points: "1,17 12,8 22,15 32,2 43,16 54,8 65,17" },
        { name: "噪音", value: `${room.noise} dB`, tone: "purple", points: "1,17 12,13 22,16 32,9 43,12 54,8 65,2" },
    ];
});

const load = async () => {
    if (!authStore.isAuthenticated) {
        authStore.openLogin();
        return;
    }

    loading.value = true;

    try {
        const result = await fetchRooms(floor.value, roomType.value);
        rooms.value = result.items;
        selectedId.value = result.items[0]?.id;
        temperature.value = Math.round(result.items[0]?.temperature ?? 24);
    } finally {
        loading.value = false;
    }
};

const quick = async (action: string) => {
    if (!selected.value) return;

    replaceRoom(await runRoomQuickAction(selected.value.id, action));
};

const selectRoom = (room: Room) => {
    selectedId.value = room.id;
    temperature.value = Math.round(room.temperature);
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
            !selected.value.deviceStates[device.key],
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
    <div class="contents">
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
                :room-count="rooms.length"
                :online-count="online"
                :comfort-score="comfort"
            />

            <section class="room-grid card-grid-enter">
                <RoomCard
                    v-for="room in visibleRooms"
                    :key="room.id"
                    :room="room"
                    :selected="selected?.id === room.id"
                    :devices="commonDevices"
                    @select="selectRoom"
                    @toggle="toggleDevice"
                />
            </section>

            <RoomControlPanel
                :rooms="rooms"
                :selected="selected"
                :loading="loading"
                :devices="commonDevices"
                :environment="environment"
                :temperature="temperature"
                :active-category="activeCategory"
                @select="selectRoom"
                @toggle="toggleDevice"
                @update:temperature="temperature = $event"
                @update:active-category="activeCategory = $event"
                @open="activeDialog = $event"
            />
        </main>

        <RoomDetailPanel
            v-if="selected"
            :room="selected"
            :environment="environment"
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
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
}
.page-tools { display: flex; align-items: center; gap: 8px; }
.page-tools label { display: flex; min-width: 220px; height: 38px; align-items: center; gap: 8px; border: 1px solid var(--color-border); border-radius: 9px; background: var(--color-card-bg); padding: 0 11px; color: var(--color-text-tertiary); }
.page-tools input { min-width: 0; flex: 1; border: 0; outline: 0; }
.page-tools select { height: 38px; padding-left: 10px; border: 1px solid var(--color-border); border-radius: 9px; background: var(--color-card-bg); color: var(--color-text-primary); }

.page-tools select option {
    background: var(--color-card-bg);
    color: var(--color-text-primary);
}
.primary { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; background: var(--color-primary-600) !important; color: white !important; }
.page-tools .primary { height: 38px; padding: 0 14px; font-size: 12px; font-weight: 800; }

.room-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }

@media (max-width: 1450px) {
    .page-header { display: grid; }
    .room-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
    .room-grid { grid-template-columns: 1fr; }
}
</style>
