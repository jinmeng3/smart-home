import { onScopeDispose, ref } from "vue";
import { defineStore } from "pinia";
import {
  createHousehold as apiCreateHousehold,
  getAccount,
  getUserPreferences as apiGetUserPreferences,
  updateAccount as apiUpdateAccount,
  updateUserPreferences as apiUpdateUserPreferences,
  updateHousehold as apiUpdateHousehold,
  addMember as apiAddMember,
  updateMemberRole as apiUpdateMemberRole,
  deleteMember as apiDeleteMember,
  uploadAvatar as apiUploadAvatar,
  deleteAvatar as apiDeleteAvatar,
} from "../api/account";
import {
  listAIModels as apiListAIModels,
  getAIModel as apiGetAIModel,
  updateAIModel as apiUpdateAIModel,
  createAIModel as apiCreateAIModel,
  activateAIModel as apiActivateAIModel,
  type AIModelRead,
} from "../api/aiModel";
import { ApiError } from "../api/client";
import { useHouseholdStore } from "./households";
import {
  cloneSettings,
  formatLocalTime,
  loadBackupHistory,
  loadSecurityMeta,
  loadSettings,
  mergeSettings,
  normalizeModelLanguage,
  persistBackupHistory,
  persistSecurityMeta,
  persistSettings,
} from "../utils/settingsPersistence";
import type {
  BackupRecord,
  HouseholdContext,
  HouseholdMember,
  HouseholdRole,
  SecurityMeta,
  SettingsState,
} from "../types/settings";

const createDefaultSecurityMeta = (): SecurityMeta => ({
  passwordUpdatedAt: null,
  devices: [
    {
      id: 1,
      name: "当前设备",
      location: "上海 · 桌面浏览器",
      lastActive: formatLocalTime(),
      trusted: true,
      current: true,
    },
    {
      id: 2,
      name: "移动设备",
      location: "上海 · 手机",
      lastActive: "07/30 21:18",
      trusted: false,
      current: false,
    },
  ],
  logs: [
    {
      id: 1,
      title: "已启用二次验证",
      detail: "当前账户的本地安全开关已同步到设置中心",
      at: "07/31 09:40",
    },
  ],
});

export const useSettingsStore = defineStore("settings", () => {
  const settings = ref<SettingsState>(loadSettings());
  const securityMeta = ref<SecurityMeta>(
    loadSecurityMeta(createDefaultSecurityMeta()),
  );
  const backupHistory = ref<BackupRecord[]>(
    loadBackupHistory([] as BackupRecord[]),
  );
  const savedAt = ref<string | null>(null);
  const saveStatus = ref<"idle" | "saved">("idle");
  const loading = ref(false);
  const aiModels = ref<AIModelRead[]>([]);
  const accountHomeLoaded = ref(false);
  let accountHomePromise: Promise<void> | null = null;
  let saveStatusTimer = 0;

  const getUserPreferencesPayload = () => ({
    appearance: { ...settings.value.appearance },
    aiAssistant: {
      detailLevel: settings.value.aiAssistant.detailLevel,
      autoExecuteLowRisk: settings.value.aiAssistant.autoExecuteLowRisk,
      confirmHighRisk: settings.value.aiAssistant.confirmHighRisk,
    },
    notifications: { ...settings.value.notifications },
    security: { ...settings.value.security },
    backup: { autoBackup: settings.value.backup.autoBackup },
  });

  const loadUserPreferences = async () => {
    const preferences = await apiGetUserPreferences();
    settings.value.appearance = preferences.appearance;
    settings.value.aiAssistant = {
      ...settings.value.aiAssistant,
      ...preferences.aiAssistant,
    };
    settings.value.notifications = preferences.notifications;
    settings.value.security = preferences.security;
    settings.value.backup = {
      ...settings.value.backup,
      ...preferences.backup,
    };
    // 服务端是偏好唯一真相：不回写本地缓存，避免与服务端双真相。
    // 无需跨端同步的 UI 偏好（如侧栏折叠）仍由各自模块本地保存。
  };

  const saveSettings = async () => {
    await apiUpdateUserPreferences(getUserPreferencesPayload());
    if (settings.value.backup.autoBackup) {
      recordBackup("auto", "设置已保存时执行自动备份");
    }
    savedAt.value = new Intl.DateTimeFormat("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }).format(new Date());
    saveStatus.value = "saved";
    window.clearTimeout(saveStatusTimer);
    saveStatusTimer = window.setTimeout(() => {
      saveStatus.value = "idle";
    }, 1600);
  };

  /** 将家庭上下文（活动家庭 + 成员 + 角色）镜像到设置 store，供既有组件消费。 */
  const applyHouseholdContext = (
    household: HouseholdContext | null,
    members: HouseholdMember[],
  ) => {
    const roleLabel = household
      ? household.role === "admin"
        ? "管理员"
        : "成员"
      : "";
    settings.value.account = {
      ...settings.value.account,
      familyName: household?.name ?? "",
      householdId: household?.id,
      householdAddress: household?.address ?? null,
      householdTimezone: household?.timezone ?? "Asia/Shanghai",
      role: roleLabel,
      members,
    };
    settings.value.summary.currentHome = household?.name ?? "";
    settings.value.summary.accountStatus = roleLabel;
  };

  const loadAccountHome = (force = false) => {
    if (accountHomeLoaded.value && !force) {
      return Promise.resolve();
    }
    if (accountHomePromise && !force) {
      return accountHomePromise;
    }

    loading.value = true;
    accountHomePromise = (async () => {
      const account = await getAccount();
      // 家庭列表 / 活动家庭 / 角色 / 成员以全局家庭上下文为唯一真相。
      const householdStore = useHouseholdStore();
      await householdStore.load(force);
      applyHouseholdContext(
        householdStore.activeHousehold,
        householdStore.members,
      );
      settings.value.account = {
        ...settings.value.account,
        id: account.id,
        username: account.name,
        email: account.email,
        avatarUrl: account.avatar_url,
      };
      accountHomeLoaded.value = true;
    })().finally(() => {
      loading.value = false;
      accountHomePromise = null;
    });

    return accountHomePromise;
  };

  const loadAIModel = async () => {
    try {
      aiModels.value = await apiListAIModels();
      const model =
        aiModels.value.find((item) => item.is_active) ??
        aiModels.value[0] ??
        (await apiGetAIModel());

      settings.value.aiAssistant = {
        ...settings.value.aiAssistant,
        model: model.name,
        language: normalizeModelLanguage(model.description),
        temperature: model.temperature,
        maxTokens: model.max_tokens,
        autoExecuteLowRisk: model.is_active,
        confirmHighRisk: model.is_active,
      };
      settings.value.homeAssistant = {
        ...settings.value.homeAssistant,
        serviceUrl: model.api_endpoint,
        accessToken: "",
        parameters: JSON.stringify(model.parameters ?? {}, null, 2),
        tokenConfigured: model.is_active,
        websocketStatus: model.is_active ? "connected" : "disconnected",
      };
      settings.value.summary.homeAssistantStatus = model.is_active
        ? "online"
        : "offline";
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404) {
        throw error;
      }
    }
  };

  const saveAccountHome = async () => {
    const householdId = settings.value.account.householdId;
    const accountRequest = apiUpdateAccount({
      name: settings.value.account.username,
      email: settings.value.account.email,
    });
    const householdRequest = householdId
      ? apiUpdateHousehold(householdId, {
          name: settings.value.account.familyName,
          address: settings.value.account.householdAddress,
          timezone: settings.value.account.householdTimezone,
        })
      : apiCreateHousehold({
          name: settings.value.account.familyName,
          address: settings.value.account.householdAddress,
          timezone: settings.value.account.householdTimezone,
        });
    const [account, household] = await Promise.all([
      accountRequest,
      householdRequest,
    ]);

    // 家庭数据以全局上下文为准：刷新列表并保持新/当前家庭为活动家庭。
    const householdStore = useHouseholdStore();
    await householdStore.load(true);
    if (household?.id) {
      await householdStore.switchHousehold(household.id);
    }
    applyHouseholdContext(householdStore.activeHousehold, householdStore.members);

    settings.value.account = {
      ...settings.value.account,
      id: account.id,
      username: account.name,
      email: account.email,
      avatarUrl: account.avatar_url,
    };
  };

  const createHousehold = async (payload: {
    name: string;
    address?: string | null;
    timezone?: string;
  }) => {
    const created = await apiCreateHousehold(payload);
    const householdStore = useHouseholdStore();
    await householdStore.load(true);
    await householdStore.switchHousehold(created.id);
    applyHouseholdContext(householdStore.activeHousehold, householdStore.members);
    return created;
  };

  const resetAccountState = () => {
    settings.value.account = {
      id: undefined,
      username: "",
      email: "",
      avatarUrl: null,
      familyName: "",
      householdId: undefined,
      householdAddress: null,
      householdTimezone: "Asia/Shanghai",
      role: "",
      members: [],
    };
    settings.value.summary.currentHome = "";
    settings.value.summary.accountStatus = "";
    accountHomeLoaded.value = false;
  };

  const saveAIModel = async () => {
    const homeAssistant = settings.value.homeAssistant;
    const [modelName, modelProvider] = settings.value.aiAssistant.model
      .split(" · ")
      .map((value) => value.trim());
    let parameters: Record<string, unknown> = {};

    try {
      parameters = JSON.parse(homeAssistant.parameters || "{}") as Record<
        string,
        unknown
      >;
    } catch {
      parameters = {};
    }

    const payload = {
      name: modelName || settings.value.aiAssistant.model,
      provider: modelProvider || modelName || settings.value.aiAssistant.model,
      api_endpoint: homeAssistant.serviceUrl,
      ...(homeAssistant.accessToken
        ? { api_key: homeAssistant.accessToken }
        : {}),
      temperature: settings.value.aiAssistant.temperature,
      max_tokens: settings.value.aiAssistant.maxTokens,
      parameters,
      is_active: Boolean(
        homeAssistant.websocketStatus === "connected" &&
        homeAssistant.serviceUrl &&
        (homeAssistant.tokenConfigured || homeAssistant.accessToken),
      ),
      description: settings.value.aiAssistant.language,
    };
    const models = await apiListAIModels();
    const response = models.length
      ? await apiUpdateAIModel(payload)
      : await apiCreateAIModel(payload);

    settings.value.aiAssistant = {
      ...settings.value.aiAssistant,
      model: response.name,
      language: normalizeModelLanguage(response.description),
      temperature: response.temperature,
      maxTokens: response.max_tokens,
      autoExecuteLowRisk: response.is_active,
      confirmHighRisk: response.is_active,
    };
    settings.value.homeAssistant = {
      ...settings.value.homeAssistant,
      serviceUrl: response.api_endpoint,
      accessToken: "",
      parameters: JSON.stringify(response.parameters ?? {}, null, 2),
      tokenConfigured: response.is_active,
      websocketStatus: response.is_active ? "connected" : "disconnected",
    };
    settings.value.summary.homeAssistantStatus = response.is_active
      ? "online"
      : "offline";
  };

  const selectAIModel = async (name: string) => {
    const selected = aiModels.value.find((model) => model.name === name);
    if (!selected) return;

    const activeModel = await apiActivateAIModel(selected.id);
    aiModels.value = aiModels.value.map((model) => ({
      ...model,
      is_active: model.id === activeModel.id,
    }));
    settings.value.aiAssistant = {
      ...settings.value.aiAssistant,
      model: activeModel.name,
      language: normalizeModelLanguage(activeModel.description),
      temperature: activeModel.temperature,
      maxTokens: activeModel.max_tokens,
    };
    settings.value.homeAssistant = {
      ...settings.value.homeAssistant,
      serviceUrl: activeModel.api_endpoint,
      accessToken: "",
      parameters: JSON.stringify(activeModel.parameters ?? {}, null, 2),
      tokenConfigured: activeModel.is_active,
      websocketStatus: activeModel.is_active ? "connected" : "disconnected",
    };
  };

  const uploadAccountAvatar = async (file: File) => {
    const response = await apiUploadAvatar(file);
    settings.value.account.avatarUrl = response.avatar_url;
  };

  const deleteAccountAvatar = async () => {
    const response = await apiDeleteAvatar();
    settings.value.account.avatarUrl = response.avatar_url;
  };

  const addHouseholdMember = async (email: string, role: HouseholdRole) => {
    const householdStore = useHouseholdStore();
    const householdId = householdStore.activeHouseholdId;
    if (!householdId) {
      throw new Error("请先创建或选择家庭");
    }

    const member = await apiAddMember(householdId, { email, role });
    await householdStore.refreshMembers();
    applyHouseholdContext(householdStore.activeHousehold, householdStore.members);
    return member;
  };

  const updateMemberRole = async (
    membershipId: number,
    role: HouseholdRole,
  ) => {
    const householdStore = useHouseholdStore();
    const householdId = householdStore.activeHouseholdId;
    if (!householdId) {
      throw new Error("请先创建或选择家庭");
    }

    const updatedMember = await apiUpdateMemberRole(
      householdId,
      membershipId,
      role,
    );
    await householdStore.refreshMembers();
    applyHouseholdContext(householdStore.activeHousehold, householdStore.members);
    return updatedMember;
  };

  const deleteHouseholdMember = async (membershipId: number) => {
    const householdStore = useHouseholdStore();
    const householdId = householdStore.activeHouseholdId;
    if (!householdId) {
      throw new Error("请先创建或选择家庭");
    }

    await apiDeleteMember(householdId, membershipId);
    await householdStore.refreshMembers();
    applyHouseholdContext(householdStore.activeHousehold, householdStore.members);
  };

  const resetSettings = () => {
    const runtimeSettings = settings.value;
    settings.value = mergeSettings({
      account: runtimeSettings.account,
      homeAssistant: {
        ...runtimeSettings.homeAssistant,
        accessToken: "",
      },
      summary: runtimeSettings.summary,
    });
    persistSettings(settings.value);
    saveStatus.value = "idle";
  };

  const syncDevices = () => {
    settings.value.summary.lastSync = "刚刚";
  };

  const updateBackupTime = () => {
    settings.value.backup.lastBackupTime = new Intl.DateTimeFormat("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(new Date());
  };

  const recordSecurityLog = (title: string, detail: string) => {
    securityMeta.value.logs = [
      {
        id: Date.now(),
        title,
        detail,
        at: formatLocalTime(),
      },
      ...securityMeta.value.logs,
    ].slice(0, 8);
    persistSecurityMeta(securityMeta.value);
  };

  const changeLocalPassword = () => {
    securityMeta.value.passwordUpdatedAt = formatLocalTime();
    recordSecurityLog("已修改密码", "当前账户的本地安全记录已更新");
  };

  const updateDeviceTrust = (deviceId: number, trusted: boolean) => {
    securityMeta.value.devices = securityMeta.value.devices.map((device) =>
      device.id === deviceId ? { ...device, trusted } : device,
    );
    recordSecurityLog(
      trusted ? "已信任设备" : "已取消信任设备",
      "设备信任状态已在本地更新",
    );
  };

  const revokeSecurityDevice = (deviceId: number) => {
    const device = securityMeta.value.devices.find(
      (item) => item.id === deviceId,
    );

    if (!device || device.current) {
      return;
    }

    securityMeta.value.devices = securityMeta.value.devices.filter(
      (item) => item.id !== deviceId,
    );
    recordSecurityLog("已移除登录设备", device.name);
  };

  const recordBackup = (type: "manual" | "auto", note?: string) => {
    const at = formatLocalTime();
    backupHistory.value = [
      {
        id: Date.now(),
        type,
        at,
        note:
          note ??
          (type === "auto"
            ? "自动备份已完成"
            : "手动备份已生成"),
      },
      ...backupHistory.value,
    ].slice(0, 6);
    settings.value.backup.lastBackupTime = at;
    persistBackupHistory(backupHistory.value);
    persistSettings(settings.value);
  };

  const importSettings = (nextSettings: SettingsState) => {
    const runtimeAccount = settings.value.account;
    const runtimeHomeAssistant = settings.value.homeAssistant;
    settings.value = mergeSettings(nextSettings);
    settings.value.account = runtimeAccount;
    settings.value.homeAssistant = {
      ...settings.value.homeAssistant,
      serviceUrl: runtimeHomeAssistant.serviceUrl,
      accessToken: "",
      tokenConfigured: runtimeHomeAssistant.tokenConfigured,
      websocketStatus: runtimeHomeAssistant.websocketStatus,
    };
    persistSettings(settings.value);
    saveStatus.value = "idle";
  };

  const getExportSettings = (): SettingsState => ({
    ...JSON.parse(JSON.stringify(settings.value)) as SettingsState,
    homeAssistant: {
      ...settings.value.homeAssistant,
      accessToken: "",
    },
  });

  onScopeDispose(() => window.clearTimeout(saveStatusTimer));

  return {
    aiModels,
    accountHomeLoaded,
    addHouseholdMember,
    applyHouseholdContext,
    createHousehold,
    deleteAccountAvatar,
    deleteHouseholdMember,
    getExportSettings,
    importSettings,
    loadAIModel,
    loadUserPreferences,
    loadAccountHome,
    loading,
    resetAccountState,
    resetSettings,
    saveAccountHome,
    saveAIModel,
    selectAIModel,
    saveSettings,
    saveStatus,
    savedAt,
    settings,
    backupHistory,
    changeLocalPassword,
    recordBackup,
    revokeSecurityDevice,
    syncDevices,
    securityMeta,
    updateBackupTime,
    updateDeviceTrust,
    updateMemberRole,
    uploadAccountAvatar,
  };
});
