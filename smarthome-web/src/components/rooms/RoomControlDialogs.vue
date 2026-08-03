<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import BaseSmartModal from "../common/BaseSmartModal.vue";
import SvgIcon from "../common/SvgIcon.vue";
import type { Room } from "../../types/room";

export type RoomDialog =
    "edit" | "create" | "logs" | "scene" | "devices" | "environment" | null;

const props = defineProps<{
    modelValue: RoomDialog;
    room: Room | undefined;
}>();

const emit = defineEmits<{
    "update:modelValue": [value: RoomDialog];
    create: [room: Pick<Room, "name" | "floor" | "roomType">];
    update: [room: Room];
}>();

const roomForm = reactive({ name: "", floor: "1F", roomType: "living" });
const selectedIcon = ref("room");
const selectedColor = ref("#2563eb");
const selectedScene = ref("休闲模式");
const sceneScope = ref("客厅设备");
const syncAutomation = ref(true);
const deviceKeyword = ref("");
const logKeyword = ref("");
const logPage = ref(1);
const trendRange = ref("今日");

const dialogMeta = computed(() => {
    const meta = {
        edit: [
            "编辑房间",
            "修改房间信息、设备分组与控制偏好",
            "保存修改",
            "large",
        ],
        create: [
            "添加房间",
            "创建新房间并绑定设备，完善家庭空间管理",
            "创建房间",
            "large",
        ],
        logs: [
            "房间活动日志",
            `查看${props.room?.name ?? "房间"}最近的设备操作、环境变化与自动化执行记录`,
            "关闭",
            "large",
        ],
        scene: [
            "房间场景切换",
            `为${props.room?.name ?? "房间"}快速切换常用场景并预览影响设备`,
            "立即切换",
            "large",
        ],
        devices: [
            "房间设备管理",
            `统一管理${props.room?.name ?? "房间"}内的设备状态、分组与快捷控制`,
            "保存设置",
            "large",
        ],
        environment: [
            "房间环境详情",
            `查看${props.room?.name ?? "房间"}的实时环境指标、趋势变化与舒适度分析`,
            "导出报告",
            "large",
        ],
    } as const;

    return props.modelValue ? meta[props.modelValue] : meta.edit;
});

const deviceRows = computed(() => {
    const rows: Array<[string, string, string, string, string, string]> = [
        ["吸顶灯", "灯光", "开启", "亮度 80%", "今天 10:25", "light"],
        ["落地灯", "灯光", "开启", "亮度 60%", "今天 10:25", "light"],
        ["电视", "影音", "开启", "HDMI 1", "今天 10:24", "device-management"],
        ["空调", "环境", "开启", "24°C｜制冷", "今天 10:24", "air-conditioner"],
        ["窗帘电机", "窗帘", "开启", "打开 70%", "今天 10:24", "curtain"],
        ["空气净化器", "环境", "开启", "自动模式｜优", "今天 10:24", "sensor"],
        ["智能插座", "电源", "开启", "功率 35W", "今天 10:24", "plug"],
        [
            "温湿度传感器",
            "传感器",
            "正常",
            "温湿度传感器",
            "今天 10:24",
            "humidity",
        ],
    ];

    return rows.filter((row) => row[0].includes(deviceKeyword.value.trim()));
});

const logs = computed(() =>
    [
        ["2026-08-04 10:15:32", "手动操作", "灯光开启", "成功", "灯光　客厅"],
        [
            "2026-08-04 10:12:08",
            "语音助手",
            "空调切换制冷 24°C",
            "成功",
            "空调　温度",
        ],
        ["2026-08-04 09:58:41", "手机 App", "窗帘打开", "成功", "窗帘　遮阳"],
        [
            "2026-08-04 09:30:00",
            "自动化",
            "自动化执行“休闲模式”",
            "成功",
            "场景　自动化",
        ],
        [
            "2026-08-04 08:45:21",
            "环境监测",
            "PM2.5 变化提醒",
            "提醒",
            "环境　PM2.5",
        ],
    ].filter((row) => row.join(" ").includes(logKeyword.value.trim())),
);

const scenes = [
    {
        name: "休闲模式",
        icon: "comfort",
        note: "放松身心，舒适休闲",
        tags: ["柔和灯光", "舒适温度", "轻松氛围"],
    },
    {
        name: "观影模式",
        icon: "device-management",
        note: "沉浸观影，最佳体验",
        tags: ["影院灯光", "窗帘闭合", "增强音效"],
    },
    {
        name: "阅读模式",
        icon: "room",
        note: "专注阅读，保护眼睛",
        tags: ["明亮灯光", "适中温度", "安静环境"],
    },
    {
        name: "离开模式",
        icon: "lock",
        note: "节能安全，安心离家",
        tags: ["关闭电器", "安防布防", "节能省电"],
    },
];

const roomIcons = [
    "room",
    "home",
    "device-management",
    "comfort",
    "scene",
    "automation",
];
const roomColors = [
    "#2563eb",
    "#8b5cf6",
    "#14b8a6",
    "#22c55e",
    "#f59e0b",
    "#f43f5e",
    "#94a3b8",
];
const bindDevices = ["灯光", "空调", "窗帘", "插座", "电视", "空气净化器"];
const bindDeviceIcons = [
    "light",
    "air-conditioner",
    "curtain",
    "plug",
    "device-management",
    "sensor",
];

watch(
    () => [props.modelValue, props.room] as const,
    () => {
        if (props.modelValue === "edit" && props.room) {
            roomForm.name = props.room.name;
            roomForm.floor = props.room.floor;
            roomForm.roomType = props.room.roomType;
        } else if (props.modelValue === "create") {
            roomForm.name = "书房";
            roomForm.floor = "2F";
            roomForm.roomType = "study";
        }
    },
    { immediate: true },
);

const close = () => emit("update:modelValue", null);

const confirm = () => {
    if (props.modelValue === "edit" && props.room) {
        emit("update", { ...props.room, ...roomForm });
    } else if (props.modelValue === "create") {
        emit("create", { ...roomForm });
    }

    close();
};
</script>

<template>
    <BaseSmartModal
        v-if="modelValue"
        :model-value="true"
        :title="dialogMeta[0]"
        :description="dialogMeta[1]"
        :confirm-text="dialogMeta[2]"
        :width="dialogMeta[3]"
        @cancel="close"
        @confirm="confirm"
        @update:model-value="close"
    >
        <div
            v-if="modelValue === 'edit' || modelValue === 'create'"
            class="room-editor"
        >
            <section class="editor-form">
                <div class="field-row">
                    <label>房间名称<input v-model="roomForm.name" /></label>
                    <label
                        >楼层 / 区域<select v-model="roomForm.floor">
                            <option>1F</option>
                            <option>2F</option>
                            <option>地下室</option>
                        </select></label
                    >
                    <label v-if="modelValue === 'create'"
                        >房间类型<select v-model="roomForm.roomType">
                            <option value="living">客厅</option>
                            <option value="bedroom">卧室</option>
                            <option value="study">书房</option>
                            <option value="kitchen">厨房</option>
                        </select></label
                    >
                </div>
                <fieldset>
                    <legend>房间图标</legend>
                    <button
                        v-for="icon in roomIcons"
                        :key="icon"
                        :class="{ active: selectedIcon === icon }"
                        type="button"
                        @click="selectedIcon = icon"
                    >
                        <SvgIcon :name="icon" />
                    </button>
                </fieldset>
                <fieldset>
                    <legend>主题颜色</legend>
                    <button
                        v-for="color in roomColors"
                        :key="color"
                        class="color-dot"
                        :class="{ active: selectedColor === color }"
                        :style="{ background: color }"
                        type="button"
                        @click="selectedColor = color"
                    />
                </fieldset>
                <fieldset class="device-binding">
                    <legend>
                        {{
                            modelValue === "edit"
                                ? "已绑定设备（6）"
                                : "绑定设备（可多选）"
                        }}
                    </legend>
                    <button
                        v-for="(device, index) in bindDevices"
                        :key="device"
                        class="active"
                        type="button"
                    >
                        <SvgIcon
                            :name="bindDeviceIcons[index] ?? 'room'"
                            size="sm"
                        />{{ device }}<b>✓</b>
                    </button>
                </fieldset>
                <section v-if="modelValue === 'edit'" class="preference-card">
                    <h3>快捷控制偏好</h3>
                    <label
                        v-for="item in [
                            '常用设备置顶',
                            '显示环境卡片',
                            '显示场景快捷入口',
                        ]"
                        :key="item"
                        ><span
                            >{{ item
                            }}<small>在房间卡片中显示此功能</small></span
                        ><input checked type="checkbox"
                    /></label>
                </section>
            </section>
            <aside class="room-preview">
                <h3>房间预览</h3>
                <div class="preview-room">
                    <span :style="{ color: selectedColor }"
                        ><SvgIcon :name="selectedIcon" size="lg"
                    /></span>
                    <div>
                        <strong>{{ roomForm.name }}</strong
                        ><small>● {{ bindDevices.length }} 个设备</small>
                    </div>
                    <b>{{ room?.comfort ?? 81 }}<small>分</small></b>
                </div>
                <div class="preview-metrics">
                    <span>🌡 {{ room?.temperature ?? "--" }}°C</span
                    ><span>◉ {{ room?.humidity ?? "--" }}%</span
                    ><span>☀ {{ room?.illuminance ?? "--" }} lux</span>
                </div>
                <h3>关联能力</h3>
                <p
                    v-for="item in ['集中控制', '自动化联动', '能耗统计']"
                    :key="item"
                    class="ability"
                >
                    <SvgIcon name="automation" size="sm" /><span
                        ><b>{{ item }}</b
                        ><small>配置房间智能能力</small></span
                    ><SvgIcon name="chevron-right" size="sm" />
                </p>
            </aside>
        </div>

        <div v-else-if="modelValue === 'logs'" class="logs-dialog">
            <div class="dialog-filters">
                <label>日期范围<input value="2026-07-29 ~ 2026-08-04" /></label
                ><label
                    >日志类型<select>
                        <option>全部类型</option>
                    </select></label
                ><label
                    >设备名称<select>
                        <option>全部设备</option>
                    </select></label
                ><label
                    >搜索<input v-model="logKeyword" placeholder="搜索事件内容"
                /></label>
            </div>
            <div class="data-table">
                <div class="table-head">
                    <span>时间</span><span>来源</span><span>事件内容</span
                    ><span>执行结果</span><span>标签</span>
                </div>
                <article v-for="row in logs" :key="row[0]">
                    <time>{{ row[0] }}</time
                    ><span>{{ row[1] }}</span
                    ><strong>{{ row[2] }}</strong
                    ><span class="success">● {{ row[3] }}</span
                    ><small>{{ row[4] }}</small>
                </article>
            </div>
            <div class="pagination">
                <span>共 32 条记录</span><button type="button">‹</button
                ><button
                    v-for="page in [1, 2, 3, 4]"
                    :key="page"
                    :class="{ active: logPage === page }"
                    type="button"
                    @click="logPage = page"
                >
                    {{ page }}</button
                ><button type="button">›</button>
            </div>
        </div>

        <div v-else-if="modelValue === 'scene'" class="scene-dialog">
            <section>
                <div class="scene-grid">
                    <button
                        v-for="scene in scenes"
                        :key="scene.name"
                        :class="{ active: selectedScene === scene.name }"
                        type="button"
                        @click="selectedScene = scene.name"
                    >
                        <span><SvgIcon :name="scene.icon" size="lg" /></span
                        ><strong>{{ scene.name }}</strong
                        ><small>{{ scene.note }}</small
                        ><i>{{ scene.tags.join("　") }}</i
                        ><b v-if="selectedScene === scene.name">✓</b>
                    </button>
                </div>
                <div class="recommendation">
                    <strong>推荐原因</strong>
                    <p>
                        当前光照适中，温度舒适，适合切换为“{{ selectedScene }}”
                    </p>
                </div>
            </section>
            <aside>
                <h3>应用范围</h3>
                <div class="scope-row">
                    <button
                        v-for="scope in [
                            '客厅设备',
                            '客厅主区',
                            '阳台',
                            '玄关联动',
                        ]"
                        :key="scope"
                        :class="{ active: sceneScope === scope }"
                        type="button"
                        @click="sceneScope = scope"
                    >
                        {{ scope }}
                    </button>
                </div>
                <label class="toggle-row"
                    ><span>同步执行自动化联动</span
                    ><input v-model="syncAutomation" type="checkbox"
                /></label>
                <div class="impact">
                    <h3>预览影响</h3>
                    <p><SvgIcon name="light" />灯光 <b>5 个</b></p>
                    <p><SvgIcon name="air-conditioner" />空调 <b>1 个</b></p>
                    <p><SvgIcon name="curtain" />窗帘 <b>2 个</b></p>
                    <p><SvgIcon name="plug" />插座 <b>1 个</b></p>
                </div>
            </aside>
        </div>

        <div v-else-if="modelValue === 'devices'" class="devices-dialog">
            <header>
                <div class="room-summary">
                    <span><SvgIcon name="room" size="lg" /></span>
                    <div>
                        <h3>{{ room?.name }}</h3>
                        <small>● 在线</small>
                    </div>
                </div>
                <article>
                    <small>设备总数</small><strong>8 <i>个设备</i></strong>
                </article>
                <article>
                    <small>在线设备</small><strong>8 <i>/ 8</i></strong>
                </article>
                <article>
                    <small>常用分组</small><strong>6 <i>个分组</i></strong>
                </article>
            </header>
            <div class="device-toolbar">
                <input
                    v-model="deviceKeyword"
                    placeholder="搜索设备名称"
                /><select>
                    <option>全部类型</option></select
                ><select>
                    <option>全部状态</option></select
                ><button type="button">批量开关</button
                ><button type="button">分组管理</button
                ><button type="button">设为常用</button>
            </div>
            <div class="device-table">
                <div>
                    <span>设备名称</span><span>所属分组</span
                    ><span>当前状态</span><span>电量 / 模式</span
                    ><span>更新时间</span><span>快捷操作</span>
                </div>
                <article v-for="row in deviceRows" :key="row[0]">
                    <span
                        ><i><SvgIcon :name="row[5]" size="sm" /></i
                        >{{ row[0] }}</span
                    ><span>{{ row[1] }}</span
                    ><span class="success">● {{ row[2] }}</span
                    ><span>{{ row[3] }}</span
                    ><span>{{ row[4] }}</span
                    ><button type="button">●</button>
                </article>
            </div>
        </div>

        <div v-else class="environment-dialog">
            <div class="environment-summary">
                <article>
                    <strong>{{ room?.name }}</strong
                    ><small>● 在线　当前房间</small>
                </article>
                <article>
                    <span>舒适度</span
                    ><strong
                        >{{ room?.comfort ?? 83 }} <small>分</small></strong
                    >
                </article>
                <article>
                    <span>环境状态</span><strong>良好</strong
                    ><small>各项指标在舒适范围内</small>
                </article>
            </div>
            <div class="metric-grid">
                <article
                    v-for="item in [
                        {
                            n: '温度',
                            v: `${room?.temperature}°C`,
                            r: '20.0 ~ 26.0°C',
                            c: '#3b82f6',
                        },
                        {
                            n: '湿度',
                            v: `${room?.humidity}%`,
                            r: '40% ~ 60%',
                            c: '#60a5fa',
                        },
                        {
                            n: 'PM2.5',
                            v: `${room?.pm25} μg/m³`,
                            r: '0 ~ 35 μg/m³',
                            c: '#22c55e',
                        },
                        {
                            n: '光照',
                            v: `${room?.illuminance} lux`,
                            r: '100 ~ 500 lux',
                            c: '#f59e0b',
                        },
                        {
                            n: '噪音',
                            v: `${room?.noise} dB`,
                            r: '30 ~ 60 dB',
                            c: '#8b5cf6',
                        },
                    ]"
                    :key="item.n"
                >
                    <small>{{ item.n }}</small
                    ><strong>{{ item.v }}</strong
                    ><svg viewBox="0 0 100 24" :style="{ stroke: item.c }">
                        <polyline
                            points="0,17 15,11 28,15 42,7 58,15 72,5 86,13 100,8"
                        /></svg
                    ><span>{{ item.r }}</span>
                </article>
            </div>
            <section class="trend-card">
                <header>
                    <h3>环境趋势</h3>
                    <div>
                        <button
                            v-for="range in ['今日', '近 7 天', '近 30 天']"
                            :key="range"
                            :class="{ active: trendRange === range }"
                            type="button"
                            @click="trendRange = range"
                        >
                            {{ range }}
                        </button>
                    </div>
                </header>
                <svg
                    class="trend-chart"
                    viewBox="0 0 760 180"
                    preserveAspectRatio="none"
                >
                    <g>
                        <line
                            v-for="y in [25, 65, 105, 145]"
                            :key="y"
                            x1="20"
                            :y1="y"
                            x2="740"
                            :y2="y"
                        />
                    </g>
                    <polyline
                        class="temperature"
                        points="20,90 100,75 180,72 260,78 340,66 420,57 500,61 580,59 660,78 740,74"
                    />
                    <polyline
                        class="humidity"
                        points="20,125 100,116 180,119 260,116 340,127 420,122 500,120 580,111 660,116 740,119"
                    />
                </svg>
            </section>
            <div class="suggestions">
                <article>
                    <SvgIcon name="air-quality" /><span
                        ><b>开启新风</b
                        ><small>PM2.5 良好，建议定期开启新风</small></span
                    >
                </article>
                <article>
                    <SvgIcon name="automation" /><span
                        ><b>适当通风</b
                        ><small>湿度适中，建议每日通风</small></span
                    >
                </article>
                <article>
                    <SvgIcon name="scene" /><span
                        ><b>夜间降低噪音</b
                        ><small>建议降低电视音量</small></span
                    >
                </article>
            </div>
        </div>
    </BaseSmartModal>
</template>

<style scoped>
.room-editor,
.scene-dialog {
    display: grid;
    grid-template-columns: 1.35fr 1fr;
    gap: 16px;
}
.editor-form {
    display: grid;
    gap: 14px;
}
.field-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}
.field-row label,
.dialog-filters label {
    display: grid;
    gap: 6px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 800;
}
.field-row input,
.field-row select,
.dialog-filters input,
.dialog-filters select,
.device-toolbar input,
.device-toolbar select {
    width: 100%;
    height: 38px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    padding: 0 10px;
}
.editor-form fieldset {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
    border: 0;
    padding: 0;
}
.editor-form legend {
    width: 100%;
    margin-bottom: 7px;
    color: var(--color-text-secondary);
    font-size: 12px;
    font-weight: 900;
}
.editor-form fieldset button {
    display: inline-flex;
    min-width: 46px;
    height: 38px;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-card-bg);
    color: var(--color-text-tertiary);
}
.editor-form fieldset button.active {
    border-color: var(--color-primary-400);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.editor-form .color-dot {
    min-width: 24px;
    width: 24px;
    height: 24px;
    border: 3px solid transparent;
    border-radius: 50%;
}
.editor-form .color-dot.active {
    box-shadow: 0 0 0 2px var(--color-primary-200);
}
.device-binding {
    display: grid !important;
    grid-template-columns: repeat(3, 1fr);
}
.device-binding legend {
    grid-column: 1/-1;
}
.device-binding b {
    margin-left: auto;
}
.preference-card,
.room-preview,
.impact,
.trend-card {
    border: 1px solid var(--color-border);
    border-radius: 12px;
    background: var(--color-card-bg);
    padding: 13px;
}
.preference-card h3,
.room-preview h3,
.scene-dialog h3 {
    margin: 0 0 9px;
    font-size: 13px;
}
.preference-card label,
.toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid var(--color-border-subtle);
    padding: 8px 0;
    font-size: 11px;
}
.preference-card small {
    display: block;
    color: var(--color-text-tertiary);
}
.preference-card input,
.toggle-row input {
    width: 36px;
    height: 19px;
    accent-color: var(--color-primary-600);
}
.room-preview {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
.preview-room {
    display: grid;
    grid-template-columns: 56px 1fr auto;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    padding: 12px;
}
.preview-room > span {
    display: grid;
    width: 56px;
    height: 56px;
    place-items: center;
    border-radius: 10px;
    background: var(--color-primary-50);
}
.preview-room div,
.preview-room > div small,
.preview-room > b small {
    display: block;
}
.preview-room > div small {
    margin-top: 5px;
    color: var(--color-success);
}
.preview-room > b {
    font-size: 22px;
}
.preview-room > b small {
    font-size: 9px;
}
.preview-metrics {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 5px;
}
.preview-metrics span {
    border-radius: 8px;
    background: var(--color-surface-subtle);
    padding: 9px 4px;
    font-size: 10px;
    text-align: center;
}
.ability {
    display: grid;
    grid-template-columns: 24px 1fr 16px;
    align-items: center;
    margin: 0;
    border-bottom: 1px solid var(--color-border-subtle);
    padding: 9px;
}
.ability span,
.ability small {
    display: block;
}
.ability small {
    color: var(--color-text-tertiary);
}
.dialog-filters {
    display: grid;
    grid-template-columns: 1.2fr 1fr 1fr 1.1fr;
    gap: 10px;
    margin-bottom: 12px;
}
.data-table,
.device-table {
    overflow: hidden;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
}
.table-head,
.data-table article {
    display: grid;
    grid-template-columns: 1.15fr 1fr 1.6fr 1.1fr 1.2fr;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    font-size: 11px;
}
.table-head {
    background: var(--color-surface-subtle);
    font-weight: 900;
}
.data-table article {
    border-top: 1px solid var(--color-border-subtle);
}
.data-table small {
    color: var(--color-primary-600);
}
.success {
    color: var(--color-success) !important;
}
.pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    margin-top: 12px;
}
.pagination span {
    margin-right: auto;
    color: var(--color-text-tertiary);
    font-size: 11px;
}
.pagination button,
.scope-row button,
.trend-card button {
    min-width: 30px;
    height: 30px;
    border: 1px solid var(--color-border);
    border-radius: 7px;
    background: var(--color-card-bg);
}
.pagination button.active,
.scope-row button.active,
.trend-card button.active {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}
.scene-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.scene-grid > button {
    position: relative;
    display: flex;
    min-height: 155px;
    align-items: center;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    border: 1px solid var(--color-border);
    border-radius: 11px;
    background: var(--color-card-bg);
}
.scene-grid > button.active {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-focus-ring);
}
.scene-grid > button > span {
    display: grid;
    width: 52px;
    height: 52px;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.scene-grid small {
    color: var(--color-text-tertiary);
}
.scene-grid i {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-style: normal;
}
.scene-grid > button > b {
    position: absolute;
    top: 8px;
    right: 8px;
    display: grid;
    width: 20px;
    height: 20px;
    place-items: center;
    border-radius: 50%;
    background: var(--color-primary-600);
    color: white;
}
.recommendation {
    margin-top: 12px;
    border: 1px solid var(--color-border);
    border-radius: 11px;
    padding: 12px;
}
.recommendation p {
    margin: 6px 0 0;
    color: var(--color-text-tertiary);
    font-size: 11px;
}
.scene-dialog > aside {
    border-left: 1px solid var(--color-border);
    padding-left: 16px;
}
.scope-row {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
}
.scope-row button {
    padding: 0 11px;
}
.impact {
    margin-top: 12px;
}
.impact p {
    display: flex;
    align-items: center;
    gap: 8px;
}
.impact p b {
    margin-left: auto;
}
.devices-dialog > header {
    display: grid;
    grid-template-columns: 1.2fr repeat(3, 1fr);
    gap: 10px;
}
.devices-dialog > header article,
.room-summary {
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 11px;
}
.devices-dialog > header article {
    display: grid;
}
.devices-dialog > header small {
    color: var(--color-text-tertiary);
}
.devices-dialog > header strong {
    font-size: 20px;
}
.devices-dialog > header i {
    color: var(--color-text-tertiary);
    font-size: 9px;
    font-style: normal;
}
.room-summary > span {
    display: grid;
    width: 50px;
    height: 50px;
    place-items: center;
    border-radius: 9px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
}
.room-summary h3 {
    margin: 0;
}
.room-summary small {
    color: var(--color-success) !important;
}
.device-toolbar {
    display: grid;
    grid-template-columns: 1.4fr 0.8fr 0.8fr repeat(3, auto);
    gap: 8px;
    margin: 12px 0;
}
.device-toolbar button {
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 0 10px;
    background: var(--color-card-bg);
    font-size: 10px;
}
.device-table > div,
.device-table article {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr 1.2fr 1.1fr 0.7fr;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    font-size: 10px;
}
.device-table > div {
    background: var(--color-surface-subtle);
    font-weight: 900;
}
.device-table article {
    border-top: 1px solid var(--color-border-subtle);
}
.device-table article > span:first-child {
    display: flex;
    align-items: center;
    gap: 7px;
    font-weight: 800;
}
.device-table article i {
    display: grid;
    width: 26px;
    height: 26px;
    place-items: center;
    border-radius: 7px;
    background: var(--color-primary-50);
    color: var(--color-primary-600);
    font-style: normal;
}
.device-table article button {
    width: 29px;
    height: 16px;
    border-radius: 999px;
    background: var(--color-primary-600);
    color: white;
}
.environment-summary {
    display: grid;
    grid-template-columns: 1.2fr 0.8fr 1fr;
    gap: 10px;
}
.environment-summary article {
    display: flex;
    min-height: 72px;
    justify-content: center;
    flex-direction: column;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 12px;
}
.environment-summary article:first-child strong {
    font-size: 18px;
}
.environment-summary small {
    color: var(--color-text-tertiary);
}
.metric-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 9px;
    margin: 12px 0;
}
.metric-grid article {
    border: 1px solid var(--color-border);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 11px;
}
.metric-grid article > * {
    display: block;
}
.metric-grid strong {
    margin: 6px 0;
    font-size: 18px;
}
.metric-grid svg {
    width: 100%;
    height: 25px;
    fill: none;
    stroke-width: 2;
}
.metric-grid span,
.metric-grid small {
    color: var(--color-text-tertiary);
    font-size: 9px;
}
.trend-card header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.trend-card header div {
    display: flex;
    gap: 5px;
}
.trend-chart {
    width: 100%;
    height: 185px;
}
.trend-chart g {
    stroke: var(--color-border-subtle);
}
.trend-chart polyline {
    fill: none;
    stroke-width: 3;
}
.trend-chart .temperature {
    stroke: var(--color-primary-600);
}
.trend-chart .humidity {
    stroke: #60a5fa;
}
.suggestions {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 9px;
    margin-top: 12px;
}
.suggestions article {
    display: flex;
    gap: 9px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    padding: 11px;
    color: var(--color-primary-600);
}
.suggestions span,
.suggestions small {
    display: block;
}
.suggestions b {
    color: var(--color-text-primary);
}
.suggestions small {
    margin-top: 4px;
    color: var(--color-text-tertiary);
}
@media (max-width: 760px) {
    .room-editor,
    .scene-dialog {
        grid-template-columns: 1fr;
    }
    .field-row,
    .dialog-filters {
        grid-template-columns: 1fr;
    }
    .device-binding,
    .metric-grid,
    .suggestions {
        grid-template-columns: 1fr 1fr;
    }
    .devices-dialog > header {
        grid-template-columns: 1fr 1fr;
    }
    .device-toolbar {
        grid-template-columns: 1fr 1fr;
    }
    .scene-dialog > aside {
        border-left: 0;
        padding-left: 0;
    }
    .data-table,
    .device-table {
        overflow-x: auto;
    }
    .data-table > * {
        min-width: 700px;
    }
    .device-table > * {
        min-width: 760px;
    }
}
</style>
