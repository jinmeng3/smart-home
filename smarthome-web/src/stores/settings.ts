import { onScopeDispose, ref } from "vue";
import { defineStore } from "pinia";
import {
  getAccount,
  listHouseholds,
  listMembers,
  updateAccount as apiUpdateAccount,
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
  HouseholdRole,
  SecurityMeta,
  SettingsState,
} from "../types/settings";

const isAdminRole = (role: string | undefined) =>
  role?.toLowerCase() === "admin";

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

  const saveSettings = () => {
    if (settings.value.backup.autoBackup) {
      recordBackup("auto", "设置已保存时执行自动备份");
    } else {
      persistSettings(settings.value);
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

  const loadAccountHome = (force = false) => {
    if (accountHomeLoaded.value && !force) {
      return Promise.resolve();
    }
    if (accountHomePromise && !force) {
      return accountHomePromise;
    }

    loading.value = true;
    accountHomePromise = (async () => {
      const [account, households] = await Promise.all([
        getAccount(),
        listHouseholds(),
      ]);
      const householdEntries = await Promise.all(
        households.map(async (household) => ({
          household,
          members: await listMembers(household.id),
        })),
      );
      const householdEntry =
        householdEntries.find(({ members }) =>
          members.some((member) => member.userId === account.id),
        ) ?? householdEntries[0];
      const household = householdEntry?.household;
      const members = householdEntry?.members ?? [];
      const role = isAdminRole(household?.role) ? "管理员" : "成员";

      settings.value.account = {
        ...settings.value.account,
        id: account.id,
        username: account.name,
        email: account.email,
        avatarUrl: account.avatar_url,
        familyName: household?.name ?? "",
        householdId: household?.id,
        householdAddress: household?.address ?? null,
        householdTimezone: household?.timezone ?? "Asia/Shanghai",
        role,
        members,
      };
      settings.value.summary.currentHome = household?.name ?? "";
      settings.value.summary.accountStatus = role;
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
      : Promise.resolve(null);
    const [account, household] = await Promise.all([
      accountRequest,
      householdRequest,
    ]);

    settings.value.account = {
      ...settings.value.account,
      username: account.name,
      email: account.email,
      avatarUrl: account.avatar_url,
      familyName: household?.name ?? settings.value.account.familyName,
      householdAddress:
        household?.address ?? settings.value.account.householdAddress,
      householdTimezone:
        household?.timezone ?? settings.value.account.householdTimezone,
    };
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
        homeAssistant.serviceUrl &&
        (homeAssistant.tokenConfigured || homeAssistant.accessToken),
      ),
      description: settings.value.aiAssistant.language,
    };
    let response;

    try {
      response = await apiUpdateAIModel(payload);
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404) {
        throw error;
      }
      response = await apiCreateAIModel(payload);
    }

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
    const householdId = settings.value.account.householdId;
    if (!householdId) return;

    const member = await apiAddMember(householdId, { email, role });
    settings.value.account.members = [
      ...(settings.value.account.members ?? []),
      member,
    ];
  };

  const updateMemberRole = async (
    membershipId: number,
    role: HouseholdRole,
  ) => {
    const householdId = settings.value.account.householdId;
    if (!householdId) return;

    const updatedMember = await apiUpdateMemberRole(
      householdId,
      membershipId,
      role,
    );
    settings.value.account.members = (settings.value.account.members ?? []).map(
      (member) =>
        member.membershipId === membershipId ? updatedMember : member,
    );
  };

  const deleteHouseholdMember = async (membershipId: number) => {
    const householdId = settings.value.account.householdId;
    if (!householdId) return;

    await apiDeleteMember(householdId, membershipId);
    settings.value.account.members = (
      settings.value.account.members ?? []
    ).filter((member) => member.membershipId !== membershipId);
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
    ...structuredClone(settings.value),
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
    deleteAccountAvatar,
    deleteHouseholdMember,
    getExportSettings,
    importSettings,
    loadAIModel,
    loadAccountHome,
    loading,
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
