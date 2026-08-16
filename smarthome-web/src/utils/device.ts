import type { DashboardDevice, Device, DeviceType, DeviceStatus } from "../types/device";
import type { Room, RoomDeviceCard } from "../types/room";
import { getDeviceTypeIcon } from "../components/device/deviceMeta";

/**
 * 设备展示层工具（SRP：模型转换与状态解析，不含请求与业务编排）。
 */

/* === 房间设备视图模型转换 === */

export const toRoomDeviceCards = (devices: Room["device"]): RoomDeviceCard[] => {
    if (!devices || devices.length === 0) return [];
    return devices.map((d) => ({
        id: d.id,
        key: d.type,
        icon: d.icon || getDeviceTypeIcon(d.type),
        color: d.color,
        name: d.name,
        detail: d.brand || "",
        status: d.status as RoomDeviceCard["status"],
    }));
};

/* === 设备状态判断 === */

export const isDeviceActive = (status: string): boolean =>
    status === "online" || status === "running";

export const isDeviceUnavailable = (status: string): boolean =>
    status === "offline" || status === "warning";

export const deviceStatusLabel: Record<string, string> = {
    online: "开",
    offline: "关",
    running: "运行中",
    warning: "异常",
};

/**
 * 设备展示层工具（SRP：模型转换与状态解析，不含请求与业务编排）。
 */

export const mapDashboardDevice = (device: Device): DashboardDevice => ({
  id: String(device.id),
  name: device.name,
  type: device.type,
  status: device.status,
  room: device.room,
  online: device.status === "online" || device.status === "running",
  updatedAt: device.lastOnline || "暂无",
  brand: device.brand,
  connection: device.connection,
  firmware: device.firmware,
  image: device.image,
});

/**
 * 设备运行时状态解析策略（OCP：对扩展开放，对修改关闭）。
 *
 * 新增一种设备类型的运行状态规则时，只需在 deviceTypeStatusStrategies
 * 中注册新的策略，无需修改本模块之外的任何既有代码。
 */

type DeviceStatusStrategy = (device: DashboardDevice) => DeviceStatus;

const offlineStrategy: DeviceStatusStrategy = () => "offline";

const onlineStrategy: DeviceStatusStrategy = () => "online";

/** 设备在线时默认视为在线，可在此覆盖特定类型的运行状态规则。 */
const runningStrategy: DeviceStatusStrategy = () => "running";

export const deviceTypeStatusStrategies: Record<
  DeviceType,
  DeviceStatusStrategy
> = {
  light: onlineStrategy,
  air_conditioner: runningStrategy,
  lock: onlineStrategy,
  camera: onlineStrategy,
  sensor: onlineStrategy,
  socket: onlineStrategy,
  curtain: onlineStrategy,
};

export const getDeviceRuntimeStatus = (
  device: DashboardDevice,
): DeviceStatus => {
  if (!device.online) {
    return offlineStrategy(device);
  }

  const strategy = deviceTypeStatusStrategies[device.type] ?? onlineStrategy;
  return strategy(device);
};

/**
 * 格式化设备时间戳，包含中文友好的显示方式。
 */
export const formatDeviceTimestamp = (
  timestamp: string,
  fallback = "暂无",
) => {
  if (!timestamp || timestamp === "暂无") return fallback;

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin} 分钟前`;

  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour} 小时前`;

  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};