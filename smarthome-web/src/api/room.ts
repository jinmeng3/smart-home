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
  RoomDetail,
  RoomStats,
} from "../types/room";

// ── DTO 类型（后端 snake_case）与映射函数 ───────────────────────────────────────────
// 后端响应使用 Pydantic camelCase alias；组件/store 只消费领域模型。

interface ApiRoom {
  id: number;
  name: string;
  floor: string;
  roomType: string;
  imageUrl?: string | null;
  icon?: string;
  themeColor?: string;
  device?: Room["device"];
  deviceCount?: number;
  onlineCount?: number;
  area: number;
  comfort: number;
  status: string;
  version?: number | null;
  createdAt: string;
  updatedAt: string;
}

interface ApiRoomListResponse {
  items: ApiRoom[];
  total: number;
}

interface ApiRoomDetailResponse {
  room: ApiRoom;
  currentScene?: string | null;
  recentActivity?: string | null;
  recentActivityTime?: string | null;
}

interface ApiRoomStats {
  roomCount: number;
  roomCountChange?: number;
  onlineRate?: number;
  alertCount?: number;
  pendingAlertCount?: number;
}

const mapRoom = (data: ApiRoom): Room => ({
  id: data.id,
  name: data.name,
  floor: data.floor,
  roomType: data.roomType,
  imageUrl: data.imageUrl ?? null,
  icon: data.icon ?? "room",
  themeColor: data.themeColor ?? "",
  version: data.version ?? 0,
  area: data.area,
  comfort: data.comfort,
  deviceCount: data.deviceCount ?? 0,
  onlineCount: data.onlineCount ?? 0,
  updatedAt: data.updatedAt,
  device: data.device ?? [],
});

const mapRoomDetail = (data: ApiRoomDetailResponse): RoomDetail => ({
  room: mapRoom(data.room),
  currentScene: data.currentScene ?? null,
  recentActivity: data.recentActivity ?? null,
  recentActivityTime: data.recentActivityTime ?? null,
});

const mapRoomStats = (data: ApiRoomStats): RoomStats => ({
  roomCount: data.roomCount,
  roomCountChange: data.roomCountChange ?? 0,
  onlineRate: data.onlineRate ?? 0,
  alertCount: data.alertCount ?? 0,
  pendingAlertCount: data.pendingAlertCount ?? 0,
});

// ── API 导出函数 ──────────────────────────────────────────────────────────────────

// fetchRooms 通过 mapper 统一 API DTO 与前端领域模型。
export const fetchRooms = async (floor = "", roomType = "") => {
  const params = new URLSearchParams();
  if (floor) params.set("floor", floor);
  if (roomType) params.set("room_type", roomType);
  const data = await apiRequest<ApiRoomListResponse>(`/api/rooms?${params}`);
  return { items: data.items.map(mapRoom), total: data.total };
};

// 修正：使用 POST /api/rooms，而非已废弃的 /api/rooms/add
export const createRoom = async (payload: RoomInput) => {
  const data = await apiRequest<ApiRoom>("/api/rooms", {
    method: "POST",
    body: JSON.stringify({
      name: payload.name,
      floor: payload.floor,
      room_type: payload.roomType,
      icon: payload.icon ?? "room",
      theme_color: payload.themeColor ?? "",
      device_ids: payload.deviceIds ?? [],
      version: payload.version,
    }),
  });
  return mapRoom(data);
};

// 修正：使用 PATCH /api/rooms/{id}，而非已废弃的 PUT /api/rooms/{id}
export const updateRoom = async (roomId: number, payload: RoomInput) => {
  const data = await apiRequest<ApiRoom>(`/api/rooms/${roomId}`, {
    method: "PATCH",
    body: JSON.stringify({
      name: payload.name,
      floor: payload.floor,
      room_type: payload.roomType,
      icon: payload.icon ?? "room",
      theme_color: payload.themeColor ?? "",
      device_ids: payload.deviceIds ?? [],
      version: payload.version,
    }),
  });
  return mapRoom(data);
};

export const updateRoomDevice = (
  roomId: number,
  deviceId: number,
  status: string,
) => apiRequest<ApiRoom>(`/api/rooms/${roomId}/device`, {
  method: "PATCH",
  body: JSON.stringify({ device_id: deviceId, status }),
}).then(mapRoom);

export const runRoomQuickAction = (roomId: number, action: string) =>
  apiRequest<ApiRoom>(`/api/rooms/${roomId}/quick-action`, {
    method: "POST",
    body: JSON.stringify({ action }),
  }).then(mapRoom);

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

// ── 房间详情 ──────────────────────────────────────────────────────────────────

// 使用 GET /api/rooms/{id}，并通过 mapper 统一领域模型。
export const fetchRoomDetail = async (roomId: number) => {
  const data = await apiRequest<ApiRoomDetailResponse>(`/api/rooms/${roomId}`);
  return mapRoomDetail(data);
};

// ── 房间统计概览 ──────────────────────────────────────────────────────────────

export const fetchRoomStats = async () => {
  const data = await apiRequest<ApiRoomStats>("/api/rooms/stats");
  return mapRoomStats(data);
};

// ── 房间删除 ──────────────────────────────────────────────────────────────────

export const deleteRoom = (roomId: number) =>
  apiRequest<null>(`/api/rooms/${roomId}`, {
    method: "DELETE",
  });
