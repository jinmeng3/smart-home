<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink } from "vue-router";
import SvgIcon from "../components/common/SvgIcon.vue";
import PageHeader from "../components/common/PageHeader.vue";
import StatsCard from "../components/common/StatsCard.vue";
import { getDeviceTypeIcon } from "../components/device/deviceMeta";
import OverviewDialogs, {
    type OverviewDialog,
} from "../components/overview/OverviewDialogs.vue";
import type { HouseholdSchedule, ScheduleItem } from "../api/overview";
import { getHouseholdOverview, getHouseholdDevices } from "../api/overview";
import { useSettingsStore } from "../stores/settings";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import type {
  OverviewSummary,
  OverviewRoom,
} from "../types/overview";

// ── 概览展示用设备类型 ────────────────────────────────────────────────────────────

interface OverviewDeviceDisplay {
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

interface OverviewRoomDisplay {
  name: string;
  icon: string;
  count: number;
  light: string;
  air: string;
  extra: string;
  tone: string;
}

// ── 设备类型 → 图标/色调映射 ───────────────────────────────────────────────────────

const DEVICE_TONE_MAP: Record<string, string> = {
  light: "orange",
  air_conditioner: "blue",
  lock: "purple",
  camera: "purple",
  sensor: "green",
  socket: "teal",
  curtain: "teal",
};

const deviceTone = (type: string) => DEVICE_TONE_MAP[type] ?? "blue";
const formatDeviceTime = (value: string) => {
    if (!value) return "未知";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value.replace("T", " ").slice(0, 16);
    const parts = new Intl.DateTimeFormat("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).formatToParts(date);
    const get = (type: Intl.DateTimeFormatPartTypes) =>
        parts.find((part) => part.type === type)?.value ?? "";
    return `${get("year")}-${get("month")}-${get("day")} ${get("hour")}:${get("minute")}`;
};

// ── 状态 ──────────────────────────────────────────────────────────────────────────

const settingsStore = useSettingsStore();

const selectedTab = ref("全部设备");
const searchKeyword = ref("");
const refreshed = ref("加载中…");
const activeDialog = ref<OverviewDialog>(null);
const loading = ref(false);

const summary = ref<OverviewSummary>({
  device_total: 0,
  device_online: 0,
  running_automation_count: 0,
  alert_count: 0,
  monthly_energy_kwh: 0,
  energy_saving_rate: 0,
});
const rooms = ref<OverviewRoomDisplay[]>([]);
const devices = ref<OverviewDeviceDisplay[]>([]);
const activities = ref<{ time: string; icon: string; title: string; description: string; tone: string }[]>([]);
const scheduleItems = ref<ScheduleItem[]>([]);

// ── 计算属性 ──────────────────────────────────────────────────────────────────────

const onlineRate = computed(() => {
  if (summary.value.device_total === 0) return "0%";
  return `${((summary.value.device_online / summary.value.device_total) * 100).toFixed(1)}%`;
});

const offlineCount = computed(() =>
  summary.value.device_total - summary.value.device_online,
);

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

// ── 操作函数 ──────────────────────────────────────────────────────────────────────

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

const handleScheduleSaved = (schedule: HouseholdSchedule) => {
  scheduleItems.value = schedule.items;
};

// ── 数据加载 ──────────────────────────────────────────────────────────────────────

const loadOverviewData = async () => {
    loading.value = true;
    try {
        // 先确保账户与家庭信息已加载，再获取 householdId
        await settingsStore.loadAccountHome();
        const householdId = settingsStore.settings.account.householdId;
        if (!householdId) return;
        const [overview, deviceList] = await Promise.all([
            getHouseholdOverview(householdId),
            getHouseholdDevices(householdId),
        ]);

        // 概览摘要
        summary.value = overview.summary;

        // 房间卡片
        const formatDeviceSummary = (value: string) => value
            .replace(/DeviceStatus\.ONLINE|\bonline\b/gi, "在线")
            .replace(/DeviceStatus\.OFFLINE|\boffline\b/gi, "离线")
            .replace(/DeviceStatus\.RUNNING|\brunning\b/gi, "运行中")
            .replace(/DeviceStatus\.WARNING|\bwarning\b/gi, "告警");
        rooms.value = overview.rooms.map((room: OverviewRoom) => ({
            name: room.name,
            icon: "room",
            count: room.device_count,
            light: `${room.light_on}/${room.light_total} 开`,
            air: formatDeviceSummary(room.device_summaries[0] ?? `${room.temperature}°C`),
            extra: formatDeviceSummary(room.device_summaries[1] ?? "暂无更多设备"),
            tone: "blue",
        }));

        // 设备列表
        devices.value = deviceList.items.map((device) => ({
            id: device.id,
            name: device.name,
            room: device.room,
            status: device.status === "online" || device.status === "running" ? "在线" : "离线",
            detail: device.status === "running" ? "运行中" : device.status === "online" ? "在线" : device.status === "warning" ? "告警" : "离线",
            updatedAt: formatDeviceTime(device.lastOnline),
            icon: getDeviceTypeIcon(device.type),
            tone: deviceTone(device.type),
            frequent: false,
            favorite: false,
        }));

        // 从后端获取活动数据
        if (overview.activities && overview.activities.length > 0) {
            activities.value = (overview.activities as any[]).map((act: Record<string, unknown>) => ({
                time: (act.time || act.created_at || "") as string,
                icon: (act.icon || "info") as string,
                title: (act.title || act.name || "") as string,
                description: (act.description || "") as string,
                tone: (act.tone || "blue") as string,
            }));
        } else {
            activities.value = [];
        }

        // 从后端获取日程数据
        if (overview.schedule && overview.schedule.length > 0) {
            scheduleItems.value = overview.schedule as any;
        } else {
            scheduleItems.value = [];
        }

        refreshed.value = "刚刚";
    } catch (err) {
        refreshed.value = "加载失败";
        console.error("概览数据加载失败:", err);
    } finally {
        loading.value = false;
    }
};

useAuthenticatedLoader(loadOverviewData);</script>

<template>
    <div class="app-page-layout">
        <main class="overview page-shell page-enter">
            <PageHeader
                title="全屋总览"
                description="查看家庭运行状态、房间分布与设备总览"
                icon="home"
                tone="var(--color-primary-600)"
                soft="var(--color-primary-50)"
            >
                <label class="search"
                    ><SvgIcon name="search" size="sm" /><input
                        v-model="searchKeyword"
                        placeholder="搜索设备、场景或房间"
                /></label>
            </PageHeader>
            <div v-if="loading" class="loading-overlay">
                <div class="loading-spinner"></div>
                <span>加载中…</span>
            </div>
            <section class="stats card-grid-enter">
                <StatsCard
                    icon="online-device"
                    label="在线设备总数"
                    :value="String(summary.device_online)"
                    :detail="`在线率 ${onlineRate}`"
                    tone="blue"
                />
                <StatsCard
                    icon="automation"
                    label="自动化运行中"
                    :value="String(summary.running_automation_count)"
                    detail="已启用自动化"
                    tone="green"
                />
                <StatsCard
                    icon="notification"
                    label="今日告警"
                    :value="String(summary.alert_count)"
                    detail="需关注"
                    tone="orange"
                />
                <StatsCard
                    icon="air-quality"
                    label="本月节能概况"
                    :value="String(summary.monthly_energy_kwh)"
                    unit="kWh"
                    :detail="`节能 ${summary.energy_saving_rate}% ↑`"
                    tone="purple"
                />
            </section>
            <section class="panel rooms">
                <header>
                    <h2>房间概览</h2>
                    <a role="button" tabindex="0" @click="openDialog('distribution')">查看房间分布 ›</a>
                </header>
                <div class="room-grid card-grid-enter">
                    <article v-for="room in rooms.slice(0, 3)" :key="room.name">
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
                            >
                        </div>
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
                    <div class="device-table-scroll">
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
                                v-for="device in visibleDevices"
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
                    </div>
                    <RouterLink v-if="selectedTab === '全部设备'" class="view-all" to="/devices">
                        查看全部设备（{{ summary.device_total }}）→
                    </RouterLink>
                    <RouterLink v-else-if="selectedTab === '常用设备'" class="view-all" to="/devices?view=frequent">
                        查看全部常用设备（{{ visibleDevices.length }}）→
                    </RouterLink>
                    <RouterLink v-else class="view-all" to="/devices?view=favorite">
                        查看全部收藏设备（{{ visibleDevices.length }}）→
                    </RouterLink>
                </section>
            </div>
        </main>
        <div
            class="sidebar"
        >
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
                        v-for="item in scheduleItems.filter((entry) => entry.enabled).slice(0, 2)"
                        :key="`${item.time}-${item.name}`"
                        class="is-blue"
                        :style="{ '--schedule-color': item.color }"
                    >
                        <time class="schedule-time">{{ item.time }}</time>
                        <span class="timeline-node" aria-hidden="true"></span>
                        <div class="schedule-body">
                            <b>{{ item.name }}</b>
                            <small>{{ item.detail }}</small>
                        </div>
                    </article>
                </div>
                <button class="schedule-summary" type="button" @click="openDialog('schedule')">
                    查看全部 {{ scheduleItems.length }} 个计划
                    <SvgIcon name="chevron-right" size="sm" />
                </button>
            </section>
            <section class="panel">
                <header>
                    <h2>设备状态</h2>
                    <RouterLink class="more-link" to="/devices">更多</RouterLink>
                </header>
                <div class="device-count">
                    <span>总设备<b>{{ summary.device_total }}</b></span
                    ><span>在线设备<b class="ok">• {{ summary.device_online }}</b></span
                    ><span>离线设备<b class="warn">• {{ offlineCount }}</b></span>
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
            <section class="panel activity">
                <header>
                    <h2>今日活动 / 动态</h2>
                    <a role="button" tabindex="0" @click="openDialog('activity')">查看全部 ›</a>
                </header>
                <p
                    v-for="item in activities.slice(0, 5)"
                    :key="item.time + item.title"
                >
                    <time>{{ item.time }}</time
                    ><i :class="item.tone"
                        ><SvgIcon :name="item.icon" size="sm" /></i
                    ><span
                        ><b>{{ item.title }}</b
                        ><small>{{ item.description }}</small></span
                    >
                </p>
                <div v-if="!activities.length" class="activity-empty">
                    <SvgIcon name="log" />
                    <span>今日暂无设备、房间或自动化动态</span>
                </div>
            </section>
        </div>
        <OverviewDialogs
            v-model="activeDialog"
            :rooms="rooms"
            :activities="activities"
            @synced="handleSynced"
            @room-created="handleRoomCreated"
            @schedule-saved="handleScheduleSaved"
        />
    </div>
</template>

<style scoped>
.page-shell {
    height: 100%;
    overflow: hidden;
}
.app-page-layout > .overview {
    min-width: 0;
    overflow-x: hidden;
    overflow-y: auto;
}
.sidebar {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: 0;
    overflow-y: auto;
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
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    background: var(--color-card-bg);
    padding: 0 12px;
    color: var(--color-text-muted);
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
    background: var(--tone-primary-soft);
    color: var(--tone-primary);
}
.green {
    background: var(--tone-success-soft);
    color: var(--color-success);
}
.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}
.gray {
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
}

.panel {
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: var(--color-card-bg);
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
    color: var(--tone-primary);
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
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.status-row b {
    color: var(--color-text-primary);
    font-size: 13px;
}
.status-row small {
    white-space: nowrap;
}
.ok,
.online {
    color: var(--color-success) !important;
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
    border: 1px solid var(--color-border-default);
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
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.room-devices {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
    margin: 8px 0;
    color: var(--color-text-tertiary);
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
    border: 1px solid var(--color-border-default);
    border-radius: 5px;
    color: var(--tone-primary);
    font-size: 10px;
    font-weight: 800;
}
.bottom-grid {
    display: grid;
    flex-shrink: 0;
    grid-template-columns: 1fr;
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
    background: var(--tone-primary-soft);
    color: var(--tone-primary);
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
    border-bottom: 1px solid var(--color-border-subtle);
    color: var(--color-text-tertiary);
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
    background: var(--tone-primary-soft);
    color: var(--tone-primary);
}
.device-cell i.green {
    background: var(--tone-success-soft);
    color: var(--color-success);
}
.device-cell i.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.device-cell i.purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}
.device-cell i.teal {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
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
    color: var(--color-text-tertiary);
    font-size: 12px;
}
.activity i {
    display: grid;
    width: 24px;
    height: 24px;
    place-items: center;
    border-radius: 50%;
    background: var(--tone-primary-soft);
    color: var(--tone-primary);
}
.activity i.blue {
    background: var(--tone-primary-soft);
    color: var(--tone-primary);
}
.activity i.green {
    background: var(--tone-success-soft);
    color: var(--color-success);
}
.activity i.orange {
    background: var(--tone-orange-soft);
    color: var(--tone-orange);
}
.activity i.purple {
    background: var(--tone-purple-soft);
    color: var(--tone-purple);
}
.activity i.teal {
    background: var(--tone-teal-soft);
    color: var(--tone-teal);
}
.activity span {
    display: flex;
    flex-direction: column;
    font-size: 12px;
}
.activity small {
    color: var(--color-text-muted);
}
.schedule-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
}
.schedule-title small {
    color: var(--color-text-tertiary);
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
    border: 1px solid var(--color-border-default);
    border-radius: 7px;
    background: var(--color-card-bg);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
}
.date-arrow:hover {
    border-color: var(--tone-primary);
    color: var(--tone-primary);
    background: var(--tone-primary-soft);
}
.date-info {
    display: flex;
    align-items: center;
    gap: 8px;
}
.date-info strong {
    color: var(--color-text-primary);
    font-size: 12px;
}
.today-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    border-radius: 999px;
    background: var(--tone-success-soft);
    padding: 2px 8px;
    color: var(--color-success);
    font-size: 10px;
    font-weight: 700;
}
.today-badge i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-success);
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
    background: var(--color-border-default);
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
    background: var(--color-surface-hover);
}
.schedule-time {
    padding-top: 2px;
    font-size: 12px;
    font-weight: 900;
    text-align: right;
}
.schedule-list article[style] .schedule-time {
    color: var(--schedule-color);
}
.schedule-list article[style] .timeline-node {
    background: var(--schedule-color);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 6px color-mix(in srgb, var(--schedule-color) 18%, transparent);
}
.timeline-node {
    position: relative;
    z-index: 1;
    width: 10px;
    height: 10px;
    margin-top: 4px;
    border-radius: 50%;
    background: var(--tone-primary);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 6px var(--tone-primary-soft);
}
.schedule-body {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding-top: 1px;
}
.schedule-body b {
    color: var(--color-text-primary);
    font-size: 12px;
}
.schedule-body small {
    color: var(--color-text-tertiary);
    font-size: 10px;
    line-height: 1.4;
}
.schedule-list article.is-orange .schedule-time {
    color: var(--tone-orange);
}
.schedule-list article.is-orange .timeline-node {
    background: var(--tone-orange);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 6px var(--tone-orange-soft);
}
.schedule-list article.is-blue .schedule-time {
    color: var(--tone-primary);
}
.schedule-list article.is-blue .timeline-node {
    background: var(--tone-primary);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 6px var(--tone-primary-soft);
}
.schedule-list article.is-purple .schedule-time {
    color: var(--tone-purple);
}
.schedule-list article.is-purple .timeline-node {
    background: var(--tone-purple);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 6px var(--tone-purple-soft);
}
.schedule-list article.is-teal .schedule-time {
    color: var(--tone-teal);
}
.schedule-list article.is-teal .timeline-node {
    background: var(--tone-teal);
    box-shadow: 0 0 0 3px var(--color-card-bg), 0 0 0 6px var(--tone-teal-soft);
}
.schedule-summary {
    display: flex;
    justify-content: center;
    gap: 4px;
    margin-top: 6px;
    border-top: 1px dashed var(--color-border-default);
    padding-top: 8px;
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.schedule-summary b {
    color: var(--tone-primary);
}
.schedule-summary em {
    color: var(--color-success);
    font-style: normal;
}
.device-count {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    margin: 11px 0;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 9px;
}
.device-count span {
    text-align: center;
    color: var(--color-text-tertiary);
    font-size: 10px;
}
.device-count b {
    display: block;
    color: var(--color-text-primary);
    font-size: 17px;
}
.warn {
    color: var(--tone-warning) !important;
}
.panel h3 {
    margin: 10px 0 4px;
    font-size: 12px;
    font-weight: 900;
}
.alert {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    color: var(--color-text-secondary);
    font-size: 10px;
}
.alert em {
    border-radius: 6px;
    background: var(--tone-primary-soft);
    padding: 2px 6px;
    color: var(--tone-primary);
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
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 9px;
    color: var(--color-text-primary);
    font-size: 11px;
    font-weight: 900;
}
.quick button svg {
    grid-row: span 2;
    color: var(--tone-primary);
}
.quick button.tone-purple svg {
    color: var(--tone-purple);
}
.quick button.tone-blue svg {
    color: var(--tone-primary);
}
.quick button.tone-green svg {
    color: var(--color-success);
}
.quick button.tone-orange svg {
    color: var(--tone-orange);
}
.quick small {
    color: var(--color-text-muted);
    font-size: 9px;
    font-weight: 500;
}
.panel footer {
    display: flex;
    justify-content: space-between;
    margin-top: 15px;
    color: var(--color-text-muted);
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
    font-size: 13px;
}
.activity small {
    font-size: 12px;
}
.date,
.panel h3 {
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
.panel footer {
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
    display: flex;
    align-items: center;
    justify-content: center;
    height: 34px;
    font-size: 13px;
}

@media (max-width: 760px) {
    .overview {
        padding: 12px;
    }
    .device-list {
        overflow-x: auto;
    }
    .device-list table {
        min-width: 620px;
    }
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

@media not all {
/* Legacy layout experiments retained temporarily but disabled. */
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
    grid-template-columns: 1fr;
}
.bottom-grid > .panel {
    min-height: 0;
    overflow: hidden;
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
.panel footer {
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

/* Medium desktop layout (the application keeps a fixed 330px right rail). */
@media (max-width: 1380px) {
    .overview {
        grid-template-rows: auto auto auto minmax(122px, 0.58fr) minmax(178px, 1fr);
        gap: 7px;
        padding: 8px;
    }
    .overview .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
    }
    .overview .stats article {
        min-height: 66px;
        padding: 8px 12px;
    }
    .overview .stats i {
        width: 38px;
        height: 38px;
    }
    .overview .stats span,
    .overview .stats small {
        white-space: nowrap;
    }
    .overview .stats strong {
        font-size: 20px;
    }
    .home-status {
        padding: 7px 9px;
    }
    .home-status .status-row {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 5px 7px;
    }
    .home-status .status-row > div,
    .home-status .status-row > div:nth-child(n + 5) {
        display: flex;
        min-height: 43px;
        padding: 5px 7px;
    }
    .home-status .status-row i {
        width: 30px;
        height: 30px;
    }
    .home-status .status-row span,
    .home-status .status-row b,
    .home-status .status-row small {
        word-break: keep-all;
        white-space: nowrap;
    }
    .room-grid {
        grid-template-rows: minmax(76px, 1fr);
        gap: 7px;
        padding: 0 8px 8px;
    }
    .room-grid article {
        min-height: 76px;
        grid-template-columns: minmax(0, 1fr);
        grid-template-rows: auto 1fr;
        gap: 3px;
        padding: 6px 8px;
    }
    .room-title i {
        width: 30px;
        height: 30px;
    }
    .room-devices {
        display: flex;
        align-items: center;
        align-self: end;
        justify-content: space-between;
        gap: 5px;
        margin: 0;
        border-left: 0;
        padding-left: 0;
    }
    .room-devices span {
        display: flex;
        min-width: 0;
        min-height: 18px;
        align-items: center;
        gap: 3px;
        white-space: nowrap;
    }
    .room-devices small {
        display: none;
    }
    .bottom-grid {
        grid-template-columns: minmax(0, 1fr);
    }
    .bottom-grid .activity {
        display: none;
    }
    .device-list nav {
        flex-wrap: nowrap;
    }
    .device-list nav h2 {
        width: auto;
        white-space: nowrap;
    }
    .right {
        gap: 7px;
        padding: 8px;
    }
    .right .panel {
        padding: 9px;
    }
    .quick button {
        min-height: 46px;
        padding: 6px;
    }
}

/* Prevent fixed-height cards from sharing or crossing visual boundaries. */
.room-grid article {
    overflow: hidden;
}
.room-devices {
    align-self: end;
    gap: 5px;
    margin-top: 8px;
}
.room-devices span {
    min-height: 18px;
}
/* Prevent fixed-height cards from sharing or crossing visual boundaries. */
/* Final overview composition: one clear vertical reading flow. */
.overview {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto auto auto minmax(0, 1fr) minmax(190px, 0.82fr);
    grid-template-areas:
        "header"
        "stats"
        "home"
        "rooms"
        "bottom";
    gap: 10px;
    padding: 12px;
}
.overview .stats article {
    min-height: 78px;
}
.home-status {
    padding: 10px 12px;
}
.home-status h2 {
    display: none;
}
.home-status .status-row {
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 8px;
    margin-top: 0;
}
.home-status .status-row > div {
    border: 0;
    background: var(--color-surface-subtle);
    padding: 7px 9px;
}
.home-status .status-row i {
    width: 34px;
    height: 34px;
}
.rooms {
    display: flex;
    min-height: 0;
    flex-direction: column;
}
.rooms header {
    flex: none;
    padding: 10px 14px;
}
.room-grid {
    min-height: 0;
    flex: 1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-template-rows: minmax(0, 1fr);
    gap: 8px;
    padding: 0 12px 12px;
}
.room-grid article {
    grid-template-rows: auto 1fr;
    padding: 9px 10px;
}
.room-title i {
    width: 30px;
    height: 30px;
}
.room-devices {
    align-content: center;
    margin: 4px 0 0;
}
.bottom-grid {
    grid-template-columns: 1fr;
    gap: 10px;
}
.bottom-grid > .panel {
    padding: 10px 12px;
}
.schedule-list {
    min-height: 0;
    margin: 5px 0;
}
.schedule-list article {
    grid-template-columns: 46px 18px minmax(0, 1fr);
    gap: 6px;
    padding: 5px 0;
}
.schedule-list::before {
    left: 57px;
}
.schedule-body small {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.schedule-summary {
    display: flex;
    width: 100%;
    height: 32px;
    flex: none;
    align-items: center;
    justify-content: center;
    gap: 5px;
    margin-top: auto;
    border: 0;
    border-radius: 8px;
    padding: 0;
    color: var(--tone-primary);
    background: var(--tone-primary-soft);
    font-size: 12px;
    font-weight: 800;
}

@media (max-width: 1380px) {
    .home-status .status-row {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .home-status .status-row > div:nth-child(n) {
        display: flex;
    }
}

@media (max-height: 820px) {
    .overview {
        grid-template-rows: auto auto auto minmax(0, 1fr) minmax(170px, 0.68fr);
        gap: 7px;
        padding: 8px;
    }
    .home-status .status-row {
        grid-template-columns: repeat(6, minmax(0, 1fr));
    }
    .home-status .status-row > div:nth-child(n) {
        display: flex;
    }
    .home-status .status-row small {
        display: none;
    }
    .room-title small {
        font-size: 10px;
    }
}

/* Spacious dashboard layout: overview and rooms form the visual center. */
.overview {
    grid-template-columns: minmax(250px, 0.78fr) minmax(0, 1.72fr);
    grid-template-rows: auto auto minmax(0, 1.15fr) minmax(0, 0.9fr);
    grid-template-areas:
        "header header"
        "stats stats"
        "home rooms"
        "bottom bottom";
    gap: 12px;
    padding: 14px;
}
.overview > :deep(.page-header) {
    grid-area: header;
}
.overview > .stats {
    grid-area: stats;
}
.overview > .home-status {
    grid-area: home;
}
.overview > .rooms {
    grid-area: rooms;
}
.overview > .bottom-grid {
    grid-area: bottom;
}
.overview .stats {
    gap: 12px;
}
.overview .stats article {
    min-height: 82px;
    padding: 12px 14px;
}
.home-status,
.rooms,
.bottom-grid > .panel {
    min-height: 0;
}
.home-status {
    padding: 14px;
}
.home-status .status-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-content: start;
    gap: 13px 10px;
    margin-top: 14px;
}
.home-status .status-row > div {
    min-width: 0;
    border-radius: 10px;
    background: var(--color-surface-subtle);
    padding: 8px;
}
.home-status .status-row i {
    width: 36px;
    height: 36px;
}
.room-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    align-content: start;
    gap: 10px;
    padding: 0 12px 12px;
}
.rooms header {
    padding: 12px 14px;
}
.room-grid article {
    display: grid;
    min-height: 0;
    grid-template-rows: auto 1fr auto;
    border-color: var(--color-border-default);
    padding: 10px;
    background: linear-gradient(145deg, var(--color-card-bg), var(--color-surface-subtle));
}
.room-devices {
    display: grid;
    grid-template-columns: 1fr;
    gap: 3px;
    margin: 7px 0;
}
.room-devices span {
    grid-template-columns: 18px 36px minmax(0, 1fr);
}
.bottom-grid {
    grid-template-columns: 1fr;
    gap: 12px;
}
.bottom-grid > .panel {
    padding: 12px;
}
.activity p {
    margin-top: 5px;
}

@media (max-width: 1380px) {
    .overview {
        grid-template-columns: minmax(220px, 0.7fr) minmax(0, 1.8fr);
    }
    .home-status .status-row {
        grid-template-columns: 1fr;
        gap: 6px;
    }
    .home-status .status-row > div:nth-child(n + 5) {
        display: none;
    }
}

@media (max-height: 820px) {
    .overview {
        grid-template-rows: auto auto minmax(0, 1fr) minmax(0, 0.72fr);
        gap: 8px;
        padding: 9px;
    }
    .home-status .status-row {
        gap: 5px;
        margin-top: 7px;
    }
    .home-status .status-row > div {
        padding: 5px 7px;
    }
    .room-grid {
        gap: 7px;
        padding: 0 8px 8px;
    }
    .room-grid article {
        padding: 7px;
    }
}
/* Authoritative layout overrides must remain last in this scoped stylesheet. */
.overview {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto auto auto minmax(132px, 0.58fr) minmax(200px, 1fr);
    grid-template-areas: "header" "stats" "home" "rooms" "bottom";
}
.home-status {
    padding: 9px 12px;
}
.home-status h2 {
    display: none;
}
.home-status .status-row {
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 8px;
    margin-top: 0;
}
.home-status .status-row > div,
.home-status .status-row > div:nth-child(n + 5) {
    display: flex;
    padding: 7px 9px;
}
.rooms {
    display: flex;
    min-height: 0;
    flex-direction: column;
}
.room-grid {
    min-height: 0;
    flex: 1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-template-rows: minmax(72px, 1fr);
    align-content: stretch;
    align-items: stretch;
    gap: 8px;
    padding: 0 10px 8px;
}
.room-grid article {
    min-height: 72px;
    overflow: hidden;
    grid-template-columns: minmax(105px, 0.72fr) minmax(0, 1.28fr);
    grid-template-rows: minmax(0, 1fr);
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
}
.rooms header {
    padding: 7px 12px;
}
.room-title i {
    width: 36px;
    height: 36px;
}
.room-title {
    min-width: 0;
}
.room-title b {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.room-title small {
    line-height: 1.1;
}
.room-devices {
    align-self: center;
    gap: 6px;
    margin: 0;
    border-left: 1px solid var(--color-border-subtle);
    padding-left: 12px;
}
.room-devices span {
    grid-template-columns: 18px 38px minmax(0, 1fr);
    min-height: 22px;
    align-items: center;
}
.bottom-grid {
    grid-template-columns: 1fr;
}

@media (max-height: 820px) {
    .overview {
        grid-template-rows: auto auto auto minmax(124px, 0.5fr) minmax(174px, 1fr);
    }
    .home-status .status-row {
        grid-template-columns: repeat(6, minmax(0, 1fr));
    }
    .home-status .status-row small {
        display: none;
    }
}
@media (max-width: 1380px) {
    .overview {
        grid-template-rows: auto auto auto minmax(122px, 0.58fr) minmax(178px, 1fr);
        gap: 7px;
        padding: 8px;
    }
    .overview .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
    }
    .overview .stats article {
        min-height: 66px;
        padding: 8px 12px;
    }
    .overview .stats span,
    .overview .stats small {
        word-break: keep-all;
        white-space: nowrap;
    }
    .home-status .status-row {
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 5px 7px;
    }
    .home-status .status-row > div,
    .home-status .status-row > div:nth-child(n + 5) {
        display: flex;
        min-height: 43px;
        padding: 5px 7px;
    }
    .home-status .status-row span,
    .home-status .status-row b,
    .home-status .status-row small {
        word-break: keep-all;
        white-space: nowrap;
    }
    .room-grid {
        grid-template-rows: minmax(76px, 1fr);
    }
    .room-grid article {
        min-height: 76px;
        grid-template-columns: minmax(0, 1fr);
        grid-template-rows: auto 1fr;
        gap: 3px;
        padding: 6px 8px;
    }
    .room-devices {
        display: flex;
        align-items: center;
        align-self: end;
        justify-content: space-between;
        gap: 5px;
        margin: 0;
        border-left: 0;
        padding-left: 0;
    }
    .room-devices span {
        display: flex;
        min-width: 0;
        min-height: 18px;
        gap: 3px;
        white-space: nowrap;
    }
    .room-devices small {
        display: none;
    }
    .bottom-grid {
        grid-template-columns: minmax(0, 1fr);
    }
    .bottom-grid .activity {
        display: none;
    }
}
}

/* Single authoritative dashboard layout. */
.overview {
    display: grid;
    height: 100%;
    min-height: 0;
    grid-template-rows: auto auto auto 132px minmax(180px, 1fr);
    gap: 8px;
    overflow: hidden;
    padding: 10px;
}
.overview .stats {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
}
.overview .stats article {
    min-width: 0;
    min-height: 76px;
    padding: 10px;
}
.overview .stats span,
.overview .stats small {
    word-break: keep-all;
}
.home-status {
    padding: 8px 10px;
}
.home-status h2 {
    display: none;
}
.home-status .status-row {
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 6px;
    margin: 0;
}
.home-status .status-row > div {
    min-width: 0;
    border-radius: 9px;
    background: var(--color-surface-subtle);
    padding: 6px;
}
.home-status .status-row span,
.home-status .status-row b,
.home-status .status-row small {
    word-break: keep-all;
}
.rooms {
    display: flex;
    min-height: 0;
    flex-direction: column;
    overflow: hidden;
    padding: 0;
}
.rooms header {
    flex: none;
    padding: 8px 12px;
}
.room-grid {
    display: grid;
    min-height: 0;
    flex: 1;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    overflow: hidden;
    padding: 0 10px 9px;
}
.room-grid article {
    display: grid;
    min-width: 0;
    min-height: 0;
    grid-template-columns: minmax(90px, 0.8fr) minmax(0, 1.2fr);
    align-items: center;
    gap: 8px;
    overflow: hidden;
    padding: 8px;
}
.room-title {
    min-width: 0;
}
.room-title i {
    width: 32px;
    height: 32px;
}
.room-devices {
    display: grid;
    min-width: 0;
    grid-template-columns: 1fr;
    gap: 5px;
    margin: 0;
    border-left: 1px solid var(--color-border-subtle);
    padding-left: 9px;
}
.room-devices span {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
}
.bottom-grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
    overflow: hidden;
}
.bottom-grid .device-list {
    grid-column: 1 / -1;
}
.bottom-grid .activity {
    display: none;
}
.bottom-grid > .panel {
    min-height: 0;
    overflow: hidden;
    padding: 10px;
}
.right {
    display: grid;
    height: 100%;
    min-height: 0;
    grid-template-rows: minmax(0, 1fr) auto auto;
    gap: 8px;
    overflow: hidden;
    padding: 9px;
}
.right .panel {
    min-height: 0;
    overflow: hidden;
    padding: 10px;
}
.right > .panel:first-child {
    display: grid;
    grid-template-rows: auto auto minmax(0, 1fr) 32px;
}
.right .schedule-list {
    min-height: 0;
    overflow: hidden;
}
.right .schedule-summary {
    margin: 0;
}

@media (max-width: 1380px) {
    .overview {
        grid-template-rows: auto auto auto 126px minmax(170px, 1fr);
    }
    .overview .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .overview .stats article {
        min-height: 62px;
        padding: 7px 10px;
    }
    .overview .stats span,
    .overview .stats small,
    .home-status span,
    .home-status b,
    .home-status small {
        white-space: nowrap;
    }
    .home-status .status-row {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
    .home-status .status-row > div {
        min-height: 40px;
        padding: 4px 7px;
    }
    .room-grid article {
        grid-template-columns: minmax(0, 1fr);
        grid-template-rows: auto auto;
        gap: 3px;
        padding: 6px 8px;
    }
    .room-devices {
        display: flex;
        justify-content: space-between;
        border-left: 0;
        padding-left: 0;
    }
    .room-devices small {
        display: none;
    }
    .bottom-grid {
        grid-template-columns: minmax(0, 1fr);
    }
    .bottom-grid .activity {
        display: none;
    }
}

/* ── 加载状态 ────────────────────────────────────────────────────────────────────── */
.loading-overlay {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    height: 200px;
    color: var(--color-text-muted);
    font-size: 14px;
}
.loading-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--color-border-default);
    border-top-color: var(--tone-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}

/* 设备概览使用独立滚动区，底部入口始终保留在可视区域。 */
.overview {
    grid-template-rows: auto auto 132px minmax(180px, 1fr);
}
.bottom-grid > .device-list {
    display: grid;
    min-height: 0;
    grid-template-rows: auto minmax(0, 1fr) 38px;
    overflow: hidden;
    padding-bottom: 0;
}
.device-table-scroll {
    min-height: 0;
    overflow: auto;
    scrollbar-color: var(--color-border-strong) transparent;
    scrollbar-width: thin;
}
.device-table-scroll table {
    width: 100%;
}
.device-table-scroll thead {
    position: sticky;
    top: 0;
    background: var(--color-card-bg);
    box-shadow: 0 1px 0 var(--color-border-subtle);
    z-index: 1;
}
.device-list .view-all {
    position: relative;
    height: 38px;
    border-top: 1px solid var(--color-border-subtle);
    background: linear-gradient(180deg, var(--color-card-bg), var(--color-primary-50));
    color: var(--color-primary-600);
    font-weight: 900;
    z-index: 2;
}
.device-list .view-all:hover {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
}
.activity-empty {
    display: flex;
    min-height: 110px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    color: var(--color-text-tertiary);
    font-size: 12px;
    text-align: center;
}
.activity-empty svg {
    color: var(--color-primary-300);
}
</style>
