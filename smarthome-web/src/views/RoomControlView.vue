<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { roomService } from "../services/room";
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

const commonDevices: RoomDeviceCard[] = [
    { key: "light", icon: "light", name: "吸顶灯", detail: "亮度 80%" },
    { key: "television", icon: "device-management", name: "电视", detail: "音量 30%" },
    { key: "airConditioner", icon: "air-conditioner", name: "空调", detail: "24°C" },
    { key: "airPurifier", icon: "sensor", name: "空气净化器", detail: "风速 自动" },
    { key: "socket", icon: "plug", name: "智能插座", detail: "" },
];

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
    loading.value = true;

    try {
        const result = await roomService.list(floor.value, roomType.value);
        rooms.value = result.items;
        selectedId.value = result.items[0]?.id;
        temperature.value = Math.round(result.items[0]?.temperature ?? 24);
    } finally {
        loading.value = false;
    }
};

const quick = async (action: string) => {
    if (!selected.value) return;

    replaceRoom(await roomService.runQuickAction(selected.value.id, action));
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
        await roomService.updateDevice(
            selected.value.id,
            device.key,
            !selected.value.deviceStates[device.key],
        ),
    );
};

const handleRoomUpdated = (room: Room) => replaceRoom(room);

const handleRoomCreated = (
    payload: Pick<Room, "name" | "floor" | "roomType">,
) => {
    const room: Room = {
        ...payload,
        id: Math.max(0, ...rooms.value.map((item) => item.id)) + 1,
        imageUrl: null,
        area: 16,
        comfort: 81,
        temperature: 24,
        humidity: 55,
        pm25: 18,
        illuminance: 320,
        noise: 42,
        deviceCount: 6,
        onlineCount: 6,
        deviceStates: {
            light: true,
            airConditioner: true,
            curtain: true,
            socket: true,
        },
        updatedAt: new Date().toISOString(),
    };

    rooms.value = [...rooms.value, room];
    selectRoom(room);
};

onMounted(() => void load());
</script>

<template>
    <div class="contents">
        <main class="workspace page-enter">
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
                <div class="room-scroll" v-if="visibleRooms.length">
                    <RoomCard
                        v-for="room in visibleRooms"
                        :key="room.id"
                        :room="room"
                        :selected="selected?.id === room.id"
                        :devices="commonDevices"
                        @select="selectRoom"
                        @toggle="toggleDevice"
                    />
                </div>
                <p v-else class="room-empty">暂无匹配的房间</p>
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
    min-width: 0;
    min-height: 0;
    overflow-y: auto;
    border: 1px solid var(--color-border);
    border-radius: 18px;
    background: var(--color-page-bg);
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
}
.page-tools { display: flex; align-items: center; gap: 8px; }
.page-tools label { display: flex; min-width: 220px; height: 38px; align-items: center; gap: 8px; border: 1px solid var(--color-border); border-radius: 9px; background: var(--color-card-bg); padding: 0 11px; color: var(--color-text-tertiary); }
.page-tools input { min-width: 0; flex: 1; border: 0; outline: 0; }
.page-tools select { height: 38px; padding-left: 10px; }
.primary { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; background: var(--color-primary-600) !important; color: white !important; }
.page-tools .primary { height: 38px; padding: 0 14px; font-size: 12px; font-weight: 800; }

.room-grid {
    position: relative;
}
.room-scroll {
    display: flex;
    gap: 12px;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
}
.room-scroll::-webkit-scrollbar {
    height: 4px;
}
.room-scroll::-webkit-scrollbar-track {
    border-radius: 2px;
    background: var(--color-surface-subtle);
}
.room-scroll::-webkit-scrollbar-thumb {
    border-radius: 2px;
    background: var(--color-border-strong);
}
.room-scroll > * {
    min-width: calc(33.333% - 8px);
    scroll-snap-align: start;
}
.room-empty {
    display: grid;
    min-height: 120px;
    place-items: center;
    border: 1px dashed var(--color-border-strong);
    border-radius: 14px;
    color: var(--color-text-tertiary);
    font-size: 13px;
    font-weight: 800;
}

@media (max-width: 1450px) {
    .page-header { display: grid; }
    .room-scroll > * {
        min-width: calc(50% - 6px);
    }
}

@media (max-width: 900px) {
    .room-scroll > * {
        min-width: calc(100% - 0px);
    }
}
</style>
