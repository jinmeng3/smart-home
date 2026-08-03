export type DeviceType =
  | "light"
  | "air_conditioner"
  | "lock"
  | "camera"
  | "sensor"
  | "socket"
  | "curtain";

export type DeviceStatus = "online" | "offline" | "warning" | "running";

export type DevicePlatform = "Home Assistant" | "Matter" | "Zigbee" | "MQTT";

export interface Device {
  id: number;
  name: string;
  room: string;
  type: DeviceType;
  brand: string;
  status: DeviceStatus;
  connection: DevicePlatform;
  firmware: string;
  lastOnline: string;
  image?: string;
}

export interface DeviceLog {
  id: number;
  deviceId: number;
  action: string;
  message: string;
  createdAt: string;
}

export interface DeviceDetail extends Device {
  deviceId: string;
  imageUrl?: string;
  createdAt: string;
  updatedAt: string;
  logs: DeviceLog[];
}

export interface DeviceListResponse {
  total: number;
  items: Device[];
}

export interface DeviceFilters {
  page: number;
  pageSize: number;
  keyword: string;
  type: DeviceType | "";
  status: DeviceStatus | "";
  room: string;
}

export interface DeviceCreatePayload {
  name: string;
  room: string;
  type: DeviceType;
  brand: string;
  connection: DevicePlatform;
  deviceId?: string;
  firmware?: string;
  imageUrl?: string;
}

export interface DeviceUpdatePayload {
  name?: string;
  room?: string;
  type?: DeviceType;
  brand?: string;
  status?: DeviceStatus;
  connection?: DevicePlatform;
  firmware?: string;
  imageUrl?: string;
}

export interface DashboardDevice {
  id: string;
  name: string;
  type: DeviceType;
  status: string;
  value?: string;
  room: string;
  online: boolean;
  updatedAt: string;
  brand?: string;
  connection?: DevicePlatform;
  firmware?: string;
  image?: string;
}

export interface DeviceSummary {
  online: number;
  offline: number;
  total: number;
}
