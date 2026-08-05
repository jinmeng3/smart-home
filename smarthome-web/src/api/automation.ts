import { apiRequest } from "./client";
import type {
  AutomationCreate,
  AutomationListResponse,
  AutomationRule,
  AutomationUpdate,
  BatchEnableRead,
  BatchScheduleWrite,
  EnabledRead,
  ExecuteRead,
  ExecutionListRead,
} from "../types/automation";

/** 自动化规则 HTTP 请求层（SRP：纯请求与查询构建，不含业务编排）。 */

// ── 查询参数构建 ────────────────────────────────────────────────────────────────────

const buildAutomationQuery = (params: {
  keyword?: string;
  triggerType?: string;
  enabled?: boolean;
  page?: number;
  pageSize?: number;
}) => {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 20),
  });
  if (params.keyword) query.set("keyword", params.keyword);
  if (params.triggerType) query.set("trigger_type", params.triggerType);
  if (params.enabled !== undefined) query.set("enabled", String(params.enabled));
  return query.toString();
};

// ── 自动化规则 CRUD ───────────────────────────────────────────────────────────────

export const listAutomations = (
  householdId: number,
  params: {
    keyword?: string;
    triggerType?: string;
    enabled?: boolean;
    page?: number;
    pageSize?: number;
  } = {},
) =>
  apiRequest<AutomationListResponse>(
    `/api/households/${householdId}/automations?${buildAutomationQuery(params)}`,
  );

export const createAutomation = (householdId: number, payload: AutomationCreate) =>
  apiRequest<AutomationRule>(`/api/households/${householdId}/automations`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getAutomation = (automationId: number) =>
  apiRequest<AutomationRule>(`/api/automations/${automationId}`);

export const updateAutomation = (automationId: number, payload: AutomationUpdate) =>
  apiRequest<AutomationRule>(`/api/automations/${automationId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const toggleAutomationEnabled = (automationId: number, enabled: boolean) =>
  apiRequest<EnabledRead>(`/api/automations/${automationId}/enabled`, {
    method: "PATCH",
    body: JSON.stringify({ enabled }),
  });

// ── 执行与记录 ────────────────────────────────────────────────────────────────────

export const executeAutomation = (
  automationId: number,
  source = "manual",
  idempotencyKey?: string,
) =>
  apiRequest<ExecuteRead>(
    `/api/automations/${automationId}/execute`,
    {
      method: "POST",
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined,
      body: JSON.stringify({ source }),
    },
  );

export const listAutomationExecutions = (
  automationId: number,
  params: { page?: number; pageSize?: number; status?: string } = {},
) => {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 20),
  });
  if (params.status) query.set("status", params.status);

  return apiRequest<ExecutionListRead>(
    `/api/automations/${automationId}/executions?${query}`,
  );
};

// ── 批量操作 ──────────────────────────────────────────────────────────────────────

export const batchEnableAutomations = (payload: {
  ruleIds: number[];
  executeNow?: boolean;
  executionIntervalSeconds?: number;
}) =>
  apiRequest<BatchEnableRead>("/api/automations/batch-enable", {
    method: "POST",
    body: JSON.stringify({
      ruleIds: payload.ruleIds,
      executeNow: payload.executeNow ?? false,
      executionIntervalSeconds: payload.executionIntervalSeconds ?? 0,
    }),
  });

export const batchSetAutomationSchedule = (payload: BatchScheduleWrite) =>
  apiRequest<BatchEnableRead>("/api/automations/schedules/batch", {
    method: "PUT",
    body: JSON.stringify({
      ruleIds: payload.ruleIds,
      timezone: payload.timezone,
      time: payload.time,
      weekdays: payload.weekdays,
      frequency: payload.frequency,
      interval: payload.interval ?? 1,
    }),
  });
