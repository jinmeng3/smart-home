import { apiRequest } from "./client";
import { formatLocalTime } from "../utils/settingsPersistence";
import type { SecurityDevice, SecurityLog, SecurityMeta } from "../types/settings";

// === DTO 类型 ===

interface SecurityDeviceRead {
  id: number;
  device_name: string;
  location: string;
  last_active_at: string;
  trusted: boolean;
  is_current: boolean;
}

interface SecurityLogRead {
  id: number;
  title: string;
  detail: string;
  created_at: string;
}

interface SecurityMetaRead {
  password_updated_at: string | null;
  devices: SecurityDeviceRead[];
  logs: SecurityLogRead[];
}

// === 映射函数 ===

const formatDateTime = (value: string | null): string | null => {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return formatLocalTime(date);
};

const toDevice = (device: SecurityDeviceRead): SecurityDevice => ({
  id: device.id,
  name: device.device_name,
  location: device.location,
  lastActive: formatDateTime(device.last_active_at) ?? "",
  trusted: device.trusted,
  current: device.is_current,
});

const toLog = (log: SecurityLogRead): SecurityLog => ({
  id: log.id,
  title: log.title,
  detail: log.detail,
  at: formatDateTime(log.created_at) ?? "",
});

// === API 导出函数 ===

export const getSecurityMeta = async (): Promise<SecurityMeta> => {
  const data = await apiRequest<SecurityMetaRead>("/api/account/me/security");
  return {
    passwordUpdatedAt: formatDateTime(data.password_updated_at),
    devices: data.devices.map(toDevice),
    logs: data.logs.map(toLog),
  };
};

export const addSecurityLog = (title: string, detail: string) =>
  apiRequest<SecurityLogRead>("/api/account/me/security/logs", {
    method: "POST",
    body: JSON.stringify({ title, detail }),
  });

export const updateDeviceTrust = (deviceId: number, trusted: boolean) =>
  apiRequest<SecurityDeviceRead>(
    `/api/account/me/security/devices/${deviceId}`,
    {
      method: "PATCH",
      body: JSON.stringify({ trusted }),
    },
  );

export const deleteSecurityDevice = (deviceId: number) =>
  apiRequest<void>(`/api/account/me/security/devices/${deviceId}`, {
    method: "DELETE",
  });