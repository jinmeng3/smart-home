export interface Room {
  id: number;
  name: string;
  floor: string;
  roomType: string;
  imageUrl?: string | null;
  area: number;
  comfort: number;
  temperature: number;
  humidity: number;
  pm25: number;
  illuminance: number;
  noise: number;
  deviceCount: number;
  onlineCount: number;
  deviceStates: Record<string, boolean | number | string>;
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
