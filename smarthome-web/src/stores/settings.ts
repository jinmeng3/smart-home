import { onScopeDispose, ref, watch } from "vue";
import { defineStore } from "pinia";
import {
  addMember as apiAddMember,
  deleteAvatar as apiDeleteAvatar,
  deleteMember as apiDeleteMember,
  getAccount,
  listHouseholds,
  listMembers,
  updateAccount,
  updateHousehold,
  updateMemberRole as apiUpdateMemberRole,
  uploadAvatar as apiUploadAvatar,
} from "../api/account";
import { createAIModel, getAIModel, updateAIModel } from "../api/aiModel";
import { ApiError } from "../api/client";
import { defaultSettings } from "../mock/settings";
import type {
  HouseholdRole,
  ModelAdvancedSettings,
  SettingsState,
} from "../types/settings";

const storageKey = "smart-home-settings";

const cloneSettings = (): SettingsState => structuredClone(defaultSettings);

const normalizeModelLanguage = (
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

const mergeSettings = (nextSettings: Partial<SettingsState>): SettingsState => {
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
    },
    notifications: { ...defaults.notifications, ...nextSettings.notifications },
    security: { ...defaults.security, ...nextSettings.security },
    backup: { ...defaults.backup, ...nextSettings.backup },
    summary: { ...defaults.summary, ...nextSettings.summary },
  };
};

const loadSettings = (): SettingsState => {
  const savedSettings = window.localStorage.getItem(storageKey);

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

const isAdminRole = (role: string | undefined) =>
  role?.toLowerCase() === "admin";

export const useSettingsStore = defineStore("settings", () => {
  const settings = ref<SettingsState>(loadSettings());
  const savedAt = ref<string | null>(null);
  const saveStatus = ref<"idle" | "saved">("idle");
  const loading = ref(false);
  const accountHomeLoaded = ref(false);
  let accountHomePromise: Promise<void> | null = null;
  let saveStatusTimer = 0;

  const persistLocalPreferences = () => {
    window.localStorage.setItem(
      storageKey,
      JSON.stringify(getLocalPreferences(settings.value)),
    );
  };
  persistLocalPreferences();

  watch(
    () => [
      settings.value.appearance.themeMode,
      settings.value.appearance.fontSize,
      settings.value.appearance.animationsEnabled,
      settings.value.appearance.sidebarCollapsed,
    ],
    persistLocalPreferences,
  );

  const saveSettings = () => {
    persistLocalPreferences();
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
      const household = households[0];
      const members = household ? await listMembers(household.id) : [];
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
      const model = await getAIModel();

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
    const accountRequest = updateAccount({
      name: settings.value.account.username,
      email: settings.value.account.email,
    });
    const householdRequest = householdId
      ? updateHousehold(householdId, {
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
    const payload = {
      name: settings.value.aiAssistant.model,
      provider:
        settings.value.aiAssistant.model.split(" ")[0] ??
        settings.value.aiAssistant.model,
      api_endpoint: homeAssistant.serviceUrl,
      ...(homeAssistant.accessToken
        ? { api_key: homeAssistant.accessToken }
        : {}),
      temperature: settings.value.aiAssistant.temperature,
      max_tokens: settings.value.aiAssistant.maxTokens,
      is_active: Boolean(
        homeAssistant.serviceUrl &&
        (homeAssistant.tokenConfigured || homeAssistant.accessToken),
      ),
      description: settings.value.aiAssistant.language,
    };
    let response;

    try {
      response = await updateAIModel(payload);
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 404) {
        throw error;
      }
      response = await createAIModel(payload);
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
      tokenConfigured: response.is_active,
      websocketStatus: response.is_active ? "connected" : "disconnected",
    };
    settings.value.summary.homeAssistantStatus = response.is_active
      ? "online"
      : "offline";
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
    persistLocalPreferences();
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
    persistLocalPreferences();
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
    saveSettings,
    saveStatus,
    savedAt,
    settings,
    syncDevices,
    updateBackupTime,
    updateMemberRole,
    uploadAccountAvatar,
  };
});
