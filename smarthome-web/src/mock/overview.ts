import type { ScheduleItem } from "../api/overview";

// ── 活动日志（降级数据） ──────────────────────────────────────────────────────────────────────

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

// ── 概览日程安排（降级数据） ──────────────────────────────────────────────────────────────────

export const overviewScheduleItems: ScheduleItem[] = [
  { time: "07:00", name: "起床模式", detail: "窗帘打开 · 卧室灯亮 · 空调制热 24°C", color: "#ff9418", enabled: true, position: 0 },
  { time: "19:00", name: "回家模式", detail: "玄关灯亮 · 空调制冷 26°C · 新风开启", color: "#3478f6", enabled: true, position: 1 },
  { time: "22:00", name: "离家模式", detail: "关闭灯光 · 安防布防 · 监控夜视", color: "#825bea", enabled: true, position: 2 },
  { time: "23:00", name: "睡眠模式", detail: "灯光渐暗 · 窗帘关闭 · 安防设防", color: "#0d9488", enabled: true, position: 3 },
];