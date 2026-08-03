import type { DeviceFilters } from "../../types/device";

/** 设备列表查询串构建（SRP：URL 构建职责独立于请求与映射）。 */

export const buildDeviceQuery = (filters: DeviceFilters) => {
  const params = new URLSearchParams({
    page: String(filters.page),
    page_size: String(filters.pageSize),
  });

  if (filters.keyword.trim()) {
    params.set("keyword", filters.keyword.trim());
  }

  if (filters.type) {
    params.set("type", filters.type);
  }

  if (filters.status) {
    params.set("status", filters.status);
  }

  if (filters.room.trim()) {
    params.set("room", filters.room.trim());
  }

  return params.toString();
};
