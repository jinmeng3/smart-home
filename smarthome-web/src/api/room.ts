import { apiRequest } from "./client";
import type {
  Room,
  RoomListResponse,
  RoomInput,
  RoomDeviceListResponse,
  RoomDeviceBindingInput,
  RoomDeviceMetaInput,
  RoomLogListResponse,
  RoomEnvironmentLatest,
  RoomEnvironmentTrend,
  RoomEnvironmentReport,
  RoomScenePreview,
  RoomSceneExecution,
  RoomSceneListResponse,
} from "../types/room";

export const fetchRooms = (floor = "", roomType = "") => {
  const params = new URLSearchParams();
  if (floor) params.set("floor", floor);
  if (roomType) params.set("room_type", roomType);
  return apiRequest<RoomListResponse>(`/api/rooms?${params}`);
};

export const createRoom = (payload: RoomInput) =>
  apiRequest<Room>("/api/rooms", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const updateRoom = (roomId: number, payload: RoomInput) =>
  apiRequest<Room>(`/api/rooms/${roomId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const updateRoomDevice = (
  roomId: number,
  device: string,
  value: boolean | number | string,
) => apiRequest<Room>(`/api/rooms/${roomId}/device`, {
  method: "PATCH",
  body: JSON.stringify({ device, value }),
});

export const runRoomQuickAction = (roomId: number, action: string) =>
  apiRequest<Room>(`/api/rooms/${roomId}/quick-action`, {
    method: "POST",
    body: JSON.stringify({ action }),
  });

// ── 房间日志 ────────────────────────────────────────────────────────────────────

export const getRoomLogs = (
  roomId: number,
  params: {
    date_from?: string;
    date_to?: string;
    keyword?: string;
    page?: number;
    page_size?: number;
  } = {},
) => {
  const query = new URLSearchParams();
  if (params.date_from) query.set("date_from", params.date_from);
  if (params.date_to) query.set("date_to", params.date_to);
  if (params.keyword) query.set("keyword", params.keyword);
  if (params.page !== undefined) query.set("page", String(params.page));
  if (params.page_size !== undefined)
    query.set("page_size", String(params.page_size));
  const qs = query.toString();
  return apiRequest<RoomLogListResponse>(`/api/rooms/${roomId}/logs?${qs}`);
};

// ── 房间设备绑定 ────────────────────────────────────────────────────────────────

export const getRoomDevices = (
  roomId: number,
  params: { keyword?: string; type?: string; status?: string } = {},
) => {
  const query = new URLSearchParams();
  if (params.keyword) query.set("keyword", params.keyword);
  if (params.type) query.set("type", params.type);
  if (params.status) query.set("status", params.status);
  const qs = query.toString();
  return apiRequest<RoomDeviceListResponse>(
    `/api/rooms/${roomId}/devices?${qs}`,
  );
};

export const replaceRoomDevices = (
  roomId: number,
  devices: RoomDeviceBindingInput[],
) =>
  apiRequest<RoomDeviceListResponse>(`/api/rooms/${roomId}/devices`, {
    method: "PUT",
    body: JSON.stringify({ devices }),
  });

export const updateRoomDeviceMeta = (
  roomId: number,
  deviceId: number,
  payload: RoomDeviceMetaInput,
) =>
  apiRequest<RoomDeviceListResponse>(
    `/api/rooms/${roomId}/devices/${deviceId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );

// ── 房间环境 ────────────────────────────────────────────────────────────────────

export const getRoomEnvironmentLatest = (roomId: number) =>
  apiRequest<RoomEnvironmentLatest>(
    `/api/rooms/${roomId}/environment/latest`,
  );

export const getRoomEnvironmentTrends = (
  roomId: number,
  metrics = "temperature,humidity",
) =>
  apiRequest<RoomEnvironmentTrend>(
    `/api/rooms/${roomId}/environment/trends?metrics=${encodeURIComponent(
      metrics,
    )}`,
  );

export const createEnvironmentReport = (roomId: number) =>
  apiRequest<RoomEnvironmentReport>(`/api/rooms/${roomId}/environment/reports`, {
    method: "POST",
  });

export const getEnvironmentReport = (taskId: string) =>
  apiRequest<RoomEnvironmentReport>(`/api/environment/reports/${taskId}`);

// ── 房间场景 ────────────────────────────────────────────────────────────────────

export const getRoomScenes = (roomId: number) =>
  apiRequest<RoomSceneListResponse>(`/api/rooms/${roomId}/scenes`);

export const previewRoomScene = (roomId: number, sceneId: string) =>
  apiRequest<RoomScenePreview>(
    `/api/rooms/${roomId}/scenes/${sceneId}/preview`,
    {
      method: "POST",
    },
  );

export const executeRoomScene = (
  roomId: number,
  sceneId: string,
  payload: { scope?: "room" | "all"; sync_automation?: boolean } = {},
) =>
  apiRequest<RoomSceneExecution>(
    `/api/rooms/${roomId}/scenes/${sceneId}/execute`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
