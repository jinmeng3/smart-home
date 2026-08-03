<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { roomService } from "../services/room";
import SvgIcon from "../components/common/SvgIcon.vue";
import RoomControlDialogs, {
    type RoomDialog,
} from "../components/rooms/RoomControlDialogs.vue";
import type { Room } from "../types/room";

type DeviceCard = {
    key: string;
    icon: string;
    name: string;
    detail: string;
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

const categories = [
    { name: "全部设备", icon: "chevron-down" },
    { name: "灯光", icon: "light" },
    { name: "空调", icon: "air-conditioner" },
    { name: "窗帘", icon: "curtain" },
    { name: "插座", icon: "plug" },
    { name: "场景", icon: "scene" },
    { name: "更多...", icon: "more" },
];

const commonDevices: DeviceCard[] = [
    { key: "light", icon: "light", name: "吸顶灯", detail: "亮度 80%" },
    { key: "television", icon: "device-management", name: "电视", detail: "音量 30%" },
    { key: "airConditioner", icon: "air-conditioner", name: "空调", detail: "24°C" },
    { key: "airPurifier", icon: "sensor", name: "空气净化器", detail: "风速 自动" },
    { key: "socket", icon: "plug", name: "智能插座", detail: "" },
];

const environment = computed(() => {
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

const toggleDevice = async (device: DeviceCard) => {
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
        <main class="workspace">
            <header class="page-header">
                <div>
                    <h1>房间控制</h1>
                    <p>按房间查看设备状态、环境数据与快捷控制</p>
                </div>
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
            </header>

            <section class="stats-grid">
                <article><i class="blue"><SvgIcon name="home" /></i><span>房间数量<strong>{{ rooms.length }} <small>个</small></strong><em>较上月 ↑ 2</em></span></article>
                <article><i class="green"><SvgIcon name="online-device" /></i><span>在线设备<strong>{{ online }} <small>个</small></strong><em>在线率 86.4%</em></span></article>
                <article><i class="orange"><SvgIcon name="notification" /></i><span>当前告警<strong>2 <small>条</small></strong><em>待处理告警</em></span></article>
                <article><i class="purple"><SvgIcon name="comfort" /></i><span>平均舒适度<strong>{{ comfort }} <small>分</small></strong><em>舒适度良好</em></span></article>
            </section>

            <section class="room-grid">
                <article
                    v-for="room in visibleRooms"
                    :key="room.id"
                    class="room-card"
                    :class="{ selected: selected?.id === room.id }"
                    @click="selectRoom(room)"
                >
                    <header>
                        <span class="room-avatar">{{ room.name.slice(0, 1) }}</span>
                        <div><h2>{{ room.name }} <small>{{ room.comfort >= 84 ? "舒适" : "良好" }}</small></h2><p><b></b>{{ room.onlineCount }} 个设备在线</p></div>
                    </header>
                    <div class="room-metrics">
                        <span><SvgIcon name="temperature" size="sm" />{{ room.temperature }}°C</span>
                        <span><SvgIcon name="humidity" size="sm" />{{ room.humidity }}%</span>
                        <span class="quality"><SvgIcon name="air-quality" size="sm" />优 {{ room.pm25 }}</span>
                    </div>
                    <div class="room-devices">
                        <button v-for="device in commonDevices.slice(0, 4)" :key="device.name" :class="{ on: room.deviceStates[device.key] }" type="button" @click.stop="selectRoom(room); toggleDevice(device)">
                            <i><SvgIcon :name="device.icon" size="sm" /></i><span>{{ device.name }}</span><small>{{ room.deviceStates[device.key] ? "开" : "关" }}</small>
                        </button>
                    </div>
                </article>
            </section>

            <section class="quick-control" :class="{ 'is-loading': loading }">
        <aside class="room-sidebar">
            <h1>房间快捷控制</h1>
            <nav aria-label="房间列表">
                <button
                    v-for="room in rooms"
                    :key="room.id"
                    :class="{ active: selected?.id === room.id }"
                    type="button"
                    @click="selectRoom(room)"
                >
                    {{ room.name }}
                </button>
            </nav>
        </aside>

        <main v-if="selected" class="control-content">
            <nav class="category-bar" aria-label="设备分类">
                <button
                    v-for="category in categories"
                    :key="category.name"
                    :class="{ active: activeCategory === category.name }"
                    type="button"
                    @click="
                        activeCategory = category.name;
                        if (category.name === '场景') activeDialog = 'scene';
                        if (category.name === '更多...') activeDialog = 'devices';
                    "
                >
                    <SvgIcon :name="category.icon" size="sm" />
                    <span>{{ category.name }}</span>
                </button>
            </nav>

            <section class="control-section">
                <h2>常用设备</h2>
                <div class="device-grid">
                    <article
                        v-for="device in commonDevices"
                        :key="device.name"
                        class="device-card"
                        :class="{
                            featured: device.key === 'airConditioner',
                            disabled: !selected.deviceStates[device.key],
                        }"
                    >
                        <header>
                            <span class="device-icon">
                                <SvgIcon :name="device.icon" size="sm" />
                            </span>
                            <div>
                                <strong>{{ device.name }}</strong>
                                <small>{{ selected.name }}</small>
                            </div>
                            <button
                                class="switch"
                                :class="{ enabled: selected.deviceStates[device.key] }"
                                :aria-label="`切换${device.name}`"
                                type="button"
                                @click="toggleDevice(device)"
                            ><span></span></button>
                        </header>

                        <div v-if="device.key === 'light'" class="range-row">
                            <span>亮度 0%</span><i><b></b></i>
                        </div>
                        <div v-else-if="device.key === 'television'" class="range-row">
                            <span>音量</span><i class="volume"><b></b></i><em>30%</em>
                        </div>
                        <div v-else-if="device.key === 'airConditioner'" class="temperature-row">
                            <b>{{ temperature }}°C</b>
                            <button type="button" @click="temperature = Math.max(16, temperature - 1)">−</button>
                            <button type="button" @click="temperature = Math.min(30, temperature + 1)">＋</button>
                        </div>
                        <div v-else-if="device.key === 'airPurifier'" class="purifier-row">
                            <span>风速</span><b>自动</b><SvgIcon name="refresh" size="sm" />
                        </div>
                    </article>
                </div>
            </section>

            <section class="control-section environment-section">
                <h2>环境数据</h2>
                <div class="environment-grid">
                    <article v-for="item in environment" :key="item.name" role="button" tabindex="0" @click="activeDialog = 'environment'" @keydown.enter="activeDialog = 'environment'">
                        <small>{{ item.name }}</small>
                        <strong>{{ item.value }}</strong>
                        <svg :class="item.tone" viewBox="0 0 66 22" aria-hidden="true">
                            <polyline :points="item.points" />
                        </svg>
                    </article>
                </div>
            </section>
        </main>

        <div v-else class="empty-state">
            {{ loading ? "正在加载房间..." : "暂无房间数据" }}
        </div>
            </section>
        </main>

        <aside v-if="selected" class="room-detail">
            <section>
                <h2>房间详情</h2>
                <div class="detail-heading"><span>{{ selected.name.slice(0, 1) }}</span><div><h3>{{ selected.name }} <small>舒适</small></h3><p><b></b>在线</p></div></div>
                <dl>
                    <div><dt>所在楼层</dt><dd>{{ selected.floor }}</dd></div>
                    <div><dt>面积</dt><dd>{{ selected.area }} m²</dd></div>
                    <div><dt>在线设备</dt><dd>{{ selected.onlineCount }} / {{ selected.deviceCount }} 个</dd></div>
                    <div><dt>当前场景</dt><dd>休闲模式</dd></div>
                    <div><dt>最近活动</dt><dd>10 分钟前（打开台灯）</dd></div>
                </dl>
                <div class="detail-actions"><button class="primary" type="button" @click="activeDialog = 'devices'"><SvgIcon name="power" size="sm" />进入控制</button><button type="button" @click="activeDialog = 'edit'"><SvgIcon name="edit" size="sm" />编辑房间</button></div>
            </section>
            <section class="environment-overview" @click="activeDialog = 'environment'">
                <h2>环境概览 <small>实时更新</small></h2>
                <div class="detail-environment"><p v-for="item in environment" :key="item.name"><span>{{ item.name }}</span><strong>{{ item.value }}</strong></p></div>
            </section>
            <section>
                <h2>快捷操作</h2>
                <div class="detail-quick">
                    <button type="button" @click="quick('all_lights')"><SvgIcon name="light" />全开灯光</button>
                    <button type="button" @click="quick('air_conditioner')"><SvgIcon name="air-conditioner" />关闭空调</button>
                    <button type="button" @click="quick('curtains')"><SvgIcon name="curtain" />打开窗帘</button>
                    <button type="button" @click="activeDialog = 'logs'"><SvgIcon name="log" />查看日志</button>
                </div>
            </section>
        </aside>

        <RoomControlDialogs
            v-model="activeDialog"
            :room="selected"
            @create="handleRoomCreated"
            @update="handleRoomUpdated"
        />
    </div>
</template>

<style scoped>
.workspace,
.room-detail {
    min-width: 0;
    min-height: 0;
    overflow-y: auto;
    border: 1px solid var(--color-border);
    border-radius: 18px;
    background: var(--color-page-bg);
}

.workspace {
    display: flex;
    flex-direction: column;
    gap: 14px;
    padding: 18px;
}

.page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
}

.page-header h1 { margin: 0; font-size: 24px; font-weight: 900; }
.page-header p { margin: 7px 0 0; color: var(--color-text-tertiary); font-size: 13px; font-weight: 700; }
.page-tools { display: flex; align-items: center; gap: 8px; }
.page-tools label { display: flex; min-width: 220px; height: 38px; align-items: center; gap: 8px; border: 1px solid var(--color-border); border-radius: 9px; background: var(--color-card-bg); padding: 0 11px; color: var(--color-text-tertiary); }
.page-tools input { min-width: 0; flex: 1; border: 0; outline: 0; }
.page-tools select { height: 38px; padding-left: 10px; }
.primary { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border-radius: 9px; background: var(--color-primary-600) !important; color: white !important; }
.page-tools .primary { height: 38px; padding: 0 14px; font-size: 12px; font-weight: 800; }

.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.stats-grid article { display: flex; min-width: 0; align-items: center; gap: 12px; border: 1px solid var(--color-border); border-radius: 13px; background: var(--color-card-bg); padding: 14px; box-shadow: var(--shadow-card); }
.stats-grid i { display: grid; width: 42px; height: 42px; flex: 0 0 42px; place-items: center; border-radius: 11px; font-style: normal; }
.stats-grid i.blue { background: var(--color-primary-50); color: var(--color-primary-600); }
.stats-grid i.green { background: var(--color-success-soft); color: var(--color-success); }
.stats-grid i.orange { background: var(--color-warning-soft); color: var(--color-warning); }
.stats-grid i.purple { background: #f3e8ff; color: #8b5cf6; }
.stats-grid span { min-width: 0; color: var(--color-text-tertiary); font-size: 11px; font-weight: 750; }
.stats-grid strong { display: block; margin-top: 3px; color: var(--color-text-primary); font-size: 20px; }
.stats-grid strong small { font-size: 11px; }
.stats-grid em { display: block; margin-top: 2px; color: var(--color-text-tertiary); font-size: 9px; font-style: normal; }

.room-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.room-card { min-width: 0; border: 1px solid var(--color-border); border-radius: 14px; background: var(--color-card-bg); padding: 14px; box-shadow: var(--shadow-card); cursor: pointer; transition: 160ms var(--motion-ease); }
.room-card:hover, .room-card.selected { border-color: var(--color-primary-300); box-shadow: var(--shadow-card-hover); }
.room-card > header { display: flex; align-items: center; gap: 10px; }
.room-avatar { display: grid; width: 42px; height: 42px; place-items: center; border-radius: 11px; background: linear-gradient(135deg, var(--color-primary-100), var(--color-primary-50)); color: var(--color-primary-700); font-weight: 900; }
.room-card h2 { margin: 0; font-size: 15px; }
.room-card h2 small, .detail-heading h3 small { border-radius: 999px; background: var(--color-success-soft); padding: 2px 6px; color: var(--color-success); font-size: 9px; }
.room-card header p { margin: 4px 0 0; color: var(--color-text-tertiary); font-size: 10px; }
.room-card header p b, .detail-heading p b { display: inline-block; width: 6px; height: 6px; margin-right: 4px; border-radius: 50%; background: var(--color-success); }
.room-metrics { display: flex; gap: 8px; margin: 12px 0; }
.room-metrics span { display: inline-flex; align-items: center; gap: 3px; border-radius: 7px; background: var(--color-surface-subtle); padding: 5px 7px; color: var(--color-text-secondary); font-size: 10px; font-weight: 800; }
.room-metrics .quality { background: var(--color-success-soft); color: var(--color-success); }
.room-devices { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; }
.room-devices button { display: grid; min-width: 0; place-items: center; gap: 3px; border-radius: 8px; background: var(--color-surface-subtle); padding: 7px 3px; color: var(--color-text-tertiary); font-size: 9px; }
.room-devices button.on { background: var(--color-primary-50); color: var(--color-primary-700); }
.room-devices i { font-style: normal; }
.room-devices span { overflow: hidden; max-width: 100%; text-overflow: ellipsis; white-space: nowrap; font-weight: 800; }
.room-devices small { font-size: 8px; }

.room-detail { display: flex; flex-direction: column; gap: 12px; padding: 12px; }
.room-detail > section { border: 1px solid var(--color-border); border-radius: 14px; background: var(--color-card-bg); padding: 15px; box-shadow: var(--shadow-card); }
.room-detail h2 { display: flex; align-items: center; justify-content: space-between; margin: 0 0 13px; font-size: 14px; }
.room-detail h2 > small { color: var(--color-text-tertiary); font-size: 9px; }
.detail-heading { display: flex; align-items: center; gap: 10px; }
.detail-heading > span { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 12px; background: var(--color-primary-50); color: var(--color-primary-700); font-weight: 900; }
.detail-heading h3 { margin: 0; font-size: 14px; }
.detail-heading p { margin: 5px 0 0; color: var(--color-text-tertiary); font-size: 10px; }
.room-detail dl { margin: 13px 0; }
.room-detail dl div { display: flex; justify-content: space-between; gap: 10px; border-bottom: 1px solid var(--color-border-subtle); padding: 8px 0; font-size: 10px; }
.room-detail dt { color: var(--color-text-tertiary); }
.room-detail dd { margin: 0; color: var(--color-text-secondary); font-weight: 800; text-align: right; }
.detail-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
.detail-actions button { display: inline-flex; min-height: 34px; align-items: center; justify-content: center; gap: 5px; border: 1px solid var(--color-border); border-radius: 8px; color: var(--color-text-secondary); font-size: 10px; font-weight: 800; }
.detail-environment { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
.detail-environment p { margin: 0; border-radius: 8px; background: var(--color-surface-subtle); padding: 9px; }
.detail-environment span, .detail-environment strong { display: block; }
.detail-environment span { color: var(--color-text-tertiary); font-size: 9px; }
.detail-environment strong { margin-top: 3px; font-size: 12px; }
.detail-quick { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; }
.detail-quick button { display: flex; min-width: 0; flex-direction: column; align-items: center; gap: 5px; border-radius: 8px; background: var(--color-primary-50); padding: 9px 4px; color: var(--color-primary-700); font-size: 9px; font-weight: 800; }

.quick-control {
    display: grid;
    min-width: 0;
    min-height: 0;
    grid-template-columns: 138px minmax(0, 1fr);
    align-self: stretch;
    overflow: hidden;
    border: 1px solid var(--color-border-subtle);
    border-radius: 18px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.quick-control.is-loading {
    opacity: 0.72;
}

.room-sidebar {
    border-right: 1px solid var(--color-border-subtle);
    padding: 14px 10px;
    background: var(--color-sidebar-bg);
}

.room-sidebar h1 {
    margin: 0 8px 10px;
    color: var(--color-text-primary);
    font-size: 14px;
    font-weight: 900;
}

.room-sidebar nav {
    display: grid;
    gap: 4px;
}

.room-sidebar button {
    position: relative;
    min-height: 31px;
    border-radius: 7px;
    padding: 0 12px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 800;
    text-align: left;
    transition: 160ms var(--motion-ease);
}

.room-sidebar button:hover {
    background: var(--color-surface-hover);
}

.room-sidebar button.active {
    background: linear-gradient(90deg, var(--color-primary-50), var(--color-primary-100));
    color: var(--color-primary-700);
}

.room-sidebar button.active::before {
    position: absolute;
    top: 4px;
    bottom: 4px;
    left: 0;
    width: 3px;
    border-radius: 999px;
    background: var(--color-primary-600);
    content: "";
}

.control-content {
    min-width: 0;
    overflow-x: hidden;
    overflow-y: auto;
    padding: 12px 14px 14px;
    background: var(--color-page-bg);
}

.category-bar {
    display: grid;
    grid-template-columns: 1.25fr repeat(6, minmax(0, 1fr));
    gap: 9px;
    padding-bottom: 9px;
}

.category-bar button {
    display: inline-flex;
    min-width: 0;
    height: 36px;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border: 1px solid var(--color-border-subtle);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    font-size: 10px;
    font-weight: 800;
    box-shadow: var(--shadow-card);
    transition: 160ms var(--motion-ease);
}

.category-bar button svg {
    color: var(--color-primary-600);
}

.category-bar button:first-child svg {
    order: 2;
    color: var(--color-text-tertiary);
}

.category-bar button:hover,
.category-bar button.active {
    border-color: var(--color-primary-200);
    color: var(--color-primary-700);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-1px);
}

.control-section h2 {
    margin: 1px 5px 7px;
    color: var(--color-text-secondary);
    font-size: 11px;
    font-weight: 900;
}

.device-grid,
.environment-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 8px;
}

.device-card,
.environment-grid article {
    min-width: 0;
    border: 1px solid var(--color-border-subtle);
    border-radius: 12px;
    background: var(--color-card-bg);
    box-shadow: var(--shadow-card);
}

.device-card {
    min-height: 88px;
    padding: 10px;
    transition: 160ms var(--motion-ease);
}

.device-card:hover {
    border-color: var(--color-primary-200);
    transform: translateY(-1px);
}

.device-card.featured {
    border-color: var(--color-primary-300);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}

.device-card.disabled {
    opacity: 0.68;
}

.device-card header {
    display: grid;
    grid-template-columns: 30px minmax(0, 1fr) auto;
    align-items: center;
    gap: 7px;
}

.device-icon {
    display: grid;
    width: 30px;
    height: 30px;
    place-items: center;
    border-radius: 7px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}

.device-card header div {
    display: grid;
    min-width: 0;
    gap: 2px;
}

.device-card strong,
.device-card small {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.device-card strong {
    color: var(--color-text-primary);
    font-size: 10px;
    font-weight: 900;
}

.device-card small {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-weight: 700;
}

.switch {
    width: 29px;
    height: 16px;
    border-radius: 999px;
    background: var(--color-text-muted);
    padding: 2px;
    transition: 160ms var(--motion-ease);
}

.switch span {
    display: block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: white;
    box-shadow: 0 1px 3px rgb(15 23 42 / 24%);
    transition: 160ms var(--motion-ease);
}

.switch.enabled {
    background: var(--color-primary-600);
}

.switch.enabled span {
    transform: translateX(13px);
}

.range-row,
.temperature-row,
.purifier-row {
    display: flex;
    min-height: 27px;
    align-items: flex-end;
    gap: 6px;
    color: var(--color-text-tertiary);
    font-size: 8px;
    font-weight: 700;
}

.range-row i {
    position: relative;
    height: 5px;
    flex: 1;
    overflow: hidden;
    border-radius: 999px;
    background: var(--color-surface-subtle);
}

.range-row i::before {
    display: block;
    width: 64%;
    height: 100%;
    background: var(--color-primary-600);
    content: "";
}

.range-row i b {
    position: absolute;
    top: -3px;
    left: 62%;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: var(--color-primary-600);
}

.range-row .volume::before {
    width: 54%;
}

.range-row em {
    color: var(--color-text-secondary);
    font-style: normal;
}

.temperature-row {
    align-items: flex-end;
}

.temperature-row > b {
    margin-right: auto;
    color: var(--color-text-primary);
    font-size: 14px;
}

.temperature-row button {
    display: grid;
    width: 22px;
    height: 20px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-primary-50);
    color: var(--color-primary-700);
    font-size: 13px;
    font-weight: 700;
}

.purifier-row b {
    color: var(--color-text-secondary);
}

.purifier-row svg {
    margin-left: auto;
    color: var(--color-primary-500);
}

.environment-section {
    margin-top: 9px;
}

.environment-grid article {
    position: relative;
    min-height: 58px;
    overflow: hidden;
    padding: 9px 11px;
}

.environment-grid small,
.environment-grid strong {
    position: relative;
    z-index: 1;
    display: block;
}

.environment-grid small {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-weight: 750;
}

.environment-grid strong {
    margin-top: 4px;
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 900;
}

.environment-grid svg {
    position: absolute;
    right: 9px;
    bottom: 8px;
    width: 52px;
    height: 18px;
    fill: none;
    stroke: var(--color-primary-500);
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 2;
}

.environment-grid svg.green { stroke: var(--color-success); }
.environment-grid svg.orange { stroke: var(--color-warning); }
.environment-grid svg.purple { stroke: #8b5cf6; }

.empty-state {
    display: grid;
    min-height: 400px;
    place-items: center;
    background: var(--color-page-bg);
    color: var(--color-text-tertiary);
    font-size: 14px;
    font-weight: 800;
}

@media (max-width: 1280px) {
    .category-bar {
        display: flex;
        gap: 10px;
        overflow-x: auto;
    }
    .category-bar button { min-width: 96px; }
    .category-bar button:first-child { min-width: 120px; }
    .device-grid,
    .environment-grid { grid-template-columns: repeat(3, minmax(160px, 1fr)); }
}

@media (max-width: 1450px) {
    .page-header { display: grid; }
    .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .quick-control { grid-template-columns: 128px minmax(0, 1fr); }
    .room-sidebar { padding-right: 10px; padding-left: 10px; }
    .control-content { padding-right: 14px; padding-left: 14px; }
}

@media (max-width: 860px) {
    .quick-control { grid-template-columns: 1fr; }
    .room-sidebar { border-right: 0; border-bottom: 1px solid var(--color-border-subtle); padding: 16px; }
    .room-sidebar h1 { margin-bottom: 10px; }
    .room-sidebar nav { display: flex; overflow-x: auto; }
    .room-sidebar button { min-width: 90px; text-align: center; }
    .room-sidebar button.active::before { top: auto; right: 8px; bottom: 0; left: 8px; width: auto; height: 3px; }
    .control-content { padding: 16px; }
}

@media (max-width: 620px) {
    .device-grid,
    .environment-grid { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
    .quick-control *,
    .quick-control *::before,
    .quick-control *::after { transition-duration: 1ms !important; }
}
</style>
