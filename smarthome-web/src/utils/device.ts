import type { DeviceStatus } from "../types/animation";
import type { DashboardDevice, Device, DeviceType } from "../types/device";

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
