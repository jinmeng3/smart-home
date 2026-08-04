import type { RoomDeviceCard } from "../types/room";

// ── 房间控制常用设备 ──────────────────────────────────────────────────────────────

export const commonDevices: RoomDeviceCard[] = [
  { key: "light", icon: "light", name: "吸顶灯", detail: "亮度 80%" },
  { key: "television", icon: "device-management", name: "电视", detail: "音量 30%" },
  { key: "airConditioner", icon: "air-conditioner", name: "空调", detail: "24°C" },
  { key: "airPurifier", icon: "sensor", name: "空气净化器", detail: "风速 自动" },
  { key: "socket", icon: "plug", name: "智能插座", detail: "" },
];