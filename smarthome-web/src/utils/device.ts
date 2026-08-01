import type { DeviceStatus } from "../types/animation";
import type { DashboardDevice } from "../types/device";

export const getDeviceRuntimeStatus = (device: DashboardDevice): DeviceStatus => {
  if (!device.online) {
    return "offline";
  }

  if (device.type === "air_conditioner") {
    return "running";
  }

  return "online";
};
