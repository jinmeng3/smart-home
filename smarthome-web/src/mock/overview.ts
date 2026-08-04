import type { ScheduleItem } from "../api/overview";

// ── 概览房间卡片 ──────────────────────────────────────────────────────────────────

export interface OverviewRoom {
  name: string;
  icon: string;
  count: number;
  light: string;
  air: string;
  extra: string;
  tone: string;
}

export const overviewRooms: OverviewRoom[] = [
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
];

// ── 活动日志 ──────────────────────────────────────────────────────────────────────

export interface ActivityItem {
  time: string;
  icon: string;
  title: string;
  description: string;
  tone: string;
}

export const overviewActivities: ActivityItem[] = [
  { time: "10:15", icon: "lock", title: "门锁开启", description: "张晓明通过指纹打开了玄关门锁", tone: "purple" },
  { time: "10:10", icon: "air-conditioner", title: "空调运行", description: "客厅空调已开启，设定 26°C 制冷模式", tone: "blue" },
  { time: "10:05", icon: "curtain", title: "窗帘关闭", description: "主卧窗帘已自动关闭", tone: "teal" },
  { time: "09:58", icon: "automation", title: "自动化执行", description: "\"离家模式\"自动执行完成", tone: "green" },
  { time: "09:45", icon: "light", title: "灯光开启", description: "卫生间灯光已开启", tone: "orange" },
  { time: "09:30", icon: "sensor", title: "传感器触发", description: "阳台人体传感器检测到移动", tone: "teal" },
  { time: "09:15", icon: "temperature", title: "温度更新", description: "客厅温度升至 26.5°C，空调自动调节", tone: "blue" },
  { time: "08:50", icon: "camera", title: "摄像头事件", description: "门口摄像头检测到访客，已抓拍保存", tone: "purple" },
  { time: "08:30", icon: "air-quality", title: "空气质量", description: "卧室空气质量优，PM2.5 指数 18", tone: "green" },
  { time: "08:00", icon: "automation", title: "自动化执行", description: "\"起床模式\"自动执行：窗帘开启·灯光亮起", tone: "green" },
  { time: "07:45", icon: "humidity", title: "湿度告警", description: "卫生间湿度异常，排风机已自动开启", tone: "orange" },
  { time: "07:30", icon: "light", title: "灯光关闭", description: "次卧灯光已自动关闭", tone: "orange" },
  { time: "07:00", icon: "curtain", title: "窗帘开启", description: "客厅窗帘已定时开启", tone: "teal" },
];

// ── 概览设备列表 ──────────────────────────────────────────────────────────────────

export interface OverviewDevice {
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

export const overviewDevices: OverviewDevice[] = [
  { id: 1, name: "客厅吸顶灯", room: "客厅", status: "在线", detail: "亮度 80%", updatedAt: "10:15", icon: "light", tone: "orange", frequent: true, favorite: true },
  { id: 2, name: "客厅空调", room: "客厅", status: "在线", detail: "26°C 制冷", updatedAt: "10:15", icon: "air-conditioner", tone: "blue", frequent: true, favorite: true },
  { id: 3, name: "主卧空调", room: "主卧", status: "在线", detail: "26°C 制冷", updatedAt: "10:14", icon: "air-conditioner", tone: "blue", frequent: true, favorite: false },
  { id: 4, name: "智能门锁", room: "玄关", status: "在线", detail: "已上锁", updatedAt: "10:13", icon: "lock", tone: "purple", frequent: true, favorite: true },
  { id: 5, name: "空气净化器", room: "客厅", status: "在线", detail: "自动模式", updatedAt: "10:12", icon: "sensor", tone: "green", frequent: true, favorite: false },
  { id: 6, name: "厨房烟感", room: "厨房", status: "在线", detail: "电量 18% · 告警", updatedAt: "10:10", icon: "notification", tone: "orange", frequent: false, favorite: false },
  { id: 7, name: "阳台门磁", room: "阳台", status: "在线", detail: "已关闭", updatedAt: "10:09", icon: "security", tone: "green", frequent: false, favorite: false },
  { id: 8, name: "客厅摄像头", room: "客厅", status: "离线", detail: "连接中断", updatedAt: "09:58", icon: "camera", tone: "purple", frequent: false, favorite: false },
];

// ── 概览日程安排 ──────────────────────────────────────────────────────────────────

export const overviewScheduleItems: ScheduleItem[] = [
  { time: "07:00", name: "起床模式", detail: "窗帘打开 · 卧室灯亮 · 空调制热 24°C", color: "#ff9418", enabled: true, position: 0 },
  { time: "19:00", name: "回家模式", detail: "玄关灯亮 · 空调制冷 26°C · 新风开启", color: "#3478f6", enabled: true, position: 1 },
  { time: "22:00", name: "离家模式", detail: "关闭灯光 · 安防布防 · 监控夜视", color: "#825bea", enabled: true, position: 2 },
  { time: "23:00", name: "睡眠模式", detail: "灯光渐暗 · 窗帘关闭 · 安防设防", color: "#0d9488", enabled: true, position: 3 },
];