/** 房间类型 → 图标映射 */
export const roomTypeIconMap: Record<string, string> = {
    living: "home",
    bedroom: "room",
    study: "comfort",
    kitchen: "plug",
    balcony: "illumination",
    bathroom: "humidity",
};

export const getRoomTypeIcon = (roomType: string): string =>
    roomTypeIconMap[roomType] ?? "room";

/** 房间类型 → 主题色 */
export const roomTypeColorMap: Record<string, string> = {
    living: "var(--color-primary-500)",
    bedroom: "var(--tone-indigo)",
    study: "var(--color-teal-600)",
    kitchen: "var(--color-device-light)",
    balcony: "var(--color-success)",
    bathroom: "var(--color-info)",
};

/** 房间类型 → 浅色背景 */
export const roomTypeBgMap: Record<string, string> = {
    living: "var(--color-primary-50)",
    bedroom: "var(--tone-indigo-soft)",
    study: "var(--color-teal-soft)",
    kitchen: "var(--color-warning-soft)",
    balcony: "var(--color-success-soft)",
    bathroom: "var(--color-info-soft)",
};

/** 房间类型选项列表 */
export const roomTypes = [
    { value: "living", label: "客厅", icon: "home" },
    { value: "bedroom", label: "卧室", icon: "room" },
    { value: "study", label: "书房", icon: "comfort" },
    { value: "kitchen", label: "厨房", icon: "plug" },
    { value: "balcony", label: "阳台", icon: "illumination" },
    { value: "bathroom", label: "卫生间", icon: "humidity" },
    { value: "custom", label: "自定义", icon: "edit" },
] as const;

/** 设备 key → 分类名称 */
export const keyToCategory: Record<string, string> = {
    light: "灯光",
    airConditioner: "空调",
    curtain: "窗帘",
    plug: "插座",
    scene: "场景",
};

/** 环境指标配置 */
export const metricConfig: Record<string, { name: string; unit: string; tone: string }> = {
    temperature: { name: "温度", unit: "°C", tone: "blue" },
    humidity: { name: "湿度", unit: "%", tone: "blue" },
    pm25: { name: "PM2.5", unit: " μg/m³", tone: "green" },
    illuminance: { name: "光照", unit: " lux", tone: "orange" },
    noise: { name: "噪音", unit: " dB", tone: "purple" },
};

/** 环境指标语义标签 */
export const metricLabels: Record<string, (val: number) => string> = {
    temperature: (v) => v < 18 ? "偏冷" : v <= 26 ? "舒适" : "偏热",
    humidity: (v) => v < 30 ? "干燥" : v <= 60 ? "舒适" : "潮湿",
    pm25: (v) => v < 35 ? "优" : v <= 75 ? "良" : "差",
    illuminance: (v) => v < 50 ? "偏暗" : v <= 500 ? "适中" : "明亮",
    noise: (v) => v < 40 ? "安静" : v <= 60 ? "正常" : "嘈杂",
};