export interface Room {
  id: number;
  name: string;
  floor: string;
  roomType: string;
  imageUrl?: string | null;
  area: number;
  comfort: number;
  deviceCount: number;
  onlineCount: number;
  updatedAt: string;
}

export interface RoomListResponse {
  items: Room[];
  total: number;
}

export interface RoomDeviceCard {
  key: string;
  icon: string;
  name: string;
  detail: string;
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
  room_type?: string;
  icon?: string;
  theme_color?: string;
  device_ids?: number[];
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
  group: string;
  favorite: boolean;
  sortOrder: number;
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
  current_scene: string | null;
  recent_activity: string | null;
  recent_activity_time: string | null;
}

// ── 房间统计概览 ──────────────────────────────────────────────────────────────────

export interface RoomStats {
  room_count: number;
  room_count_change: number;
  online_rate: number;
  alert_count: number;
  pending_alert_count: number;
}
