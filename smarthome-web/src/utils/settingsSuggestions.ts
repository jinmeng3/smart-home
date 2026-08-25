import type {
  SettingsState,
  SettingsSuggestionItem,
} from "../types/settings";
import type { AIModelRead } from "../api/aiModel";

/**
 * 设置建议派生（SRP：纯函数，接收当前 settings 快照与 AI 模型列表，
 * 返回按优先级排序的建议数组；不依赖 Pinia、DOM 或 localStorage）。
 */

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/**
 * "08/25 15:30"（由 settingsPersistence.formatLocalTime 输出）回退解析。
 * 解析失败返回 null，调用方应理解为"无有效时间戳"。
 */
const parseLocalTimestamp = (raw: string | null | undefined): number | null => {
  if (!raw) return null;
  const match = raw.match(/^(\d{2})\/(\d{2})\s+(\d{2}):(\d{2})$/);
  if (!match) return null;
  const [, month, day, hour, minute] = match;
  const year = new Date().getFullYear();
  const date = new Date(
    year,
    Number(month) - 1,
    Number(day),
    Number(hour),
    Number(minute),
    0,
    0,
  );
  return Number.isNaN(date.getTime()) ? null : date.getTime();
};

/** 返回距今的天数；时间戳缺失或无效时返回 Infinity（视为"已陈旧"） */
const daysSince = (raw: string | null | undefined): number => {
  const ts = parseLocalTimestamp(raw);
  if (ts === null) return Infinity;
  return Math.floor((Date.now() - ts) / MS_PER_DAY);
};

export interface DeriveOptions {
  aiModels?: AIModelRead[];
  /** 注入当前时间便于测试；不传则取 Date.now() */
  now?: number;
}

/**
 * 规则匹配：基于真实 settings + aiModels 派生建议。
 * 返回结果会去掉已经"做好"的项目，只展示用户**未完成**的配置。
 */
export const deriveSuggestions = (
  settings: SettingsState,
  options: DeriveOptions = {},
): SettingsSuggestionItem[] => {
  const out: SettingsSuggestionItem[] = [];
  const { aiModels = [], now = Date.now() } = options;

  // 1) 双重认证（高优先级）
  if (!settings.security.twoFactorEnabled) {
    out.push({
      id: "enable-2fa",
      target: "security",
      title: "建议开启双重认证",
      description: "提升账户安全性，防止未授权访问",
    });
  }

  // 2) 自动备份
  if (!settings.backup.autoBackup) {
    out.push({
      id: "auto-backup",
      target: "backup",
      title: "建议启用自动备份",
      description: "定期备份配置，防止数据丢失",
    });
  } else if (daysSince(settings.backup.lastBackupTime) > 7) {
    out.push({
      id: "auto-backup-stale",
      target: "backup",
      title: "已超过 7 天未备份",
      description: "建议立即执行一次手动备份",
    });
  }

  // 3) 设备同步（空 / 超过 1 天）
  const syncDays = daysSince(settings.summary.lastSync);
  if (!Number.isFinite(syncDays) || syncDays > 1) {
    out.push({
      id: "sync-devices",
      target: "homeAssistant",
      title: !Number.isFinite(syncDays) ? "建议同步最新设备" : "设备同步已超过 24 小时",
      description: "保持设备数据最新，体验更稳定",
    });
  }

  // 4) Home Assistant 未配置 token
  if (!settings.homeAssistant.tokenConfigured) {
    out.push({
      id: "home-assistant-token",
      target: "homeAssistant",
      title: "Home Assistant 尚未连接",
      description: "填写服务地址与访问令牌后可启用设备联动",
    });
  }

  // 5) AI 模型未激活 / 未配置
  const hasActiveModel = aiModels.some((m) => m.is_active);
  if (aiModels.length === 0) {
    out.push({
      id: "ai-model-missing",
      target: "ai",
      title: "尚未配置 AI 模型",
      description: "添加并激活模型后才能使用智能对话与自动化",
    });
  } else if (!hasActiveModel) {
    out.push({
      id: "ai-model-inactive",
      target: "ai",
      title: "当前没有激活的 AI 模型",
      description: "在 AI 模型列表中选择一个模型并激活",
    });
  }

  // 6) 通知全关
  const allNotificationsOff =
    !settings.notifications.deviceOffline &&
    !settings.notifications.securityAlerts &&
    !settings.notifications.automationResults;
  if (allNotificationsOff) {
    out.push({
      id: "notifications-off",
      target: "notifications",
      title: "通知全部已关闭",
      description: "建议至少开启设备离线与安全告警通知",
    });
  }

  // 显式消费 now 以便测试/未来扩展（按需用于"上次活跃 N 天未聊天"等规则）
  void now;

  return out;
};
