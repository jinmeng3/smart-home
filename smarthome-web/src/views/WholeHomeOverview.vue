<script setup lang="ts">
import { ref, shallowRef } from "vue";
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
const refreshed = ref("5 分钟前");
const activeDialog = ref<OverviewDialog>(null);

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
                <h2>家庭概况</h2>
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
                            </tr>
                        </thead>
                        <tbody>
                            <tr
                                v-for="row in [
                                    [
                                        '客厅吸顶灯',
                                        '客厅',
                                        '在线',
                                        '亮度 80%',
                                        '10:15',
                                        'light',
                                        'orange',
                                    ],
                                    [
                                        '客厅空调',
                                        '客厅',
                                        '在线',
                                        '26°C 制冷',
                                        '10:15',
                                        'air-conditioner',
                                        'blue',
                                    ],
                                    [
                                        '主卧空调',
                                        '主卧',
                                        '在线',
                                        '26°C 制冷',
                                        '10:14',
                                        'air-conditioner',
                                        'blue',
                                    ],
                                    [
                                        '智能门锁',
                                        '玄关',
                                        '在线',
                                        '已上锁',
                                        '10:13',
                                        'lock',
                                        'purple',
                                    ],
                                    [
                                        '空气净化器',
                                        '客厅',
                                        '在线',
                                        '自动模式',
                                        '10:12',
                                        'sensor',
                                        'green',
                                    ],
                                ]"
                                :key="row[0]"
                            >
                                <td class="device-cell">
                                    <i :class="row[6]"
                                        ><SvgIcon :name="row[5]" size="sm" /></i
                                    ><span>{{ row[0] }}</span>
                                </td>
                                <td>{{ row[1] }}</td>
                                <td class="online">● {{ row[2] }}</td>
                                <td>{{ row[3] }}</td>
                                <td>{{ row[4] }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <button class="view-all">查看全部设备（28）⌄</button>
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
                    <h2>家庭日程 / 自动化计划</h2>
                    <a role="button" tabindex="0" @click="openDialog('schedule')">更多</a>
                </header>
                <h3 class="date">‹　2025年5月20日 星期二　›</h3>
                <div
                    class="schedule"
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
                >
                    <time>{{ item[0] }}</time
                    ><span :class="item[3]"
                        ><b>{{ item[1] }}</b
                        ><small>{{ item[2] }}</small></span
                    >
                </div>
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
    overflow: auto;
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
    background: #fff0df;
    color: #ff8a1f;
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
    background: #fff0df;
    color: #ff8a1f;
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
    background: #fff0df;
    color: #ff8a1f;
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
.date {
    text-align: center;
    margin: 12px 0;
    font-size: 12px;
}
.schedule {
    display: grid;
    grid-template-columns: 52px 1fr;
    gap: 8px;
    margin: 11px 0;
}
.schedule time {
    font-size: 11px;
    font-weight: 900;
}
.schedule span {
    display: flex;
    flex-direction: column;
    border-left: 3px solid #2875f4;
    padding-left: 9px;
    font-size: 11px;
}
.schedule span.blue {
    border-left-color: #2875f4;
}
.schedule span.orange {
    border-left-color: #ff8a1f;
}
.schedule span.purple {
    border-left-color: #7651ee;
}
.schedule span.teal {
    border-left-color: #0d9488;
}
.schedule small {
    margin-top: 4px;
    color: #7e8da3;
    font-size: 10px;
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
    color: #ff8a1f;
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
    display: flex;
    grid-template-columns: none;
    gap: 10px;
    overflow-x: auto;
    padding: 0 14px 14px;
    scrollbar-width: thin;
}
.room-grid article {
    min-width: 235px;
    flex: 1 0 235px;
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
        display: flex;
    }
    .room-grid article {
        min-width: 235px;
        flex-basis: 235px;
    }
}
</style>
