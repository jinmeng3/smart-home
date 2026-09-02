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

// === DTO 类型（后端 snake_case）与映射函数 ===

interface ApiRoom {
  id: number;
  name: string;
  floor: string;
  room_type: string;
  image_url?: string | null;
  icon?: string;
  theme_color?: string;
  device?: Room["device"];
  device_count?: number;
  online_count?: number;
  area: number;
  comfort: number;
  status: string;
  version?: number | null;
  created_at: string;
  updated_at: string;
}

interface ApiRoomListResponse {
  items: ApiRoom[];
  total: number;
}

interface ApiRoomDetailResponse {
  room: ApiRoom;
  current_scene?: string | null;
  recent_activity?: string | null;
  recent_activity_time?: string | null;
}

interface ApiRoomStats {
  room_count: number;
  room_count_change?: number;
  online_rate?: number;
  alert_count?: number;
  pending_alert_count?: number;
}

const mapRoom = (data: ApiRoom): Room => ({
  id: data.id,
  name: data.name,
  floor: data.floor,
  roomType: data.room_type,
  imageUrl: data.image_url ?? null,
  icon: data.icon ?? "room",
  themeColor: data.theme_color ?? "",
  version: data.version ?? 0,
  area: data.area,
  comfort: data.comfort,
  deviceCount: data.device_count ?? 0,
  onlineCount: data.online_count ?? 0,
  updatedAt: data.updated_at,
  device: data.device ?? [],
});

const mapRoomDetail = (data: ApiRoomDetailResponse): RoomDetail => ({
  room: mapRoom(data.room),
  currentScene: data.current_scene ?? null,
  recentActivity: data.recent_activity ?? null,
  recentActivityTime: data.recent_activity_time ?? null,
});

const mapRoomStats = (data: ApiRoomStats): RoomStats => ({
  roomCount: data.room_count,
  roomCountChange: data.room_count_change ?? 0,
  onlineRate: data.online_rate ?? 0,
  alertCount: data.alert_count ?? 0,
  pendingAlertCount: data.pending_alert_count ?? 0,
});

// === API 导出函数 ===

export const fetchRooms = async (floor = "", roomType = "") => {
  const params = new URLSearchParams();
  if (floor) params.set("floor", floor);
  if (roomType) params.set("room_type", roomType);
  const data = await apiRequest<ApiRoomListResponse>(`/api/rooms?${params}`);
  return { items: data.items.map(mapRoom), total: data.total };
};

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

// === 房间日志 ===

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

// === 房间设备绑定 ===

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

// === 房间环境 ===

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

// === 房间场景 ===

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

// === 房间详情 ===

export const fetchRoomDetail = async (roomId: number) => {
  const data = await apiRequest<ApiRoomDetailResponse>(`/api/rooms/${roomId}`);
  return mapRoomDetail(data);
};

// === 房间统计概览 ===

export const fetchRoomStats = async () => {
  const data = await apiRequest<ApiRoomStats>("/api/rooms/stats");
  return mapRoomStats(data);
};

// === 房间删除 ===

export const deleteRoom = (roomId: number) =>
  apiRequest<null>(`/api/rooms/${roomId}`, {
    method: "DELETE",
  });
