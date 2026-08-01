import { apiRequest } from "./client";
import type {
  Device,
  DeviceCreatePayload,
  DeviceDetail,
  DeviceFilters,
  DeviceListResponse,
  DeviceLog,
  DeviceUpdatePayload,
} from "../types/device";

interface ApiDevice {
  id: number;
  device_id?: string;
  name: string;
  room: string;
  type: Device["type"];
  brand: string;
  status: Device["status"];
  connection?: string;
  firmware?: string;
  image_url?: string | null;
  last_online?: string | null;
  created_at?: string;
  updated_at?: string;
  logs?: ApiDeviceLog[];
}

interface ApiDeviceLog {
  id: number;
  device_id: number;
  action: string;
  message: string;
  created_at: string;
}

interface ApiDeviceListResponse {
  total: number;
  items: ApiDevice[];
}

const mapDevice = (device: ApiDevice): Device => ({
  id: device.id,
  name: device.name,
  room: device.room,
  type: device.type,
  brand: device.brand,
  status: device.status,
  connection: device.connection ?? "Home Assistant",
  firmware: device.firmware ?? "1.0.0",
  lastOnline: device.last_online ?? "",
  image: device.image_url ?? undefined,
});

const mapDeviceLog = (log: ApiDeviceLog): DeviceLog => ({
  id: log.id,
  deviceId: log.device_id,
  action: log.action,
  message: log.message,
  createdAt: log.created_at,
});

const mapDeviceDetail = (device: ApiDevice): DeviceDetail => ({
  ...mapDevice(device),
  deviceId: device.device_id ?? String(device.id),
  imageUrl: device.image_url ?? undefined,
  createdAt: device.created_at ?? "",
  updatedAt: device.updated_at ?? "",
  logs: device.logs?.map(mapDeviceLog) ?? [],
});

const buildDeviceQuery = (filters: DeviceFilters) => {
  const params = new URLSearchParams({
    page: String(filters.page),
    page_size: String(filters.pageSize),
  });

  if (filters.keyword.trim()) {
    params.set("keyword", filters.keyword.trim());
  }

  if (filters.type) {
    params.set("type", filters.type);
  }

  if (filters.status) {
    params.set("status", filters.status);
  }

  if (filters.room.trim()) {
    params.set("room", filters.room.trim());
  }

  return params.toString();
};

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

export const createDevice = (payload: DeviceCreatePayload) =>
  apiRequest<ApiDevice>("/api/devices", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateDevice = (id: number, payload: DeviceUpdatePayload) =>
  apiRequest<ApiDevice>(`/api/devices/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deleteDevice = (id: number) =>
  apiRequest<null>(`/api/devices/${id}`, {
    method: "DELETE",
  });

export const syncDevices = (platform: string) =>
  apiRequest<{ platform: string; synced_count: number }>("/api/devices/sync", {
    method: "POST",
    body: JSON.stringify({ platform }),
  });

export const listDeviceLogs = async (id: number): Promise<DeviceLog[]> => {
  const response = await apiRequest<{ total: number; items: ApiDeviceLog[] }>(
    `/api/devices/${id}/logs`,
  );

  return response.items.map(mapDeviceLog);
};
