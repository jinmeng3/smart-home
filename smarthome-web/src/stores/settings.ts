import { computed, onScopeDispose, ref } from "vue";
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
  updateAIModelById as apiUpdateAIModelById,
  deleteAIModelById as apiDeleteAIModelById,
  type AIModelRead,
  type AIModelPayload,
} from "../api/aiModel";
import {
  addSecurityLog as apiAddSecurityLog,
  deleteSecurityDevice as apiDeleteSecurityDevice,
  getSecurityMeta as apiGetSecurityMeta,
  updateDeviceTrust as apiUpdateDeviceTrust,
} from "../api/security";
import { ApiError } from "../api/client";
import { syncDevices as apiSyncDevices } from "../api/device";
import { fetchAiSuggestions } from "../api/settingsAi";
import { useHouseholdStore } from "./households";
import {
  cloneSettings,
  formatLocalTime,
  loadBackupHistory,
  loadJson,
  loadSecurityMeta as loadStoredSecurityMeta,
  loadSettings,
  mergeSettings,
  persistBackupHistory,
  persistSecurityMeta,
  persistSettings,
  securityStorageKey,
} from "../utils/settingsPersistence";
import { deriveSuggestions } from "../utils/settingsSuggestions";
import {
  hashSnapshot,
  readAiSuggestionsCache,
  writeAiSuggestionsCache,
} from "../utils/aiSuggestionsCache";
import type {
  BackupRecord,
  HouseholdContext,
  HouseholdMember,
  HouseholdRole,
  SecurityMeta,
  SettingsState,
  SettingsSuggestionItem,
} from "../types/settings";

const createEmptySecurityMeta = (): SecurityMeta => ({
  passwordUpdatedAt: null,
  devices: [],
  logs: [],
});

export const useSettingsStore = defineStore("settings", () => {
  const settings = ref<SettingsState>(loadSettings());
  const securityMeta = ref<SecurityMeta>(
    loadStoredSecurityMeta(createEmptySecurityMeta()),
  );
  /** 基于真实 settings + aiModels 实时派生的设置建议（替换原硬编码） */
  const suggestions = computed(() =>
    deriveSuggestions(settings.value, { aiModels: aiModels.value }),
  );
  /** AI 生成的补充建议，默认未加载；调用 loadAiSuggestions 后填充 */
  const aiSuggestions = ref<SettingsSuggestionItem[]>([]);
  const aiSuggestionsLoading = ref(false);
  const aiSuggestionsError = ref<string | null>(null);
  let aiSuggestionsAbort: AbortController | null = null;
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

  /**
   * 写入一条备份记录到本地历史与 `lastBackupTime`。
   * 提前到 store 顶部以避免被 `saveSettings()` 引用时处于 TDZ。
   */
  const recordBackup = (type: "manual" | "auto", note?: string) => {
    const at = formatLocalTime();
    backupHistory.value = [
      {
        id: Date.now(),
        type,
        at,
        note: note ?? (type === "auto" ? "自动备份已完成" : "手动备份已生成"),
      },
      ...backupHistory.value,
    ].slice(0, 6);
    settings.value.backup.lastBackupTime = at;
    persistBackupHistory(backupHistory.value);
    persistSettings(settings.value);
  };

  const getUserPreferencesPayload = () => ({
    appearance: { ...settings.value.appearance },
    aiAssistant: {
      language: settings.value.aiAssistant.language,
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

  const securityMetaLoaded = ref(false);
  let securityMetaPromise: Promise<void> | null = null;

  const loadSecurityMeta = (force = false): Promise<void> => {
    if (securityMetaLoaded.value && !force) {
      return Promise.resolve();
    }
    if (securityMetaPromise && !force) {
      return securityMetaPromise;
    }

    const promise = (async () => {
      const meta = await apiGetSecurityMeta();

      // 首次从后端同步成功后，将旧 localStorage 中的安全日志导入后端（仅一次）
      if (meta.logs.length === 0) {
        const localMeta = loadJson<SecurityMeta | null>(
          securityStorageKey,
          null,
        );
        if (localMeta && localMeta.logs.length > 0) {
          void (async () => {
            for (const log of localMeta.logs) {
              try {
                await apiAddSecurityLog(log.title, log.detail);
              } catch {
                break;
              }
            }
            await loadSecurityMeta(true);
          })();
        }
      }

      securityMeta.value = meta;
      securityMetaLoaded.value = true;
      persistSecurityMeta(meta);
    })()
      .catch(() => {
        // 后端不可用时保留 localStorage 兜底数据，降级为离线模式
      })
      .finally(() => {
        securityMetaPromise = null;
      });

    securityMetaPromise = promise;
    return promise;
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
        apiProtocol: model.api ?? "openai-completions",
        compat: JSON.stringify(model.compat ?? {}, null, 2),
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

  /**
   * 调用后端 LLM 生成补充建议。
   * - 本地 cache（TTL 30 分钟）→ 后端 5 分钟缓存 → 实际 LLM 调用。
   * - 失败（无模型/网络/LLM 错误）时保留本地建议列表，error 用于 UI 提示。
   * - 重复调用会自动取消上一次未完成的请求。
   * - force=true 绕过本地与后端缓存。
   */
  const loadAiSuggestions = async (force = false) => {
    aiSuggestionsAbort?.abort();
    const controller = new AbortController();
    aiSuggestionsAbort = controller;
    aiSuggestionsLoading.value = true;
    aiSuggestionsError.value = null;
    try {
      // 快照中跳过大字段：accessToken / parameters / compat 这些与 LLM 提示无关
      const snapshot = {
        account: settings.value.account,
        appearance: settings.value.appearance,
        aiAssistant: {
          model: settings.value.aiAssistant.model,
          language: settings.value.aiAssistant.language,
          detailLevel: settings.value.aiAssistant.detailLevel,
          autoExecuteLowRisk: settings.value.aiAssistant.autoExecuteLowRisk,
          confirmHighRisk: settings.value.aiAssistant.confirmHighRisk,
        },
        homeAssistant: {
          serviceUrl: settings.value.homeAssistant.serviceUrl,
          apiProtocol: settings.value.homeAssistant.apiProtocol,
          tokenConfigured: settings.value.homeAssistant.tokenConfigured,
        },
        notifications: settings.value.notifications,
        security: settings.value.security,
        backup: settings.value.backup,
        summary: settings.value.summary,
        aiModels: aiModels.value.map((m) => ({
          name: m.name,
          provider: m.provider,
          is_active: m.is_active,
        })),
      };
      const hash = hashSnapshot(snapshot);

      // 1) 本地缓存命中直接返回，不发请求
      if (!force) {
        const cached = readAiSuggestionsCache(hash);
        if (cached.hit) {
          aiSuggestions.value = cached.suggestions;
          aiSuggestionsError.value = null;
          return;
        }
      }

      // 2) 调用后端（后端另有 5 分钟内存缓存）
      const result = await fetchAiSuggestions(snapshot, {
        force,
        signal: controller.signal,
      });
      aiSuggestions.value = result;

      // 3) 写入本地缓存
      if (!force) {
        writeAiSuggestionsCache(hash, result);
      }
    } catch (error) {
      if ((error as { name?: string })?.name === "AbortError") return;
      aiSuggestions.value = [];
      aiSuggestionsError.value =
        error instanceof Error ? error.message : "AI 建议生成失败";
    } finally {
      if (aiSuggestionsAbort === controller) {
        aiSuggestionsAbort = null;
        aiSuggestionsLoading.value = false;
      }
    }
  };

  /**
   * 取消进行中的 AI 建议请求。用于页面卸载 / 手动重置场景，
   * 避免 AbortController 跨越生命周期调用。
   */
  const cancelAiSuggestions = () => {
    aiSuggestionsAbort?.abort();
    aiSuggestionsAbort = null;
    aiSuggestionsLoading.value = false;
  };

  /**
   * 后台预取 AI 建议：仅在本地建议列表非空、且当前未在加载/未持有结果时触发。
   * 设计为"fire-and-forget"，调用方不需 await。失败会被 loadAiSuggestions 静默吞掉。
   */
  const prefetchAiSuggestionsIfNeeded = () => {
    if (aiSuggestionsLoading.value) return;
    if (aiSuggestions.value.length > 0) return;
    if (suggestions.value.length === 0) return;
    void loadAiSuggestions(false);
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

    const householdStore = useHouseholdStore();
    await householdStore.load(true);
    if (household?.id) {
      await householdStore.switchHousehold(household.id);
    }
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
    applyHouseholdContext(
      householdStore.activeHousehold,
      householdStore.members,
    );
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
    // 从当前选中的模型对象取 name/provider，而不是从 ai.model 字符串里猜
    // （ai.model 只保存模型名，旧逻辑按 " · " 拆分会把 provider 误判为 name）
    const selectedModel = aiModels.value.find(
      (model) => model.name === settings.value.aiAssistant.model,
    );
    let parameters: Record<string, unknown> = {};

    try {
      parameters = JSON.parse(homeAssistant.parameters || "{}") as Record<
        string,
        unknown
      >;
    } catch {
      parameters = {};
    }

    const payload: Record<string, unknown> = {
      name: selectedModel?.name || settings.value.aiAssistant.model,
      provider: selectedModel?.provider || "openai",
      api_endpoint: homeAssistant.serviceUrl,
      api: homeAssistant.apiProtocol,
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
    };

    try {
      const compat = JSON.parse(homeAssistant.compat || "{}") as Record<
        string,
        unknown
      >;
      if (Object.keys(compat).length > 0) payload.compat = compat;
    } catch {}
    const models = await apiListAIModels();
    const response = models.length
      ? await apiUpdateAIModel(payload)
      : await apiCreateAIModel(payload);

    settings.value.aiAssistant = {
      ...settings.value.aiAssistant,
      model: response.name,
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
      apiProtocol: response.api ?? "openai-completions",
      compat: JSON.stringify(response.compat ?? {}, null, 2),
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

  const refreshAIModels = async () => {
    aiModels.value = await apiListAIModels();
    return aiModels.value;
  };

  const createModel = async (payload: AIModelPayload) => {
    const created = await apiCreateAIModel(payload);
    await refreshAIModels();
    if (created.is_active) await loadAIModel();
    return created;
  };

  const updateModel = async (modelId: number, payload: AIModelPayload) => {
    const updated = await apiUpdateAIModelById(modelId, payload);
    await refreshAIModels();
    if (updated.is_active) await loadAIModel();
    return updated;
  };

  const activateModel = async (modelId: number) => {
    const activeModel = await apiActivateAIModel(modelId);
    await loadAIModel();
    return activeModel;
  };

  const removeModel = async (modelId: number) => {
    await apiDeleteAIModelById(modelId);
    await refreshAIModels();
    if (!aiModels.value.length) {
      settings.value.aiAssistant.model = "";
      settings.value.homeAssistant.serviceUrl = "";
      settings.value.homeAssistant.tokenConfigured = false;
      settings.value.homeAssistant.websocketStatus = "disconnected";
      settings.value.summary.homeAssistantStatus = "offline";
    }
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
    applyHouseholdContext(
      householdStore.activeHousehold,
      householdStore.members,
    );
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
    applyHouseholdContext(
      householdStore.activeHousehold,
      householdStore.members,
    );
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
    applyHouseholdContext(
      householdStore.activeHousehold,
      householdStore.members,
    );
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

  const syncDevices = async () => {
    const platforms: Array<"Home Assistant" | "Matter" | "Zigbee" | "MQTT"> = [
      "Home Assistant",
      "Matter",
      "Zigbee",
      "MQTT",
    ];

    let syncedCount = 0;
    let hasError = false;

    for (const platform of platforms) {
      try {
        const result = await apiSyncDevices(platform);
        syncedCount += result.synced_count;
      } catch {
        hasError = true;
      }
    }

    settings.value.summary.lastSync = hasError
      ? "同步完成（部分失败）"
      : syncedCount > 0
        ? `刚刚（${syncedCount} 台）`
        : "刚刚";
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

  const recordSecurityLog = async (title: string, detail: string) => {
    const localLog = {
      id: Date.now(),
      title,
      detail,
      at: formatLocalTime(),
    };

    try {
      await apiAddSecurityLog(title, detail);
    } catch {
      // 后端不可用时仅保留本地记录
    }

    securityMeta.value.logs = [localLog, ...securityMeta.value.logs].slice(
      0,
      8,
    );
    persistSecurityMeta(securityMeta.value);
  };

  const changeLocalPassword = () => {
    securityMeta.value.passwordUpdatedAt = formatLocalTime();
    void recordSecurityLog("已修改密码", "当前账户的本地安全记录已更新");
  };

  const updateDeviceTrust = async (deviceId: number, trusted: boolean) => {
    try {
      await apiUpdateDeviceTrust(deviceId, trusted);
    } catch {
      // 后端失败时保留本地状态
    }

    securityMeta.value.devices = securityMeta.value.devices.map((device) =>
      device.id === deviceId ? { ...device, trusted } : device,
    );
    void recordSecurityLog(
      trusted ? "已信任设备" : "已取消信任设备",
      "设备信任状态已更新",
    );
  };

  const revokeSecurityDevice = async (deviceId: number) => {
    const device = securityMeta.value.devices.find(
      (item) => item.id === deviceId,
    );

    if (!device || device.current) {
      return;
    }

    try {
      await apiDeleteSecurityDevice(deviceId);
    } catch {
      // 后端失败时保留本地状态
    }

    securityMeta.value.devices = securityMeta.value.devices.filter(
      (item) => item.id !== deviceId,
    );
    void recordSecurityLog("已移除登录设备", device.name);
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
    ...(JSON.parse(JSON.stringify(settings.value)) as SettingsState),
    homeAssistant: {
      ...settings.value.homeAssistant,
      accessToken: "",
    },
  });

  onScopeDispose(() => window.clearTimeout(saveStatusTimer));

  return {
    aiModels,
    activateModel,
    accountHomeLoaded,
    addHouseholdMember,
    applyHouseholdContext,
    createHousehold,
    createModel,
    deleteAccountAvatar,
    deleteHouseholdMember,
    getExportSettings,
    importSettings,
    loadAIModel,
    refreshAIModels,
    loadAiSuggestions,
    cancelAiSuggestions,
    prefetchAiSuggestionsIfNeeded,
    aiSuggestions,
    aiSuggestionsLoading,
    aiSuggestionsError,
    loadUserPreferences,
    loadAccountHome,
    loadSecurityMeta,
    loading,
    resetAccountState,
    resetSettings,
    removeModel,
    saveAccountHome,
    saveAIModel,
    selectAIModel,
    saveSettings,
    saveStatus,
    savedAt,
    settings,
    suggestions,
    backupHistory,
    changeLocalPassword,
    recordBackup,
    revokeSecurityDevice,
    syncDevices,
    securityMeta,
    updateBackupTime,
    updateModel,
    updateDeviceTrust,
    updateMemberRole,
    uploadAccountAvatar,
  };
});
