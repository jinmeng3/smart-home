import type {
  ModelAdvancedSettings,
  SettingsState,
} from "../types/settings";
/**
 * 设置持久化模块（SRP：负责本地设置的加载、合并与序列化，
 * 不承担账户、安全、备份等业务逻辑）。
 */

export const settingsStorageKey = "smart-home-settings";
const securityStorageKey = "smart-home-security-meta";
const backupStorageKey = "smart-home-backup-history";

const defaultSettings: SettingsState = {
  account: {
    username: "",
    email: "",
    avatarUrl: null,
    familyName: "",
    householdId: undefined,
    householdAddress: null,
    householdTimezone: "Asia/Shanghai",
    role: "",
    members: [],
  },
  appearance: {
    themeMode: "light",
    fontSize: "medium",
    animationsEnabled: true,
    performanceMode: false,
  },
  aiAssistant: {
    model: "Orion GPT-4o",
    temperature: 0.7,
    maxTokens: 4096,
    language: "zh-CN",
    detailLevel: 70,
    autoExecuteLowRisk: true,
    confirmHighRisk: true,
  },
  homeAssistant: {
    serviceUrl: "https://home.example.com:8123",
    accessToken: "",
    parameters: "{}",
    apiProtocol: "openai-completions",
    compat: "",
    tokenConfigured: false,
    websocketStatus: "disconnected",
  },
  notifications: {
    deviceOffline: true,
    securityAlerts: true,
    automationResults: true,
    quietStart: "23:00",
    quietEnd: "07:00",
  },
  security: {
    twoFactorEnabled: true,
  },
  backup: {
    autoBackup: true,
    lastBackupTime: "",
  },
  summary: {
    currentHome: "",
    accountStatus: "",
    homeAssistantStatus: "online",
    lastSync: "",
  },
  suggestions: [
    {
      id: "enable-2fa",
      target: "security",
      title: "建议开启双重认证",
      description: "提升账户安全性，防止未授权访问",
    },
    {
      id: "auto-backup",
      target: "backup",
      title: "建议启用自动备份",
      description: "定期备份配置，防止数据丢失",
    },
    {
      id: "sync-devices",
      target: "homeAssistant",
      title: "建议同步最新设备",
      description: "保持设备数据最新，体验更稳定",
    },
  ],
};

export const cloneSettings = (): SettingsState =>
  structuredClone(defaultSettings);

export const loadJson = <T>(key: string, fallback: T): T => {
  const raw = window.localStorage.getItem(key);

  if (!raw) {
    return fallback;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
};

export const normalizeModelLanguage = (
  language: unknown,
): ModelAdvancedSettings["language"] => {
  if (language === "en-US" || language === "English") {
    return "en-US";
  }
  if (language === "auto") {
    return "auto";
  }
  return "zh-CN";
};

export const mergeSettings = (
  nextSettings: Partial<SettingsState>,
): SettingsState => {
  const defaults = cloneSettings();

  return {
    ...defaults,
    ...nextSettings,
    account: defaults.account,
    appearance: { ...defaults.appearance, ...nextSettings.appearance },
    aiAssistant: {
      ...defaults.aiAssistant,
      ...nextSettings.aiAssistant,
      language: normalizeModelLanguage(nextSettings.aiAssistant?.language),
    },
    homeAssistant: {
      ...defaults.homeAssistant,
      ...nextSettings.homeAssistant,
      accessToken: "",
      parameters: nextSettings.homeAssistant?.parameters ?? "{}",
    },
    notifications: { ...defaults.notifications, ...nextSettings.notifications },
    security: { ...defaults.security, ...nextSettings.security },
    backup: { ...defaults.backup, ...nextSettings.backup },
    summary: { ...defaults.summary, ...nextSettings.summary },
  };
};

export const loadSettings = (): SettingsState => {
  const savedSettings = window.localStorage.getItem(settingsStorageKey);

  if (!savedSettings) {
    return cloneSettings();
  }

  try {
    return mergeSettings(JSON.parse(savedSettings) as Partial<SettingsState>);
  } catch {
    return cloneSettings();
  }
};

const getLocalPreferences = (
  settings: SettingsState,
): Partial<SettingsState> => ({
  appearance: settings.appearance,
  notifications: settings.notifications,
  security: settings.security,
  backup: settings.backup,
  aiAssistant: settings.aiAssistant,
});

export const persistSettings = (settings: SettingsState) => {
  window.localStorage.setItem(
    settingsStorageKey,
    JSON.stringify(getLocalPreferences(settings)),
  );
};

export const loadSecurityMeta = <T>(fallback: T): T =>
  loadJson<T>(securityStorageKey, fallback);

export const persistSecurityMeta = (value: unknown) => {
  window.localStorage.setItem(securityStorageKey, JSON.stringify(value));
};

export const loadBackupHistory = <T>(fallback: T): T =>
  loadJson<T>(backupStorageKey, fallback);

export const persistBackupHistory = (value: unknown) => {
  window.localStorage.setItem(backupStorageKey, JSON.stringify(value));
};

export const formatLocalTime = (date = new Date()) =>
  new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
