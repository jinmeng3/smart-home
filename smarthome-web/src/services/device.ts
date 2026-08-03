import {
  batchGroupDevices,
  batchUpdateFirmware,
  createDevice,
  deleteDevice,
  getDevice,
  listDeviceLogs,
  listDevices,
  scanDevices,
  syncDevices,
  updateDevice,
  uploadDeviceImage,
} from "../api/device";
import type {
  Device,
  DeviceCreatePayload,
  DeviceDetail,
  DeviceFilters,
  DeviceListResponse,
  DeviceLog,
  DevicePlatform,
  DeviceUpdatePayload,
} from "../types/device";

/**
 * 设备领域服务层（DIP：对上层暴露稳定的设备能力接口，
 * 上层只依赖此抽象，不直接依赖具体的 API 实现）。
 */
export const deviceService = {
  list(filters: DeviceFilters): Promise<DeviceListResponse> {
    return listDevices(filters);
  },

  get(id: number): Promise<DeviceDetail> {
    return getDevice(id);
  },

  create(payload: DeviceCreatePayload): Promise<Device> {
    return createDevice(payload);
  },

  update(id: number, payload: DeviceUpdatePayload): Promise<Device> {
    return updateDevice(id, payload);
  },

  remove(id: number): Promise<null> {
    return deleteDevice(id);
  },

  listLogs(id: number): Promise<DeviceLog[]> {
    return listDeviceLogs(id);
  },

  sync(platform: DevicePlatform): Promise<{ platform: DevicePlatform; synced_count: number }> {
    return syncDevices(platform);
  },

  scan(platform: string | null): Promise<{
    platform: string | null;
    scanned_count: number;
    found_count: number;
    found: Array<{ id: number; name: string }>;
  }> {
    return scanDevices(platform);
  },

  batchUpdateFirmware(deviceIds: number[], version: string) {
    return batchUpdateFirmware(deviceIds, version);
  },

  batchGroup(deviceIds: number[], group: string) {
    return batchGroupDevices(deviceIds, group);
  },

  uploadImage(file: File): Promise<string> {
    return uploadDeviceImage(file);
  },
};
