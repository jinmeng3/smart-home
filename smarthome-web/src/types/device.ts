export type DeviceType = string;

/** 预定义的设备类型，用于类型选择器中的快捷选项 */
export const PRESET_DEVICE_TYPES = [
  "light",
  "air_conditioner",
  "lock",
  "camera",
  "sensor",
  "socket",
  "curtain",
] as const;

export type DeviceStatus = "online" | "offline" | "warning" | "running";

export type DevicePlatform = "Home Assistant" | "Matter" | "Zigbee" | "MQTT";

export interface Device {
  id: number;
  deviceId?: string;
  name: string;
  room: string;
  type: DeviceType;
  brand: string;
  status: DeviceStatus;
  connection: DevicePlatform;
  firmware: string;
  icon?: string;
  color?: string;
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
  icon?: string;
  color?: string;
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
  icon?: string;
  color?: string;
  imageUrl?: string;
}

export interface DeviceBatchGroupPayload {
  group: string;
  deviceIds: number[];
}

export interface DeviceBatchGroupResult {
  groupId: number;
  group: string;
  assignedCount: number;
}

export interface DashboardDevice {
  id: string;
  name: string;
  type: DeviceType;
  icon?: string;
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

// ── 自动化相关 ────────────────────────────────────────────────────────────────

/** 自动化规则（用于仪表盘展示） */
export interface Automation {
  id: string;
  name: string;
  trigger: string;
  actions: string[];
  enabled: boolean;
  time: string;
  description: string;
}

export interface DeviceSummary {
  online: number;
  offline: number;
  total: number;
}
