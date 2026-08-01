import type { Automation } from "../types/automation";
import type { ChatMessage, RecentConversation } from "../types/chat";
import type { DashboardDevice } from "../types/device";

export const devices: DashboardDevice[] = [
  {
    id: "living-room-light",
    name: "客厅吸顶灯",
    type: "light",
    status: "离线",
    room: "客厅",
    online: false,
    updatedAt: "10:08",
  },
  {
    id: "bedroom-ac",
    name: "主卧空调",
    type: "air_conditioner",
    status: "运行中",
    value: "26℃ 制冷",
    room: "主卧",
    online: true,
    updatedAt: "10:20",
  },
  {
    id: "front-door-lock",
    name: "智能门锁",
    type: "lock",
    status: "正常",
    room: "玄关",
    online: true,
    updatedAt: "10:18",
  },
  {
    id: "living-room-camera",
    name: "客厅摄像头",
    type: "camera",
    status: "在线",
    room: "客厅",
    online: true,
    updatedAt: "10:21",
  },
];

export const automations: Automation[] = [
  {
    id: "wake-up",
    name: "起床模式",
    trigger: "每天 07:00",
    actions: ["窗帘打开", "卧室灯亮", "空调制热 24℃"],
    enabled: true,
    time: "07:00",
    description: "窗帘打开 · 卧室灯亮 · 空调制热 24℃",
  },
  {
    id: "arrive-home",
    name: "回家模式",
    trigger: "每天 19:00",
    actions: ["玄关灯亮", "空调制冷 26℃", "新风开启"],
    enabled: true,
    time: "19:00",
    description: "玄关灯亮 · 空调制冷 26℃ · 新风开启",
  },
  {
    id: "sleep",
    name: "睡眠模式",
    trigger: "每天 22:30",
    actions: ["关闭灯光", "安防布防", "监控夜视"],
    enabled: true,
    time: "22:30",
    description: "关闭灯光 · 安防布防 · 监控夜视",
  },
];

export const messages: ChatMessage[] = [
  {
    id: "message-1",
    role: "user",
    content: "帮我总结一下家里当前状态，并给出今晚的智能控制建议。",
    timestamp: "10:30",
  },
  {
    id: "message-2",
    role: "assistant",
    content: "好的，以下是您家当前状态及今晚建议：",
    timestamp: "10:31",
  },
];

export const recentConversations: RecentConversation[] = [
  { id: "recent-1", title: "打开客厅灯光", time: "10:22", icon: "Lightbulb" },
  { id: "recent-2", title: "睡眠模式设置", time: "昨天", icon: "Moon" },
  { id: "recent-3", title: "空调温度建议", time: "昨天", icon: "Snowflake" },
  { id: "recent-4", title: "查看门锁状态", time: "周一", icon: "Lock" },
  { id: "recent-5", title: "每日电量统计", time: "周一", icon: "Activity" },
  { id: "recent-6", title: "摄像头异常提醒", time: "5月18日", icon: "Camera" },
];
