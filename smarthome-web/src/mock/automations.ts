// ── 自动化规则类型 ────────────────────────────────────────────────────────────────

export interface AutomationRule {
  id: number;
  name: string;
  description: string;
  trigger: string;
  devices: number;
  icon: string;
  tone: string;
  enabled: boolean;
}

// ── 自动化规则 Mock 数据 ──────────────────────────────────────────────────────────

export const automationRules: AutomationRule[] = [
  {
    id: 1,
    name: "回家联动",
    description: "位置触发 · 到达家半径 100m 内",
    trigger: "位置触发",
    devices: 6,
    icon: "home",
    tone: "blue",
    enabled: true,
  },
  {
    id: 2,
    name: "睡眠模式自动化",
    description: "时间触发 · 22:30 每天",
    trigger: "时间触发",
    devices: 5,
    icon: "clock",
    tone: "purple",
    enabled: true,
  },
  {
    id: 3,
    name: "离家安防联动",
    description: "位置触发 · 离开家 200m 外",
    trigger: "位置触发",
    devices: 7,
    icon: "security",
    tone: "green",
    enabled: true,
  },
  {
    id: 4,
    name: "空调节能联动",
    description: "设备状态 · 温度高于 28°C",
    trigger: "设备状态",
    devices: 4,
    icon: "air-conditioner",
    tone: "blue",
    enabled: false,
  },
  {
    id: 5,
    name: "晨间唤醒联动",
    description: "时间触发 · 07:00 工作日",
    trigger: "时间触发",
    devices: 6,
    icon: "illumination",
    tone: "orange",
    enabled: false,
  },
];