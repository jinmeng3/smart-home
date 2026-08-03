import { apiRequest } from "./client";
import {
  mapCreatePayload,
  mapDevice,
  mapDeviceDetail,
  mapDeviceLog,
  mapUpdatePayload,
  type ApiDevice,
  type ApiDeviceLog,
} from "./device/mappers";
import { buildDeviceQuery } from "./device/query";
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

interface ApiDeviceListResponse {
  total: number;
  items: ApiDevice[];
}

export const listDevices = async (
  filters: DeviceFilters,
): Promise<DeviceListResponse> => {
  const response = await apiRequest<ApiDeviceListResponse>(
    `/api/devices?${buildDeviceQuery(filters)}`,
  );

  return {
    total: response.total,
    items: response.items.map(mapDevice),
  };
};

export const getDevice = async (id: number): Promise<DeviceDetail> => {
  const response = await apiRequest<ApiDevice>(`/api/devices/${id}`);
  return mapDeviceDetail(response);
};

export const createDevice = async (payload: DeviceCreatePayload): Promise<Device> => {
  const response = await apiRequest<ApiDevice>("/api/devices", {
    method: "POST",
    body: JSON.stringify(mapCreatePayload(payload)),
  });
  return mapDevice(response);
};

export const updateDevice = async (
  id: number,
  payload: DeviceUpdatePayload,
): Promise<Device> => {
  const response = await apiRequest<ApiDevice>(`/api/devices/${id}`, {
    method: "PUT",
    body: JSON.stringify(mapUpdatePayload(payload)),
  });
  return mapDevice(response);
};

export const deleteDevice = (id: number) =>
  apiRequest<null>(`/api/devices/${id}`, {
    method: "DELETE",
  });

export const syncDevices = (platform: DevicePlatform) =>
  apiRequest<{ platform: DevicePlatform; synced_count: number }>("/api/devices/sync", {
    method: "POST",
    body: JSON.stringify({ platform }),
  });

export const listDeviceLogs = async (id: number): Promise<DeviceLog[]> => {
  const response = await apiRequest<{ total: number; items: ApiDeviceLog[] }>(
    `/api/devices/${id}/logs`,
  );

  return response.items.map(mapDeviceLog);
};

export const uploadDeviceImage = async (file: File): Promise<string> => {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<string>("/api/devices/images", {
    method: "POST",
    body: formData,
  });
};

// ── 快捷操作 ──────────────────────────────────────────────────────────────────────

interface ScanResult {
  platform: string | null;
  scanned_count: number;
  found_count: number;
  found: ApiDevice[];
}

interface FirmwareBatchResult {
  updated_count: number;
}

interface BatchGroupResult {
  group_id: number;
  group: string;
  assigned_count: number;
}

export const scanDevices = async (
  platform: string | null,
): Promise<ScanResult> => {
  return apiRequest<ScanResult>("/api/devices/scan", {
    method: "POST",
    body: JSON.stringify({ platform }),
  });
};

export const batchUpdateFirmware = async (
  device_ids: number[],
  version: string,
): Promise<FirmwareBatchResult> => {
  return apiRequest<FirmwareBatchResult>("/api/devices/firmware", {
    method: "POST",
    body: JSON.stringify({ device_ids, version }),
  });
};

export const batchGroupDevices = async (
  device_ids: number[],
  group: string,
): Promise<BatchGroupResult> => {
  return apiRequest<BatchGroupResult>("/api/devices/groups/assign", {
    method: "POST",
    body: JSON.stringify({ device_ids, group }),
  });
};
