import { statusColorMap } from "../../constants/status-colors";
import type { DevicePlatform, DeviceStatus, DeviceType } from "../../types/device";
import type { SemanticStatus } from "../../constants/status-colors";

export const devicePlatformOptions: DevicePlatform[] = [
  "Home Assistant",
  "Matter",
  "Zigbee",
  "MQTT",
];

export const platformIconMap: Record<string, string> = {
  "Home Assistant": "home-assistant",
  Matter: "matter",
  Zigbee: "zigbee",
  MQTT: "mqtt",
};

export const deviceTypeOptions: { label: string; value: DeviceType | "" }[] = [
  { label: "全部", value: "" },
  { label: "灯光", value: "light" },
  { label: "空调", value: "air_conditioner" },
  { label: "门锁", value: "lock" },
  { label: "摄像头", value: "camera" },
  { label: "传感器", value: "sensor" },
  { label: "插座", value: "socket" },
  { label: "窗帘", value: "curtain" },
];

export const deviceStatusOptions: {
  label: string;
  value: DeviceStatus | "";
}[] = [
  { label: "全部", value: "" },
  { label: "在线", value: "online" },
  { label: "离线", value: "offline" },
  { label: "告警", value: "warning" },
  { label: "运行中", value: "running" },
];

export const deviceTypeLabelMap: Record<string, string> = {
  light: "灯光",
  air_conditioner: "空调",
  lock: "门锁",
  camera: "摄像头",
  sensor: "传感器",
  socket: "插座",
  curtain: "窗帘",
};

export const deviceStatusLabelMap: Record<DeviceStatus, string> = {
  online: "在线",
  offline: "离线",
  warning: "告警",
  running: "运行中",
};

/** 获取状态文案，未知状态回退为原始值。 */
export const getDeviceStatusLabel = (status: string) =>
  deviceStatusLabelMap[status as DeviceStatus] ?? status;

export const deviceTypeIconMap: Record<string, string> = {
  light: "light",
  air_conditioner: "air-conditioner",
  lock: "lock",
  camera: "camera",
  sensor: "sensor",
  socket: "plug",
  curtain: "curtain",
};

/** 获取设备类型中文标签，未知类型回退为原始值。 */
export const getDeviceTypeLabel = (type: string): string =>
  deviceTypeLabelMap[type] ?? type;

/** 获取设备类型图标名，未知类型使用默认图标。 */
export const getDeviceTypeIcon = (type: string): string =>
  deviceTypeIconMap[type] ?? "device-management";

/** 设备可选图标列表 */
export const deviceIconOptions: { label: string; value: string }[] = [
  { label: "默认", value: "device-management" },
  { label: "灯光", value: "light" },
  { label: "空调", value: "air-conditioner" },
  { label: "门锁", value: "lock" },
  { label: "摄像头", value: "camera" },
  { label: "传感器", value: "sensor" },
  { label: "插座", value: "plug" },
  { label: "窗帘", value: "curtain" },
  { label: "温湿度", value: "humidity" },
  { label: "空气", value: "air-quality" },
  { label: "温度", value: "temperature" },
  { label: "光照", value: "illumination" },
  { label: "噪音", value: "noise" },
  { label: "舒适", value: "comfort" },
  { label: "开关", value: "power" },
  { label: "安防", value: "security" },
  { label: "节能", value: "energy" },
  { label: "定时", value: "clock" },
  { label: "日历", value: "calendar" },
  { label: "场景", value: "automation" },
  { label: "场景2", value: "scene" },
  { label: "搜索", value: "scan" },
  { label: "分组", value: "group" },
  { label: "日志", value: "log" },
  { label: "设置", value: "settings" },
  { label: "信息", value: "info" },
  { label: "位置", value: "location" },
  { label: "房间", value: "room" },
  { label: "主页", value: "home" },
  { label: "聊天", value: "chat" },
  { label: "通知", value: "notification" },
  { label: "备份", value: "backup" },
  { label: "平台", value: "platform" },
  { label: "账户", value: "account" },
  { label: "成员", value: "members" },
  { label: "外观", value: "appearance" },
  { label: "AI", value: "ai" },
];

export const getStatusClasses = (status: DeviceStatus) => {
  const config = statusColorMap[status as SemanticStatus];

  return [config.textClass, config.backgroundClass, config.borderClass];
};
