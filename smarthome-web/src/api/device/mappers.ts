import type {
  Device,
  DeviceCreatePayload,
  DeviceDetail,
  DeviceLog,
  DevicePlatform,
  DeviceUpdatePayload,
} from "../../types/device";

/** 设备 DTO 与领域模型互转（SRP：映射职责独立于请求与查询构建）。 */

export interface ApiDevice {
  id: number;
  device_id?: string;
  name: string;
  room: string;
  type: Device["type"];
  brand: string;
  status: Device["status"];
  connection: DevicePlatform;
  firmware: string;
  image_url?: string | null;
  last_online?: string | null;
  created_at?: string;
  updated_at?: string;
  logs?: ApiDeviceLog[];
}

export interface ApiDeviceLog {
  id: number;
  device_id: number;
  action: string;
  message: string;
  created_at: string;
}

export const mapDevice = (device: ApiDevice): Device => ({
  id: device.id,
  name: device.name,
  room: device.room,
  type: device.type,
  brand: device.brand,
  status: device.status,
  connection: device.connection,
  firmware: device.firmware,
  lastOnline: device.last_online ?? "",
  image: device.image_url ?? undefined,
});

export const mapDeviceLog = (log: ApiDeviceLog): DeviceLog => ({
  id: log.id,
  deviceId: log.device_id,
  action: log.action,
  message: log.message,
  createdAt: log.created_at,
});

export const mapDeviceDetail = (device: ApiDevice): DeviceDetail => ({
  ...mapDevice(device),
  deviceId: device.device_id ?? String(device.id),
  imageUrl: device.image_url ?? undefined,
  createdAt: device.created_at ?? "",
  updatedAt: device.updated_at ?? "",
  logs: device.logs?.map(mapDeviceLog) ?? [],
});

export const mapCreatePayload = (payload: DeviceCreatePayload) => ({
  name: payload.name,
  room: payload.room,
  type: payload.type,
  brand: payload.brand,
  connection: payload.connection,
  device_id: payload.deviceId,
  firmware: payload.firmware,
  image_url: payload.imageUrl,
});

export const mapUpdatePayload = (payload: DeviceUpdatePayload) => ({
  name: payload.name,
  room: payload.room,
  type: payload.type,
  brand: payload.brand,
  status: payload.status,
  connection: payload.connection,
  firmware: payload.firmware,
  image_url: payload.imageUrl,
});
