import { apiRequest } from "./client";
import type { Room, RoomListResponse } from "../types/room";

export const fetchRooms = (floor = "", roomType = "") => {
  const params = new URLSearchParams();
  if (floor) params.set("floor", floor);
  if (roomType) params.set("room_type", roomType);
  return apiRequest<RoomListResponse>(`/api/rooms?${params}`);
};

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
