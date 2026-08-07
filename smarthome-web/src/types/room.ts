export interface Room {
  id: number;
  name: string;
  floor: string;
  roomType: string;
  imageUrl?: string | null;
  icon: string;
  themeColor: string;
  version: number;
  area: number;
  comfort: number;
  deviceCount: number;
  onlineCount: number;
  updatedAt: string;
  device: RoomDeviceListItem[];
}

export interface RoomListResponse {
  items: Room[];
  total: number;
}

export interface RoomDeviceCard {
  id: number;
  key: string;
  icon: string;
  color?: string;
  name: string;
  detail: string;
  status: "online" | "offline" | "warning" | "running";
}

// ── 添加/编辑房间 ────────────────────────────────────────────────────────────────

export interface RoomPreferencesInput {
  pin_common_devices: boolean;
  show_environment: boolean;
  show_scene_entry: boolean;
}

export interface RoomInput {
  name: string;
  floor?: string;
  roomType?: string;
  icon?: string;
  themeColor?: string;
  deviceIds?: number[];
  preferences?: RoomPreferencesInput;
  version?: number | null;
}

// ── 房间设备列表 ────────────────────────────────────────────────────────────────

export interface RoomDeviceListItem {
  id: number;
  name: string;
  type: string;
  brand: string;
  status: string;
  icon: string;
  color: string;
  group: string;
  favorite: boolean;
  sortOrder: number;
  updatedAt: string;
}

export interface RoomDeviceListResponse {
  items: RoomDeviceListItem[];
  total: number;
}

export interface RoomDeviceBindingInput {
  device_id: number;
  group?: string;
  favorite?: boolean;
  sort_order?: number;
}

export interface RoomDeviceMetaInput {
  group?: string | null;
  favorite?: boolean | null;
  sort_order?: number | null;
}

// ── 房间活动日志 ────────────────────────────────────────────────────────────────

export interface RoomLog {
  id: number;
  occurredAt: string;
  source: string;
  event: string;
  result: string;
  durationMs: number | null;
  deviceId: number | null;
  deviceName: string | null;
  tags: string[];
  detail: Record<string, unknown>;
}

export interface RoomLogListResponse {
  total: number;
  items: RoomLog[];
}

// ── 房间环境 ────────────────────────────────────────────────────────────────────

export interface RoomEnvironmentLatest {
  sampledAt: string;
  values: Record<string, number>;
}

export interface RoomEnvironmentPoint {
  sampledAt: string;
  values: Record<string, number>;
}

export interface RoomEnvironmentTrend {
  metrics: string[];
  items: RoomEnvironmentPoint[];
}

export interface RoomEnvironmentReport {
  taskId: string;
  status: string;
  downloadUrl?: string | null;
}

// ── 房间场景 ────────────────────────────────────────────────────────────────────

export interface RoomScene {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  triggerType: string;
  triggerLabel: string;
  roomLabels: string[];
  deviceCount: number;
  enabled: boolean;
  recommended: boolean;
  highRisk: boolean;
  sortOrder: number;
  sourceTemplateId: string | null;
  createdAt: string;
  updatedAt: string;
  steps: Array<{ id: string; name: string; description: string; deviceId: string; order: number }>;
}

export interface RoomSceneListResponse {
  items: RoomScene[];
  total: number;
}

export interface RoomScenePreviewStep {
  stepId: string;
  name: string;
  deviceId: string;
  estimatedMs: number;
  riskLevel: "low" | "high";
}

export interface RoomScenePreview {
  sceneId: string;
  highRisk: boolean;
  triggerLabel: string;
  steps: RoomScenePreviewStep[];
}

export interface RoomSceneExecutionStep {
  stepId: string;
  status: string;
  message: string | null;
}

export interface RoomSceneExecution {
  executionId: string;
  sceneId: string;
  status: string;
  startedAt: string;
  finishedAt: string | null;
  steps: RoomSceneExecutionStep[];
}

// ── 房间详情（含最近活动和当前场景） ────────────────────────────────────────────────

export interface RoomDetail {
  room: Room;
  currentScene: string | null;
  recentActivity: string | null;
  recentActivityTime: string | null;
}

// ── 房间统计概览 ──────────────────────────────────────────────────────────────────

export interface RoomStats {
  roomCount: number;
  roomCountChange: number;
  onlineRate: number;
  alertCount: number;
  pendingAlertCount: number;
}