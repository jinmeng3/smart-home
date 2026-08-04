<script setup lang="ts">
import { computed, ref, shallowRef } from "vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import PageHeader from "../components/common/PageHeader.vue";
import StatsCard from "../components/common/StatsCard.vue";
import OverviewDialogs, {
    type OverviewDialog,
} from "../components/overview/OverviewDialogs.vue";

const rooms = shallowRef([
    {
        name: "客厅",
        icon: "room",
        count: 6,
        light: "2/2 开",
        air: "26°C 制冷",
        extra: "窗帘 已关闭",
        tone: "blue",
    },
    {
        name: "主卧",
        icon: "room",
        count: 5,
        light: "1/2 开",
        air: "26°C 制冷",
        extra: "窗帘 已关闭",
        tone: "blue",
    },
    {
        name: "次卧",
        icon: "room",
        count: 4,
        light: "0/1 开",
        air: "27°C 制冷",
        extra: "窗帘 已关闭",
        tone: "blue",
    },
    {
        name: "厨房",
        icon: "plug",
        count: 5,
        light: "1/1 开",
        air: "烟机 关闭",
        extra: "燃气 正常",
        tone: "orange",
    },
    {
        name: "卫生间",
        icon: "humidity",
        count: 4,
        light: "1/1 开",
        air: "排风机 开启",
        extra: "水浸 正常",
        tone: "green",
    },
    {
        name: "阳台",
        icon: "illumination",
        count: 4,
        light: "0/1 开",
        air: "洗衣机 待机",
        extra: "温湿度 28°C 60%",
        tone: "orange",
    },
]);
const selectedTab = ref("常用设备");
const searchKeyword = ref("");
const refreshed = ref("5 分钟前");
const activeDialog = ref<OverviewDialog>(null);

interface OverviewDevice {
    id: number;
    name: string;
    room: string;
    status: "在线" | "离线";
    detail: string;
    updatedAt: string;
    icon: string;
    tone: string;
    frequent: boolean;
    favorite: boolean;
}

const devices = ref<OverviewDevice[]>([
    { id: 1, name: "客厅吸顶灯", room: "客厅", status: "在线", detail: "亮度 80%", updatedAt: "10:15", icon: "light", tone: "orange", frequent: true, favorite: true },
    { id: 2, name: "客厅空调", room: "客厅", status: "在线", detail: "26°C 制冷", updatedAt: "10:15", icon: "air-conditioner", tone: "blue", frequent: true, favorite: true },
    { id: 3, name: "主卧空调", room: "主卧", status: "在线", detail: "26°C 制冷", updatedAt: "10:14", icon: "air-conditioner", tone: "blue", frequent: true, favorite: false },
    { id: 4, name: "智能门锁", room: "玄关", status: "在线", detail: "已上锁", updatedAt: "10:13", icon: "lock", tone: "purple", frequent: true, favorite: true },
    { id: 5, name: "空气净化器", room: "客厅", status: "在线", detail: "自动模式", updatedAt: "10:12", icon: "sensor", tone: "green", frequent: true, favorite: false },
    { id: 6, name: "厨房烟感", room: "厨房", status: "在线", detail: "电量 18% · 告警", updatedAt: "10:10", icon: "notification", tone: "orange", frequent: false, favorite: false },
    { id: 7, name: "阳台门磁", room: "阳台", status: "在线", detail: "已关闭", updatedAt: "10:09", icon: "security", tone: "green", frequent: false, favorite: false },
    { id: 8, name: "客厅摄像头", room: "客厅", status: "离线", detail: "连接中断", updatedAt: "09:58", icon: "camera", tone: "purple", frequent: false, favorite: false },
]);

const visibleDevices = computed(() => {
    const keyword = searchKeyword.value.trim().toLocaleLowerCase();

    return devices.value.filter((device) => {
        const matchesTab =
            selectedTab.value === "全部设备" ||
            (selectedTab.value === "常用设备" && device.frequent) ||
            (selectedTab.value === "收藏设备" && device.favorite);
        const matchesKeyword =
            !keyword ||
            [device.name, device.room, device.status, device.detail].some(
                (value) => value.toLocaleLowerCase().includes(keyword),
            );

        return matchesTab && matchesKeyword;
    });
});

const toggleFavorite = (deviceId: number) => {
    devices.value = devices.value.map((device) =>
        device.id === deviceId
            ? { ...device, favorite: !device.favorite }
            : device,
    );
};

const openDialog = (dialog: Exclude<OverviewDialog, null>) => {
    activeDialog.value = dialog;
};

const handleSynced = () => {
    refreshed.value = "刚刚";
};

const handleRoomCreated = (name: string) => {
    rooms.value = [
        ...rooms.value,
        {
            name,
            icon: "room",
            count: 0,
            light: "0/0 开",
            air: "暂无设备",
            extra: "等待绑定",
            tone: "blue",
        },
    ];
};
</script>

<template>
    <div class="contents">
        <main class="overview page-shell page-enter">
            <PageHeader title="全屋总览" description="查看家庭运行状态、房间分布与设备总览">
                <label class="search"
                    ><SvgIcon name="search" size="sm" /><input
                        v-model="searchKeyword"
                        placeholder="搜索设备、场景或房间"
                /></label>
            </PageHeader>
            <section class="stats card-grid-enter">
                <StatsCard
                    icon="online-device"
                    label="在线设备总数"
                    value="28"
                    detail="在线率 77.8%"
                    tone="blue"
                />
                <StatsCard
                    icon="automation"
                    label="自动化运行中"
                    value="8"
                    detail="较昨日 +2"
                    tone="green"
                />
                <StatsCard
                    icon="notification"
                    label="今日告警"
                    value="2"
                    detail="较昨日 -1 ↓"
                    tone="orange"
                />
                <StatsCard
                    icon="air-quality"
                    label="本月节能概况"
                    value="32.6"
                    unit="kWh"
                    detail="节能 12% ↑"
                    tone="purple"
                />
            </section>
            <section class="panel home-status">

                <div class="status-row">
                    <div>
                        <i class="green"><SvgIcon name="security" /></i
                        ><span
                            >家庭状态<b class="ok">一切正常</b
                            ><small>系统运行良好</small></span
                        >
                    </div>
                    <div>
                        <i class="blue"><SvgIcon name="members" /></i
                        ><span
                            >在家人数<b>2 人</b><small>张晓明 等</small></span
                        >
                    </div>
                    <div>
                        <i class="blue"><SvgIcon name="temperature" /></i
                        ><span>室内温度<b>26.0°C</b><small>舒适</small></span>
                    </div>
                    <div>
                        <i class="blue"><SvgIcon name="humidity" /></i
                        ><span>室内湿度<b>55%</b><small>舒适</small></span>
                    </div>
                    <div>
                        <i class="green"><SvgIcon name="air-quality" /></i
                        ><span
                            >空气质量<b class="ok">优 28</b
                            ><small>PM2.5</small></span
                        >
                    </div>
                    <div>
                        <i class="gray"><SvgIcon name="lock" /></i
                        ><span
                            >门锁状态<b>全部上锁</b
                            ><small>6/6 已上锁</small></span
                        >
                    </div>
                </div>
            </section>
            <section class="panel rooms">
                <header>
                    <h2>房间概览</h2>
                    <a>查看房间分布 ›</a>
                </header>
                <div class="room-grid card-grid-enter">
                    <article v-for="room in rooms" :key="room.name">
                        <div class="room-title">
                            <i :class="room.tone"
                                ><SvgIcon :name="room.icon" /></i
                            ><span
                                ><b>{{ room.name }}</b
                                ><small>{{ room.count }} 个设备</small></span
                            >
                        </div>
                        <div class="room-devices">
                            <span
                                >☀️ <small>灯光</small
                                ><b>{{ room.light }}</b></span
                            ><span
                                >❄️ <small>设备</small
                                ><b>{{ room.air }}</b></span
                            ><span
                                >▥ <small>状态</small
                                ><b>{{ room.extra }}</b></span
                            >
                        </div>
                        <button>进入控制</button>
                    </article>
                </div>
            </section>
            <div class="bottom-grid">
                <section class="panel device-list">
                    <nav>
                        <h2>设备概览</h2>
                        <button
                            v-for="tab in ['全部设备', '常用设备', '收藏设备']"
                            :key="tab"
                            :class="{ active: selectedTab === tab }"
                            @click="selectedTab = tab"
                        >
                            {{ tab }}
                        </button>
                    </nav>
                    <table>
                        <thead>
                            <tr>
                                <th>设备名称</th>
                                <th>所属房间</th>
                                <th>状态</th>
                                <th>状态信息</th>
                                <th>更新时间</th>
                                <th>收藏</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                v-for="device in visibleDevices.slice(0, 5)"
                                :key="device.id"
                            >
                                <td class="device-cell">
                                    <i :class="device.tone"
                                        ><SvgIcon :name="device.icon" size="sm" /></i
                                    ><span>{{ device.name }}</span>
                                </td>
                                <td>{{ device.room }}</td>
                                <td :class="device.status === '在线' ? 'online' : 'offline'">● {{ device.status }}</td>
                                <td>{{ device.detail }}</td>
                                <td>{{ device.updatedAt }}</td>
                                <td>
                                    <button
                                        class="favorite"
                                        :class="{ active: device.favorite }"
                                        :aria-label="device.favorite ? `取消收藏${device.name}` : `收藏${device.name}`"
                                        type="button"
                                        @click="toggleFavorite(device.id)"
                                    >{{ device.favorite ? "★" : "☆" }}</button>
                                </td>
                            </tr>
                            <tr v-if="visibleDevices.length === 0">
                                <td class="device-empty" colspan="6">没有符合条件的设备</td>
                            </tr>
                        </tbody>
                    </table>
                    <button class="view-all" type="button" @click="openDialog('devices')">
                        查看全部设备（{{ devices.length }}）⌄
                    </button>
                </section>
                <section class="panel activity">
                    <header>
                        <h2>今日活动 / 动态</h2>
                        <a>查看全部 ›</a>
                    </header>
                    <p
                        v-for="item in [
                            [
                                '10:15',
                                'lock',
                                '门锁开启',
                                '张晓明通过指纹打开了玄关门锁',
                                'purple',
                            ],
                            [
                                '10:10',
                                'air-conditioner',
                                '空调运行',
                                '客厅空调已开启，设定 26°C 制冷模式',
                                'blue',
                            ],
                            [
                                '10:05',
                                'curtain',
                                '窗帘关闭',
                                '主卧窗帘已自动关闭',
                                'teal',
                            ],
                            [
                                '09:58',
                                'automation',
                                '自动化执行',
                                '“离家模式”自动执行完成',
                                'green',
                            ],
                            [
                                '09:45',
                                'light',
                                '灯光开启',
                                '卫生间灯光已开启',
                                'orange',
                            ],
                        ]"
                        :key="item[0]"
                    >
                        <time>{{ item[0] }}</time
                        ><i :class="item[4]"
                            ><SvgIcon :name="item[1]" size="sm" /></i
                        ><span
                            ><b>{{ item[2] }}</b
                            ><small>{{ item[3] }}</small></span
                        >
                    </p>
                </section>
            </div>
        </main>
        <aside class="right page-shell">
            <section class="panel">
                <header>
                    <h2 class="schedule-title">
                        <span class="tone-chip is-orange">
                            <SvgIcon name="calendar" size="sm" />
                        </span>
                        家庭日程
                        <small>/ 自动化计划</small>
                    </h2>
                    <a role="button" tabindex="0" @click="openDialog('schedule')">更多</a>
                </header>
                <div class="date-nav">
                    <button class="date-arrow" type="button" aria-label="上一个日期">
                        <SvgIcon name="chevron-left" size="sm" />
                    </button>
                    <div class="date-info">
                        <strong>5月20日 星期二</strong>
                        <span class="today-badge"><i></i>今天</span>
                    </div>
                    <button class="date-arrow" type="button" aria-label="下一个日期">
                        <SvgIcon name="chevron-right" size="sm" />
                    </button>
                </div>
                <div class="schedule-list">
                    <article
                        v-for="item in [
                            [
                                '07:00',
                                '起床模式',
                                '窗帘打开 · 卧室灯亮 · 空调制热 24°C',
                                'orange',
                            ],
                            [
                                '19:00',
                                '回家模式',
                                '玄关灯亮 · 空调制冷 26°C · 新风开启',
                                'blue',
                            ],
                            [
                                '22:00',
                                '离家模式',
                                '关闭灯光 · 安防布防 · 监控夜视',
                                'purple',
                            ],
                            [
                                '23:00',
                                '睡眠模式',
                                '灯光渐暗 · 窗帘关闭 · 安防设防',
                                'teal',
                            ],
                        ]"
                        :key="item[0]"
                        :class="`is-${item[3]}`"
                    >
                        <time class="schedule-time">{{ item[0] }}</time>
                        <span class="timeline-node" aria-hidden="true"></span>
                        <div class="schedule-body">
                            <b>{{ item[1] }}</b>
                            <small>{{ item[2] }}</small>
                        </div>
                    </article>
                </div>
                <p class="schedule-summary">
                    今日计划 <b>4</b> 个 · 已开启 <b>3</b> 个
                </p>
            </section>
            <section class="panel">
                <header>
                    <h2>设备状态</h2>
                    <a role="button" tabindex="0" @click="openDialog('devices')">更多</a>
                </header>
                <div class="device-count">
                    <span>总设备<b>36</b></span
                    ><span>在线设备<b class="ok">• 28</b></span
                    ><span>离线设备<b class="warn">• 8</b></span>
                </div>
                <h3>重点提醒</h3>
                <p class="alert">⚠ 厨房烟感电池电量低 <em>厨房</em></p>
                <p class="alert">⚠ 阳台门磁长时间未关闭 <em>阳台</em></p>
                <p class="alert">♟ 主卧空调滤网需要清洁 <em>主卧</em></p>
            </section>
            <section class="panel">
                <h2>快捷操作</h2>
                <div class="quick">
                    <button
                        class="tone-purple"
                        @click="openDialog('inspection')"
                    >
                        <SvgIcon name="scan" />一键巡检<small
                            >检查全屋设备</small
                        ></button
                    ><button
                        class="tone-blue"
                        @click="openDialog('mode')"
                    >
                        <SvgIcon name="home" />全屋模式<small
                            >快速启用场景</small
                        ></button
                    ><button
                        class="tone-green"
                        @click="openDialog('sync')"
                    >
                        <SvgIcon name="refresh" />同步设备<small
                            >刷新设备状态</small
                        ></button
                    ><button
                        class="tone-orange"
                        @click="openDialog('room')"
                    >
                        <SvgIcon name="plus" />添加房间<small>创建新房间</small>
                    </button>
                </div>
                <footer>最近同步：{{ refreshed }} <a>⟳ 刷新</a></footer>
            </section>
        </aside>
        <OverviewDialogs
            v-model="activeDialog"
            @synced="handleSynced"
            @room-created="handleRoomCreated"
        />
    </div>
</template>

<style scoped>
.page-shell {
    min-width: 0;
    height: 100%;
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 18px;
    background: var(--color-page-bg);
    box-shadow: var(--shadow-soft);
}
.overview {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 18px;
}
.search {
    display: flex;
    width: 240px;
    height: 38px;
    align-items: center;
    gap: 8px;
    border: 1px solid #dce5f2;
    border-radius: 9px;
    background: #fff;
    padding: 0 12px;
    color: #8ca0bb;
}
.search input {
    min-width: 0;
    outline: 0;
    font-size: 12px;
}
.stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}
.status-row i,
.room-title i {
    display: grid;
    width: 44px;
    height: 44px;
    flex: none;
    place-items: center;
    border-radius: 50%;
}
.blue {
    background: #e9f2ff;
    color: #2871f5;
}
.green {
    background: #e7f9ee;
    color: #20b86a;
}
.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.purple {
    background: #eee9ff;
    color: #7651ee;
}
.gray {
    background: #edf1f6;
    color: #64748b;
}

.panel {
    border: 1px solid #e2e9f2;
    border-radius: 14px;
    background: #fff;
    padding: 13px;
    box-shadow: var(--shadow-card);
}
.panel h2 {
    font-size: 15px;
    font-weight: 900;
}
.panel header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.panel a {
    color: #246df2;
    font-size: 11px;
    font-weight: 800;
}
.status-row {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-top: 12px;
}
.status-row > div {
    display: flex;
    align-items: center;
    gap: 9px;
}
.status-row span {
    display: flex;
    min-width: 0;
    flex-direction: column;
    color: #77869b;
    font-size: 10px;
}
.status-row b {
    color: #26354c;
    font-size: 13px;
}
.status-row small {
    white-space: nowrap;
}
.ok,
.online {
    color: #17ad62 !important;
}
.offline {
    color: var(--color-danger) !important;
}
.favorite {
    color: var(--color-text-muted);
    font-size: 18px;
    line-height: 1;
}
.favorite:hover,
.favorite.active {
    color: var(--color-warning);
}
.device-empty {
    height: 96px;
    color: var(--color-text-tertiary) !important;
    text-align: center !important;
}
.rooms {
    padding: 0;
}
.rooms header {
    padding: 12px 14px;
}
.room-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 9px;
    padding: 0 12px 12px;
}
.room-grid article {
    border: 1px solid #e2e9f2;
    border-radius: 10px;
    padding: 10px;
}
.room-title {
    display: flex;
    align-items: center;
    gap: 8px;
}
.room-title i {
    width: 31px;
    height: 31px;
    border-radius: 8px;
}
.room-title span {
    display: flex;
    flex-direction: column;
}
.room-title small {
    color: #77869b;
    font-size: 10px;
}
.room-devices {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
    margin: 8px 0;
    color: #64748b;
}
.room-devices span {
    font-size: 10px;
}
.room-devices small,
.room-devices b {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.room-devices b {
    font-weight: 500;
}
.room-grid article > button,
.view-all {
    width: 100%;
    height: 23px;
    border: 1px solid #dce6f4;
    border-radius: 5px;
    color: #2a6ff0;
    font-size: 10px;
    font-weight: 800;
}
.bottom-grid {
    display: grid;
    grid-template-columns: 1.05fr 1fr;
    gap: 10px;
}
.device-list nav {
    display: flex;
    align-items: center;
    gap: 5px;
}
.device-list nav h2 {
    margin-right: 5px;
}
.device-list nav button {
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 10px;
}
.device-list nav .active {
    background: #eaf2ff;
    color: #1769ff;
}
.device-list table {
    width: 100%;
    margin-top: 5px;
    border-collapse: collapse;
    font-size: 10px;
}
.device-list th,
.device-list td {
    padding: 5px;
    text-align: left;
    border-bottom: 1px solid #edf1f6;
    color: #63738b;
}
.device-cell {
    display: flex;
    align-items: center;
    gap: 6px;
}
.device-cell i {
    display: grid;
    width: 24px;
    height: 24px;
    flex: none;
    place-items: center;
    border-radius: 7px;
}
.device-cell i.blue {
    background: #e9f2ff;
    color: #2871f5;
}
.device-cell i.green {
    background: #e7f9ee;
    color: #20b86a;
}
.device-cell i.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.device-cell i.purple {
    background: #eee9ff;
    color: #7651ee;
}
.device-cell i.teal {
    background: #e0f5f6;
    color: #0d9488;
}
.view-all {
    margin-top: 4px;
}
.activity p {
    display: grid;
    grid-template-columns: 38px 25px 1fr;
    align-items: center;
    gap: 7px;
    margin-top: 6px;
}
.activity time {
    color: #738198;
    font-size: 10px;
}
.activity i {
    display: grid;
    width: 24px;
    height: 24px;
    place-items: center;
    border-radius: 50%;
    background: #edf4ff;
    color: #3276f4;
}
.activity i.blue {
    background: #e9f2ff;
    color: #2871f5;
}
.activity i.green {
    background: #e7f9ee;
    color: #20b86a;
}
.activity i.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.activity i.purple {
    background: #eee9ff;
    color: #7651ee;
}
.activity i.teal {
    background: #e0f5f6;
    color: #0d9488;
}
.activity span {
    display: flex;
    flex-direction: column;
    font-size: 10px;
}
.activity small {
    color: #7d8ca1;
}
.right {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px;
}
.right .panel {
    padding: 14px;
}
.schedule-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
}
.schedule-title small {
    color: #7e8da3;
    font-size: 10px;
    font-weight: 400;
}
.schedule-title .tone-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    font-size: 14px;
}
.date-nav {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 12px 0 4px;
}
.date-arrow {
    display: grid;
    place-items: center;
    width: 24px;
    height: 24px;
    border: 1px solid #e1e8f1;
    border-radius: 7px;
    background: #fff;
    color: #41516a;
    cursor: pointer;
    transition: all 0.2s ease;
}
.date-arrow:hover {
    border-color: var(--tone-primary);
    color: var(--tone-primary);
    background: #edf4ff;
}
.date-info {
    display: flex;
    align-items: center;
    gap: 8px;
}
.date-info strong {
    color: #1c2a40;
    font-size: 12px;
}
.today-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    background: #e7f9ee;
    padding: 2px 8px;
    color: #20b86a;
    font-size: 10px;
    font-weight: 700;
}
.today-badge i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #20b86a;
}
.schedule-list {
    position: relative;
    margin: 8px 0 2px;
}
.schedule-list::before {
    content: '';
    position: absolute;
    top: 10px;
    bottom: 10px;
    left: calc(52px + 8px + 5px);
    width: 2px;
    background: #e2e9f2;
}
.schedule-list article {
    position: relative;
    display: grid;
    grid-template-columns: 52px 22px 1fr;
    align-items: flex-start;
    gap: 8px;
    padding: 8px 0;
    border-radius: 10px;
    transition: background 0.2s ease;
}
.schedule-list article:hover {
    background: #f7fafd;
}
.schedule-time {
    padding-top: 2px;
    font-size: 12px;
    font-weight: 900;
    text-align: right;
}
.timeline-node {
    position: relative;
    z-index: 1;
    width: 10px;
    height: 10px;
    margin-top: 4px;
    border-radius: 50%;
    background: #2875f4;
    box-shadow: 0 0 0 3px #fff, 0 0 0 6px #e9f2ff;
}
.schedule-body {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding-top: 1px;
}
.schedule-body b {
    color: #26354c;
    font-size: 12px;
}
.schedule-body small {
    color: #7e8da3;
    font-size: 10px;
    line-height: 1.4;
}
.schedule-list article.is-orange .schedule-time {
    color: var(--tone-orange);
}
.schedule-list article.is-orange .timeline-node {
    background: var(--tone-orange);
    box-shadow: 0 0 0 3px #fff, 0 0 0 6px var(--tone-orange-soft);
}
.schedule-list article.is-blue .schedule-time {
    color: #2871f5;
}
.schedule-list article.is-blue .timeline-node {
    background: #2871f5;
    box-shadow: 0 0 0 3px #fff, 0 0 0 6px #e9f2ff;
}
.schedule-list article.is-purple .schedule-time {
    color: #7651ee;
}
.schedule-list article.is-purple .timeline-node {
    background: #7651ee;
    box-shadow: 0 0 0 3px #fff, 0 0 0 6px #eee9ff;
}
.schedule-list article.is-teal .schedule-time {
    color: #0d9488;
}
.schedule-list article.is-teal .timeline-node {
    background: #0d9488;
    box-shadow: 0 0 0 3px #fff, 0 0 0 6px #e0f5f6;
}
.schedule-summary {
    display: flex;
    justify-content: center;
    gap: 4px;
    margin-top: 6px;
    border-top: 1px dashed #e2e9f2;
    padding-top: 8px;
    color: #7e8da3;
    font-size: 10px;
}
.schedule-summary b {
    color: var(--tone-primary);
}
.schedule-summary em {
    color: #20b86a;
    font-style: normal;
}
.device-count {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    margin: 11px 0;
    border: 1px solid #e4eaf2;
    border-radius: 9px;
    padding: 9px;
}
.device-count span {
    text-align: center;
    color: #74839a;
    font-size: 10px;
}
.device-count b {
    display: block;
    color: #1c2a40;
    font-size: 17px;
}
.warn {
    color: #f07821 !important;
}
.right h3 {
    margin: 10px 0 4px;
    font-size: 12px;
    font-weight: 900;
}
.alert {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    color: #41516a;
    font-size: 10px;
}
.alert em {
    border-radius: 6px;
    background: #edf4ff;
    padding: 2px 6px;
    color: #2b70ef;
    font-style: normal;
}
.quick {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 9px;
    margin-top: 12px;
}
.quick button {
    display: grid;
    grid-template-columns: 30px 1fr;
    align-items: center;
    text-align: left;
    border: 1px solid #e1e8f1;
    border-radius: 9px;
    padding: 9px;
    color: #26364e;
    font-size: 11px;
    font-weight: 900;
}
.quick button svg {
    grid-row: span 2;
    color: #2873f5;
}
.quick button.tone-purple svg {
    color: #7651ee;
}
.quick button.tone-blue svg {
    color: #2873f5;
}
.quick button.tone-green svg {
    color: #17ad62;
}
.quick button.tone-orange svg {
    color: var(--tone-orange);
}
.quick small {
    color: #8593a8;
    font-size: 9px;
    font-weight: 500;
}
.right footer {
    display: flex;
    justify-content: space-between;
    margin-top: 15px;
    color: #8a98aa;
    font-size: 10px;
}
@media (max-width: 1200px) {
    .stats {
        grid-template-columns: repeat(2, 1fr);
    }
    .status-row {
        grid-template-columns: repeat(3, 1fr);
    }
    .room-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .bottom-grid {
        grid-template-columns: 1fr;
    }
    .search {
        width: 190px;
    }
}
/* Readability and single-row room overview refinements. */
.overview {
    gap: 14px;
    padding: 20px;
    font-size: 14px;
}
.page-header h1 {
    font-size: 27px;
}
.page-header p {
    font-size: 15px;
}
.search {
    width: 280px;
    height: 42px;
}
.search input {
    font-size: 14px;
}
.stats article {
    min-height: 96px;
    padding: 16px;
}
.stats i {
    width: 50px;
    height: 50px;
}
.stats span {
    font-size: 14px;
}
.stats strong {
    font-size: 25px;
}
.stats small {
    font-size: 13px;
}
.panel h2 {
    font-size: 17px;
}
.panel a {
    font-size: 13px;
}
.status-row span {
    font-size: 12px;
}
.status-row b {
    font-size: 15px;
}
.status-row small {
    font-size: 11px;
}
.rooms {
    overflow: hidden;
}
.rooms header {
    padding: 14px 16px;
}
.room-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    overflow: hidden;
    padding: 0 14px 14px;
}
.room-grid article {
    min-width: 0;
    padding: 12px;
}
.room-title b {
    font-size: 15px;
}
.room-title small {
    font-size: 12px;
}
.room-devices span {
    font-size: 12px;
}
.room-grid article > button,
.view-all {
    height: 32px;
    font-size: 12px;
}
.device-list nav button {
    min-height: 32px;
    font-size: 12px;
}
.device-list table {
    font-size: 12px;
}
.device-list th,
.device-list td {
    padding: 7px 6px;
}
.activity time,
.activity span {
    font-size: 12px;
}
.activity small {
    font-size: 11px;
}
.date,
.right h3 {
    font-size: 14px;
}
.schedule time,
.schedule span {
    font-size: 13px;
}
.schedule small {
    font-size: 12px;
}
.device-count span,
.alert {
    font-size: 12px;
}
.device-count b {
    font-size: 20px;
}
.quick button {
    min-height: 62px;
    font-size: 13px;
}
.quick small,
.right footer {
    font-size: 11px;
}
@media (max-width: 1200px) {
    .room-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .room-grid article {
        min-width: 0;
    }
}

/* Device overview uses larger type while keeping every column in bounds. */
.device-list {
    min-width: 0;
    overflow: hidden;
}
.device-list nav {
    flex-wrap: wrap;
}
.device-list nav h2 {
    font-size: 16px;
}
.device-list nav button {
    min-height: 34px;
    padding: 6px 11px;
    font-size: 13px;
}
.device-list table {
    table-layout: fixed;
    font-size: 13px;
}
.device-list th,
.device-list td {
    overflow: hidden;
    padding: 8px 6px;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.device-list th:nth-child(1) { width: 27%; }
.device-list th:nth-child(2) { width: 13%; }
.device-list th:nth-child(3) { width: 13%; }
.device-list th:nth-child(4) { width: 21%; }
.device-list th:nth-child(5) { width: 16%; }
.device-list th:nth-child(6) { width: 10%; }
.device-cell {
    display: table-cell;
    font-weight: 800;
}
.device-cell i {
    display: inline-grid;
    margin-right: 6px;
    vertical-align: middle;
}
.device-cell span {
    vertical-align: middle;
}
.device-list .view-all {
    height: 34px;
    font-size: 13px;
}

@media (max-width: 760px) {
    .device-list nav h2 {
        width: 100%;
    }
    .device-list nav button {
        flex: 1;
        padding-right: 6px;
        padding-left: 6px;
        font-size: 12px;
    }
    .device-list table {
        font-size: 12px;
    }
    .device-list th,
    .device-list td {
        padding-right: 4px;
        padding-left: 4px;
    }
    .device-cell i {
        display: none;
    }
}

/* Keep the dashboard inside the application viewport without page scrolling. */
.overview {
    display: grid;
    grid-template-rows: auto auto auto auto minmax(0, 1fr);
    height: 100%;
    min-height: 0;
    gap: 8px;
    padding: 12px;
}
.overview .stats article {
    min-height: 76px;
    padding: 11px 13px;
}
.overview .stats i {
    width: 42px;
    height: 42px;
}
.overview .stats strong {
    font-size: 21px;
}
.home-status {
    padding: 10px 12px;
}
.home-status .status-row {
    gap: 8px;
    margin-top: 7px;
}
.room-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 7px;
    padding: 0 10px 10px;
}
.rooms header {
    padding: 9px 12px;
}
.room-grid article {
    padding: 8px;
}
.room-devices {
    grid-template-columns: 1fr;
    gap: 2px;
    margin: 5px 0;
}
.room-devices span {
    display: grid;
    grid-template-columns: 18px 38px minmax(0, 1fr);
    align-items: center;
}
.room-devices small,
.room-devices b {
    display: inline;
}
.bottom-grid {
    min-height: 0;
    overflow: hidden;
}
.bottom-grid > .panel {
    min-height: 0;
    overflow: hidden;
}
.right {
    display: grid;
    grid-template-rows: minmax(0, 1fr) auto auto;
    height: 100%;
    min-height: 0;
    gap: 8px;
    overflow: hidden;
    padding: 10px;
}
.right .panel {
    min-height: 0;
    overflow: hidden;
    padding: 10px;
}
.schedule-list article {
    padding: 5px 0;
}
.quick {
    gap: 6px;
    margin-top: 8px;
}
.quick button {
    min-height: 48px;
    padding: 6px;
}
.right footer {
    margin-top: 8px;
}

@media (max-height: 820px) {
    .overview {
        gap: 6px;
        padding: 8px;
    }
    .overview .stats article {
        min-height: 66px;
        padding: 8px 10px;
    }
    .overview .stats small,
    .status-row small,
    .room-grid article > button,
    .activity p:nth-of-type(n + 4),
    .device-list tbody tr:nth-child(n + 4) {
        display: none;
    }
    .panel {
        padding: 8px;
    }
}
</style>
