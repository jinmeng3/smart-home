import { apiRequest } from "./client";
import { mapDevice, type ApiDevice } from "./device";
import type { DeviceListResponse } from "../types/device";
import type {
  HouseholdOverview,
  HouseholdSchedule,
  InspectionInput,
  ModeExecuteInput,
  ScheduleItem,
  ScheduleWrite,
  SyncJobInput,
  SyncJobResult,
  TaskResult,
} from "../types/overview";

export type {
  HouseholdSchedule,
  ScheduleItem,
  ScheduleWrite,
} from "../types/overview";

/** 总览与日程 HTTP 请求层（SRP：纯请求与查询构建，不含业务编排）。 */

// === 首页总览 ===

export const getHouseholdOverview = (householdId: number) =>
  apiRequest<HouseholdOverview>(`/api/households/${householdId}/overview`);

export const getHouseholdDevices = async (
  householdId: number,
): Promise<DeviceListResponse> => {
  const response = await apiRequest<{ total: number; items: ApiDevice[] }>(
    `/api/households/${householdId}/devices`,
  );
  return {
    total: response.total,
    items: response.items.map(mapDevice),
  };
};

export const syncHouseholdDevices = (householdId: number) =>
  apiRequest<SyncJobResult>(
    `/api/households/${householdId}/devices/sync`,
    { method: "POST" },
  );

// === 模式执行 ===

export const executeMode = (payload: ModeExecuteInput) =>
  apiRequest<TaskResult>("/api/overview/modes/execute", {
    method: "POST",
    body: JSON.stringify({
      mode: payload.mode,
      roomIds: payload.roomIds ?? [],
      runAutomations: payload.runAutomations ?? true,
      idempotencyKey: payload.idempotencyKey,
    }),
  });

// === 设备巡检 ===

export const createInspection = (payload: InspectionInput) =>
  apiRequest<TaskResult>("/api/inspections", {
    method: "POST",
    body: JSON.stringify({
      scope: payload.scope,
      roomIds: payload.roomIds ?? [],
      deviceTypes: payload.deviceTypes ?? [],
      checks: payload.checks,
    }),
  });

export const getInspection = (inspectionId: number) =>
  apiRequest<TaskResult>(`/api/inspections/${inspectionId}`);

// === 设备同步任务 ===

export const createSyncJob = (payload: SyncJobInput) =>
  apiRequest<SyncJobResult>("/api/device-sync-jobs", {
    method: "POST",
    body: JSON.stringify({
      scope: payload.scope ?? "all",
      sources: payload.sources,
      options: payload.options ?? {},
      idempotencyKey: payload.idempotencyKey,
    }),
  });

export const getSyncJob = (jobId: number) =>
  apiRequest<SyncJobResult>(`/api/device-sync-jobs/${jobId}`);

// === 家庭日程 ===

export const getSchedule = (date: string) =>
  apiRequest<HouseholdSchedule | null>(`/api/schedules/${date}`);

export const saveSchedule = (date: string, payload: ScheduleWrite) =>
  apiRequest<HouseholdSchedule>(`/api/schedules/${date}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
