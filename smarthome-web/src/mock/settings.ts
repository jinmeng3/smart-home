import type { SettingsState } from '../types/settings'

export const defaultSettings: SettingsState = {
  account: {
    username: '',
    email: '',
    avatarUrl: null,
    familyName: '',
    householdId: undefined,
    householdAddress: null,
    householdTimezone: 'Asia/Shanghai',
    role: '',
    members: [],
  },
  appearance: {
    themeMode: 'light',
    fontSize: 'medium',
    animationsEnabled: true,
    sidebarCollapsed: false,
  },
  aiAssistant: {
    model: 'Orion GPT-4o',
    temperature: 0.7,
    maxTokens: 4096,
    language: 'zh-CN',
    detailLevel: 70,
    autoExecuteLowRisk: true,
    confirmHighRisk: true,
  },
  homeAssistant: {
    serviceUrl: 'https://home.example.com:8123',
    accessToken: 'orion-home-assistant-access-token',
    websocketStatus: 'connected',
  },
  notifications: {
    deviceOffline: true,
    securityAlerts: true,
    automationResults: true,
    quietStart: '23:00',
    quietEnd: '07:00',
  },
  security: {
    twoFactorEnabled: true,
  },
  backup: {
    autoBackup: true,
    lastBackupTime: '今天 09:40',
  },
  summary: {
    currentHome: '',
    accountStatus: '',
    homeAssistantStatus: 'online',
    lastSync: '5 分钟前',
  },
  suggestions: [
    {
      id: 'enable-2fa',
      target: 'security',
      title: '建议开启双重认证',
      description: '提升账户安全性，防止未授权访问',
    },
    {
      id: 'auto-backup',
      target: 'backup',
      title: '建议启用自动备份',
      description: '定期备份配置，防止数据丢失',
    },
    {
      id: 'sync-devices',
      target: 'homeAssistant',
      title: '建议同步最新设备',
      description: '保持设备数据最新，体验更稳定',
    },
  ],
}
