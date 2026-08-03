<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";

export type OverviewDialog =
    "mode" | "room" | "inspection" | "devices" | "schedule" | "sync" | null;

interface Props {
    modelValue: OverviewDialog;
}

const props = defineProps<Props>();
const emit = defineEmits<{
    "update:modelValue": [value: OverviewDialog];
    synced: [];
    "room-created": [name: string];
}>();

const loading = ref(false);
const selectedMode = ref("home");
const selectedScope = ref("all");
const roomName = ref("");
const roomType = ref("书房");
const floor = ref("二楼");
const selectedIcon = ref("room");
const selectedColor = ref("#3478f6");
const roomDevices = reactive(["灯光", "空调", "传感器", "窗帘"]);
const inspectionScope = ref("all");
const inspectionItems = reactive([
    "在线状态",
    "电量",
    "网络连接",
    "响应延迟",
    "固件版本",
    "异常告警",
]);
const autoSync = ref(true);
const syncOptions = reactive([
    "名称与房间归属",
    "电量与在线状态",
    "检测新接入设备",
]);

const modes = [
    {
        key: "home",
        name: "回家模式",
        icon: "home",
        hint: "开启常用照明、舒适空调",
    },
    {
        key: "away",
        name: "离家模式",
        icon: "security",
        hint: "关闭灯光、开启安防",
    },
    {
        key: "sleep",
        name: "睡眠模式",
        icon: "air-quality",
        hint: "柔和灯光、关闭部分设备",
    },
    {
        key: "movie",
        name: "观影模式",
        icon: "scene",
        hint: "客厅灯光调暗、窗帘关闭",
    },
] as const;
const scopes = ["客厅", "主卧", "次卧", "厨房", "卫生间", "阳台"];
const roomTypes = ["书房", "儿童房", "影音室", "储物间"];
const roomIcons = [
    "room",
    "home",
    "device-management",
    "air-conditioner",
    "curtain",
    "more",
];
const colors = [
    "#3478f6",
    "#20b86a",
    "#19b6bd",
    "#825bea",
    "#ff8a1f",
    "#f05252",
];
const deviceRows = [
    ["客厅吸顶灯", "客厅", "在线", "—", "10:15", "正常"],
    ["客厅空调", "客厅", "在线", "26°C", "10:15", "正常"],
    ["主卧空调", "主卧", "在线", "26°C", "10:14", "正常"],
    ["智能门锁", "玄关", "在线", "100%", "10:13", "正常"],
    ["空气净化器", "客厅", "在线", "68%", "10:12", "正常"],
    ["厨房烟感", "厨房", "在线", "18%", "10:10", "告警"],
    ["阳台门磁", "阳台", "在线", "100%", "10:09", "正常"],
    ["客厅摄像头", "客厅", "离线", "—", "09:58", "离线"],
];
const schedules = reactive([
    {
        time: "07:00",
        name: "起床模式",
        detail: "窗帘打开 · 卧室灯亮 · 空调制热 24°C",
        color: "#ff9418",
    },
    {
        time: "19:00",
        name: "回家模式",
        detail: "玄关灯亮 · 空调制冷 26°C · 新风开启",
        color: "#3478f6",
    },
    {
        time: "22:00",
        name: "离家模式",
        detail: "关闭灯光 · 安防布防 · 监控夜视",
        color: "#20b86a",
    },
    {
        time: "23:00",
        name: "睡眠模式",
        detail: "灯光渐暗 · 窗帘关闭 · 安防设防",
        color: "#825bea",
    },
]);

const visible = computed({
    get: () => props.modelValue !== null,
    set: (value: boolean) => {
        if (!value) emit("update:modelValue", null);
    },
});

const title = computed(
    () =>
        ({
            mode: "切换全屋模式",
            room: "添加房间",
            inspection: "全屋巡检",
            devices: "设备状态总览",
            schedule: "编辑家庭日程",
            sync: "同步设备状态",
        })[props.modelValue ?? "mode"],
);

const description = computed(
    () =>
        ({
            mode: "快速应用家庭场景模式到全屋设备",
            room: "创建新的房间并绑定设备，完善家庭空间管理",
            inspection: "快速检测全屋设备、网络与自动化状态",
            devices: "查看在线、离线与异常设备的详细状态",
            schedule: "管理家庭日程与自动化计划",
            sync: "刷新并同步全屋设备的最新状态与连接信息",
        })[props.modelValue ?? "mode"],
);

const confirmText = computed(
    () =>
        ({
            mode: "立即切换",
            room: "创建房间",
            inspection: "开始巡检",
            devices: "导出列表",
            schedule: "保存计划",
            sync: "开始同步",
        })[props.modelValue ?? "mode"],
);

const toggle = (list: string[], value: string) => {
    const index = list.indexOf(value);
    if (index >= 0) list.splice(index, 1);
    else list.push(value);
};

const confirm = async () => {
    if (props.modelValue === "room" && !roomName.value.trim()) {
        ElMessage.warning("请输入房间名称");
        return;
    }
    loading.value = true;
    await new Promise((resolve) => window.setTimeout(resolve, 450));
    if (props.modelValue === "room")
        emit("room-created", roomName.value.trim());
    if (props.modelValue === "sync") emit("synced");
    ElMessage.success(`${title.value}操作成功`);
    loading.value = false;
    emit("update:modelValue", null);
};

watch(
    () => props.modelValue,
    (value) => {
        if (value === "room") roomName.value = "";
    },
);
</script>

<template>
    <BaseSmartModal
        v-model="visible"
        :title="title"
        :description="description"
        :icon="modelValue === 'sync' ? 'refresh' : undefined"
        :width="
            modelValue === 'devices' ? 860 : modelValue === 'room' ? 760 : 720
        "
        :loading="loading"
        :confirm-text="confirmText"
        @confirm="confirm"
    >
        <div v-if="modelValue === 'mode'" class="mode-layout">
            <div class="mode-grid">
                <button
                    v-for="mode in modes"
                    :key="mode.key"
                    type="button"
                    class="mode-card"
                    :class="{ selected: selectedMode === mode.key }"
                    @click="selectedMode = mode.key"
                >
                    <span><SvgIcon :name="mode.icon" size="lg" /></span>
                    <b>{{ mode.name }}</b
                    ><small>{{ mode.hint }}</small>
                    <i v-if="selectedMode === mode.key">✓</i>
                </button>
            </div>
            <section class="side-stack">
                <div class="box">
                    <b>应用范围</b>
                    <div class="chips">
                        <button
                            v-for="scope in scopes"
                            :key="scope"
                            type="button"
                            :class="{ active: selectedScope === scope }"
                            @click="selectedScope = scope"
                        >
                            {{ scope }}
                        </button>
                    </div>
                </div>
                <label class="switch-row"
                    ><span
                        >同步执行自动化联动<small
                            >切换模式时同时运行关联自动化</small
                        ></span
                    ><input v-model="autoSync" type="checkbox"
                /></label>
                <div class="box impact">
                    <b>预览影响</b>
                    <p>
                        <SvgIcon name="light" size="sm" />灯光
                        <strong>12 台</strong>
                    </p>
                    <p>
                        <SvgIcon name="air-conditioner" size="sm" />空调
                        <strong>3 台</strong>
                    </p>
                    <p>
                        <SvgIcon name="curtain" size="sm" />窗帘
                        <strong>4 台</strong>
                    </p>
                    <small>共影响 20 台设备</small>
                </div>
            </section>
        </div>

        <div v-else-if="modelValue === 'room'" class="room-layout">
            <div class="form-stack">
                <label
                    >房间名称<input
                        v-model="roomName"
                        maxlength="20"
                        placeholder="请输入房间名称"
                    /><small>{{ roomName.length }}/20</small></label
                >
                <div class="form-row">
                    <label
                        >房间类型<select v-model="roomType">
                            <option v-for="type in roomTypes" :key="type">
                                {{ type }}
                            </option>
                        </select></label
                    ><label
                        >楼层/区域<select v-model="floor">
                            <option>一楼</option>
                            <option>二楼</option>
                            <option>地下室</option>
                        </select></label
                    >
                </div>
                <fieldset>
                    <legend>房间图标</legend>
                    <button
                        v-for="icon in roomIcons"
                        :key="icon"
                        type="button"
                        :class="{ active: selectedIcon === icon }"
                        @click="selectedIcon = icon"
                    >
                        <SvgIcon :name="icon" />
                    </button>
                </fieldset>
                <fieldset>
                    <legend>图标颜色</legend>
                    <button
                        v-for="color in colors"
                        :key="color"
                        type="button"
                        class="color-dot"
                        :class="{ active: selectedColor === color }"
                        :style="{ background: color }"
                        @click="selectedColor = color"
                    />
                </fieldset>
                <fieldset class="device-bind">
                    <legend>绑定设备</legend>
                    <button
                        v-for="device in [
                            '灯光',
                            '空调',
                            '传感器',
                            '窗帘',
                            '摄像头',
                            '门锁',
                        ]"
                        :key="device"
                        type="button"
                        :class="{ active: roomDevices.includes(device) }"
                        @click="toggle(roomDevices, device)"
                    >
                        <SvgIcon
                            :name="
                                device === '传感器'
                                    ? 'sensor'
                                    : device === '摄像头'
                                      ? 'camera'
                                      : device === '门锁'
                                        ? 'lock'
                                        : device === '灯光'
                                          ? 'light'
                                          : device === '空调'
                                            ? 'air-conditioner'
                                            : 'curtain'
                            "
                        />{{ device }}
                    </button>
                </fieldset>
            </div>
            <aside class="room-preview">
                <b>房间预览</b>
                <div>
                    <span :style="{ color: selectedColor }"
                        ><SvgIcon :name="selectedIcon" size="lg"
                    /></span>
                    <h3>{{ roomName || roomType }}</h3>
                    <p>{{ roomDevices.length }} 个设备</p>
                    <small>当前未启用自动化</small>
                </div>
                <ul>
                    <li>
                        楼层/区域 <b>{{ floor }}</b>
                    </li>
                    <li>
                        房间类型 <b>{{ roomType }}</b>
                    </li>
                    <li>
                        设备数量 <b>{{ roomDevices.length }}</b>
                    </li>
                </ul>
            </aside>
        </div>

        <div v-else-if="modelValue === 'inspection'" class="inspection">
            <div class="inspection-top">
                <section class="box">
                    <b>巡检范围</b>
                    <div class="chips wide">
                        <button
                            v-for="item in [
                                ['all', '全部设备'],
                                ['light', '灯光'],
                                ['air', '空调'],
                                ['lock', '门锁'],
                                ['sensor', '传感器'],
                                ['automation', '自动化'],
                            ]"
                            :key="item[0]"
                            type="button"
                            :class="{ active: inspectionScope === item[0] }"
                            @click="inspectionScope = item[0]"
                        >
                            {{ item[1] }}
                        </button>
                    </div>
                    <b>巡检项目</b>
                    <div class="check-grid">
                        <label v-for="item in inspectionItems" :key="item"
                            ><input type="checkbox" checked />{{ item }}</label
                        >
                    </div>
                </section>
                <aside class="estimate">
                    <small>预计检测</small><strong>36</strong
                    ><span>台设备</span>
                    <hr />
                    <b>◷ 2 <small>分钟</small></b
                    ><span>预计耗时</span>
                </aside>
            </div>
            <section class="box issues">
                <b>最近问题预览 <small>（可能发现）</small></b>
                <p>⚠️ 厨房烟感电池电量低 <em>厨房</em></p>
                <p>⚠️ 阳台门磁长时间未关闭 <em>阳台</em></p>
                <p>♻ 主卧空调滤网需要清洁 <em>主卧</em></p>
            </section>
        </div>

        <div v-else-if="modelValue === 'devices'" class="devices-dialog">
            <div class="summary">
                <article><small>总设备</small><b>36</b></article>
                <article><small>● 在线</small><b>28</b></article>
                <article><small>● 离线</small><b>8</b></article>
                <article><small>⚠ 告警</small><b>3</b></article>
            </div>
            <div class="filters">
                <select>
                    <option>全部房间</option></select
                ><select>
                    <option>全部类型</option></select
                ><select>
                    <option>全部状态</option></select
                ><input placeholder="搜索设备名称" />
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>设备名称</th>
                            <th>所属房间</th>
                            <th>当前状态</th>
                            <th>电量 / 温度</th>
                            <th>更新时间</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="row in deviceRows" :key="row[0]">
                            <td>{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td :class="row[2] === '在线' ? 'good' : 'warn'">
                                ● {{ row[2] }}
                            </td>
                            <td>{{ row[3] }}</td>
                            <td>{{ row[4] }}</td>
                            <td>
                                <em
                                    :class="
                                        row[5] === '正常'
                                            ? 'good-tag'
                                            : 'warn-tag'
                                    "
                                    >{{ row[5] }}</em
                                >
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div v-else-if="modelValue === 'schedule'" class="schedule-dialog">
            <div class="date-bar">
                ▣　2025年5月20日 星期二 <span>‹　›</span>
            </div>
            <div class="schedule-list">
                <article v-for="item in schedules" :key="item.time">
                    <time>{{ item.time }}</time
                    ><i :style="{ background: item.color }" /><b>{{
                        item.name
                    }}</b
                    ><small>{{ item.detail }}</small
                    ><button type="button">✎</button
                    ><button type="button">♲</button>
                </article>
            </div>
            <section class="setting-row">
                <div><b>重复设置</b><small>选择重复执行的星期</small></div>
                <div class="chips">
                    <button
                        v-for="day in [
                            '周一',
                            '周二',
                            '周三',
                            '周四',
                            '周五',
                            '周六',
                            '周日',
                        ]"
                        :key="day"
                        type="button"
                        :class="{ active: day !== '周日' }"
                    >
                        {{ day }}
                    </button>
                </div>
                <label
                    >启用自动执行 <input v-model="autoSync" type="checkbox"
                /></label>
            </section>
            <section>
                <b>关联房间 / 设备</b>
                <div class="chips">
                    <button
                        v-for="item in [
                            '客厅',
                            '玄关',
                            '主卧',
                            '空调',
                            '灯光',
                            '窗帘',
                        ]"
                        :key="item"
                        type="button"
                        class="active"
                    >
                        {{ item }}
                    </button>
                </div>
            </section>
        </div>

        <div v-else class="sync-layout">
            <section class="box">
                <b>同步范围</b>
                <p class="section-label">设备范围</p>
                <div class="chips wide">
                    <button
                        v-for="item in [
                            '全部设备',
                            '在线设备',
                            '离线设备',
                            '常用设备',
                        ]"
                        :key="item"
                        type="button"
                        :class="{ active: item === '全部设备' }"
                    >
                        {{ item }}
                    </button>
                </div>
                <p class="section-label">设备来源</p>
                <div class="chips wide">
                    <button
                        v-for="item in [
                            'Home Assistant',
                            'Zigbee 网关',
                            '蓝牙设备',
                            'Matter 设备',
                        ]"
                        :key="item"
                        type="button"
                        :class="{ active: item === 'Home Assistant' }"
                    >
                        {{ item }}
                    </button>
                </div>
                <p class="section-label">同步选项</p>
                <label
                    v-for="item in syncOptions"
                    :key="item"
                    class="switch-row"
                    ><span>{{ item }}<small>更新设备的最新信息</small></span
                    ><input type="checkbox" checked
                /></label>
            </section>
            <aside class="side-stack">
                <div class="box sync-summary">
                    <b>同步概览</b>
                    <p>当前设备总数 <strong>36</strong></p>
                    <p>在线 <strong>28</strong></p>
                    <p>离线 <strong>8</strong></p>
                    <p>预计新增 <strong>2</strong></p>
                </div>
                <div class="box">
                    <b>同步历史</b>
                    <p>今天 09:55　手动同步　<em class="good-tag">成功</em></p>
                    <p>昨天 22:10　自动同步　<em class="good-tag">成功</em></p>
                </div>
            </aside>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.box,
.room-preview,
.estimate {
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 16px;
}
.mode-layout,
.room-layout,
.sync-layout {
    display: grid;
    grid-template-columns: 1.65fr 1fr;
    gap: 16px;
}
.mode-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.mode-card {
    position: relative;
    display: flex;
    min-height: 150px;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
}
.mode-card.selected {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-primary-100);
}
.mode-card > span,
.room-preview > div > span {
    display: grid;
    width: 54px;
    height: 54px;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.mode-card small,
.switch-row small,
.setting-row small {
    display: block;
    color: var(--color-text-tertiary);
}
.mode-card i {
    position: absolute;
    right: 8px;
    top: 8px;
    width: 20px;
    border-radius: 50%;
    background: var(--color-primary-500);
    color: #fff;
}
.side-stack,
.form-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
}
.chips button,
fieldset button {
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 7px 12px;
}
.chips button.active,
fieldset button.active {
    border-color: var(--color-primary-400);
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}
.switch-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px;
}
.switch-row input,
.setting-row input {
    width: 38px;
    height: 20px;
    accent-color: var(--color-primary-500);
}
.impact p,
.sync-summary p {
    display: flex;
    gap: 8px;
    margin: 10px 0;
}
.impact strong,
.sync-summary strong {
    margin-left: auto;
}
.form-stack > label,
.form-row label {
    position: relative;
    display: flex;
    flex-direction: column;
    gap: 7px;
    font-weight: 700;
}
.form-stack input,
.form-stack select,
.filters input,
.filters select {
    height: 38px;
    border: 1px solid var(--color-border-default);
    border-radius: 8px;
    background: var(--color-panel-background);
    padding: 0 11px;
}
.form-stack > label > small {
    position: absolute;
    right: 10px;
    bottom: 10px;
    color: var(--color-text-tertiary);
}
.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
fieldset {
    display: flex;
    gap: 9px;
    border: 0;
}
legend {
    margin-bottom: 8px;
    font-weight: 700;
}
.color-dot {
    width: 22px;
    height: 22px;
    padding: 0;
    border-radius: 50%;
}
.device-bind {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
}
.device-bind button {
    display: flex;
    align-items: center;
    gap: 7px;
}
.room-preview {
    text-align: center;
}
.room-preview > div {
    padding: 20px;
}
.room-preview > div > span {
    margin: auto;
}
.room-preview h3 {
    margin: 10px 0 2px;
    font-size: 20px;
}
.room-preview ul {
    list-style: none;
    text-align: left;
}
.room-preview li {
    display: flex;
    justify-content: space-between;
    padding: 7px;
}
.inspection-top {
    display: grid;
    grid-template-columns: 1fr 140px;
    gap: 12px;
}
.wide {
    margin-bottom: 18px;
}
.check-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-top: 14px;
}
.check-grid input {
    accent-color: var(--color-primary-500);
}
.estimate {
    display: flex;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
}
.estimate strong {
    color: var(--color-primary-600);
    font-size: 30px;
}
.estimate hr {
    width: 80%;
    border: 0;
    border-top: 1px solid var(--color-border-default);
}
.issues {
    margin-top: 12px;
}
.issues p {
    display: flex;
    margin-top: 8px;
    border-top: 1px solid var(--color-border-default);
    padding-top: 8px;
}
.issues em {
    margin-left: auto;
}
.summary {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}
.summary article {
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    padding: 14px;
}
.summary b {
    display: block;
    font-size: 24px;
}
.filters {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 14px 0;
}
.table-wrap {
    overflow: auto;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
}
th,
td {
    border-bottom: 1px solid var(--color-border-default);
    padding: 10px;
    text-align: left;
    white-space: nowrap;
}
.good {
    color: var(--color-success);
}
.warn {
    color: var(--color-warning);
}
.good-tag,
.warn-tag {
    border-radius: 10px;
    padding: 3px 8px;
    font-style: normal;
}
.good-tag {
    background: var(--color-success-soft);
    color: var(--color-success);
}
.warn-tag {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}
.date-bar {
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 14px;
    font-weight: 800;
}
.date-bar span {
    float: right;
}
.schedule-list article {
    display: grid;
    grid-template-columns: 55px 8px 90px 1fr 34px 34px;
    align-items: center;
    gap: 10px;
    margin-top: 8px;
    border: 1px solid var(--color-border-default);
    border-radius: 9px;
    padding: 11px;
}
.schedule-list i {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}
.schedule-list button {
    border: 1px solid var(--color-border-default);
    border-radius: 7px;
    background: var(--color-panel-background);
    padding: 5px;
}
.setting-row {
    display: grid;
    grid-template-columns: 130px 1fr auto;
    align-items: center;
    margin: 14px 0;
    border-top: 1px solid var(--color-border-default);
    border-bottom: 1px solid var(--color-border-default);
    padding: 12px 0;
}
.section-label {
    margin-top: 16px;
    color: var(--color-text-secondary);
    font-size: 12px;
}
.sync-summary p {
    border-bottom: 1px solid var(--color-border-default);
    padding-bottom: 8px;
}
@media (max-width: 760px) {
    .mode-layout,
    .room-layout,
    .sync-layout,
    .inspection-top {
        grid-template-columns: 1fr;
    }
    .mode-grid {
        grid-template-columns: 1fr;
    }
    .summary {
        grid-template-columns: 1fr 1fr;
    }
    .filters {
        grid-template-columns: 1fr 1fr;
    }
    .schedule-list article {
        grid-template-columns: 50px 8px 1fr auto auto;
    }
    .schedule-list small {
        grid-column: 3/-1;
    }
    .setting-row {
        grid-template-columns: 1fr;
    }
    .device-bind {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
