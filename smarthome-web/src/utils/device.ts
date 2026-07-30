import type { DeviceStatus } from "../types/animation";
import type { Device } from "../types/device";

export const getDeviceRuntimeStatus = (device: Device): DeviceStatus => {
  if (!device.online) {
    return "offline";
  }

  if (device.type === "air_conditioner") {
    return "running";
  }

  return "online";
};
