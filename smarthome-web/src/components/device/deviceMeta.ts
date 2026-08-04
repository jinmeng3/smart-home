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

export const deviceTypeLabelMap: Record<DeviceType, string> = {
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

export const deviceTypeIconMap: Record<DeviceType, string> = {
  light: "light",
  air_conditioner: "air-conditioner",
  lock: "lock",
  camera: "camera",
  sensor: "sensor",
  socket: "plug",
  curtain: "curtain",
};

export const getStatusClasses = (status: DeviceStatus) => {
  const config = statusColorMap[status as SemanticStatus];

  return [config.textClass, config.backgroundClass, config.borderClass];
};
