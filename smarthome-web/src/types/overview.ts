// ── 家庭日程 ──────────────────────────────────────────────────────────────────────

export interface ScheduleItem {
  id?: number;
  time: string;
  name: string;
  detail: string;
  scene_id?: string;
  position: number;
  enabled: boolean;
  color: string;
}

export interface HouseholdSchedule {
  id: number;
  scheduleDate: string;
  enabled: boolean;
  repeatDays: number[];
  targets: { room_ids?: number[]; device_ids?: number[] };
  items: ScheduleItem[];
  version: number;
  updatedAt: string;
}

export interface ScheduleWrite {
  enabled: boolean;
  repeatDays: number[];
  targets: { room_ids?: number[]; device_ids?: number[] };
  items: ScheduleItem[];
  version?: number;
}

// ── 首页总览 ──────────────────────────────────────────────────────────────────────

/**
 * 注意：概览接口 (OverviewRead 及其嵌套模型) 未继承 OverviewSchema，
 * 因此后端直接返回 snake_case 字段名，此处类型与后端响应保持一致。
 */
export interface OverviewSummary {
  device_total: number;
  device_online: number;
  running_automation_count: number;
  alert_count: number;
  monthly_energy_kwh: number;
  energy_saving_rate: number;
}

export interface HomeStatus {
  status: string;
  people_home: number;
  temperature: number;
  humidity: number;
  air_quality: string;
  pm25: number;
  locked_count: number;
  lock_total: number;
}

export interface OverviewRoom {
  id: number;
  name: string;
  device_count: number;
  light_on: number;
  light_total: number;
  temperature: number;
  device_summaries: string[];
}

export interface OverviewRecentDevice {
  id: number;
  name: string;
  room_name: string;
  online: boolean;
  state_text: string;
  updated_at: string;
}

export interface HouseholdOverview {
  summary: OverviewSummary;
  home_status: HomeStatus;
  rooms: OverviewRoom[];
  recent_devices: OverviewRecentDevice[];
  activities: unknown[];
  schedule: unknown[];
  alerts: unknown[];
}

// ── 模式执行 ──────────────────────────────────────────────────────────────────────

export type OverviewMode = "home" | "away" | "sleep" | "guest";

export interface ModeExecuteInput {
  mode: OverviewMode;
  roomIds?: number[];
  runAutomations?: boolean;
  idempotencyKey: string;
}

// ── 任务结果（模式执行 / 设备巡检） ──────────────────────────────────────────────────

export interface TaskResult {
  id: number;
  status: string;
  affectedDeviceCount?: number;
  checkedCount?: number;
  deviceCount?: number;
  estimatedSeconds?: number;
}

// ── 设备巡检 ──────────────────────────────────────────────────────────────────────

export type InspectionScope = "all" | "rooms" | "device_types";

export interface InspectionInput {
  scope: InspectionScope;
  roomIds?: number[];
  deviceTypes?: string[];
  checks: string[];
}

// ── 设备同步任务 ────────────────────────────────────────────────────────────────────

export interface SyncJobInput {
  scope?: string;
  sources: string[];
  options?: Record<string, boolean>;
  idempotencyKey: string;
}

export interface SyncJobResult {
  id: number;
  status: string;
  statistics: Record<string, number>;
}
