import {
  fetchRooms as apiFetchRooms,
  runRoomQuickAction as apiRunRoomQuickAction,
  updateRoomDevice as apiUpdateRoomDevice,
} from "../api/room";
import type { Room, RoomListResponse } from "../types/room";

/**
 * 房间领域服务层（DIP：视图只依赖此抽象，
 * 不直接依赖 API 实现；单一职责——仅编排房间操作）。
 */
export const roomService = {
  list(floor = "", roomType = ""): Promise<RoomListResponse> {
    return apiFetchRooms(floor, roomType);
  },

  updateDevice(
    roomId: number,
    device: string,
    value: boolean | number | string,
  ): Promise<Room> {
    return apiUpdateRoomDevice(roomId, device, value);
  },

  runQuickAction(roomId: number, action: string): Promise<Room> {
    return apiRunRoomQuickAction(roomId, action);
  },
};
