<script setup lang="ts">
import {
    computed,
    nextTick,
    onBeforeUnmount,
    onMounted,
    reactive,
    ref,
    watch,
} from "vue";
import { onBeforeRouteLeave } from "vue-router";
import { ElMessage } from "element-plus";
import ConfirmActionDialog from "../components/common/ConfirmActionDialog.vue";
import ConfirmEntitySummary from "../components/common/ConfirmEntitySummary.vue";
import AccountFamilyCard from "../components/settings/AccountFamilyCard.vue";
import AiAssistantSettingsCard from "../components/settings/AiAssistantSettingsCard.vue";
import AppearanceSettingsCard from "../components/settings/AppearanceSettingsCard.vue";
import BackupSettingsCard from "../components/settings/BackupSettingsCard.vue";
import HomeAssistantSettingsCard from "../components/settings/HomeAssistantSettingsCard.vue";
import MemberManagementCard from "../components/settings/MemberManagementCard.vue";
import NotificationSettingsCard from "../components/settings/NotificationSettingsCard.vue";
import SecuritySettingsCard from "../components/settings/SecuritySettingsCard.vue";
import BaseCollapsibleRail from "../components/common/BaseCollapsibleRail.vue";
import ConfigHealthCard from "../components/settings/ConfigHealthCard.vue";
import SettingsDirectory from "../components/settings/SettingsDirectory.vue";
import SettingsSuggestionPanel from "../components/settings/SettingsSuggestionPanel.vue";
import SettingsSummaryPanel from "../components/settings/SettingsSummaryPanel.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import { useSettingsStore } from "../stores/settings";
import { useHouseholdStore } from "../stores/households";
import { useAuthStore } from "../stores/auth";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { getErrorMessage } from "../utils/error";
import { ApiError } from "../api/client";
import { settingsSections, sectionIds } from "../constants/settingsSections";
import type { AccountForm, FamilyMember, HouseholdRole } from "../types/settings";
import type { SettingsSectionId } from "../types/settings";

const settingsStore = useSettingsStore();
const householdStore = useHouseholdStore();
const authStore = useAuthStore();

const activeSection = ref<SettingsSectionId>("account");
const savingAccount = ref(false);
const addingMember = ref(false);
const loadingMemberId = ref<number | null>(null);
const switchingHousehold = ref(false);
const initialAccountSnapshot = ref<string>();
const initialIntegrationSnapshot = ref<string>();
const initialPreferencesSnapshot = ref<string>();

/** 表单字段级错误（来自 ApiError.fieldErrors，422 校验定位到具体字段） */
const accountFieldErrors = ref<Record<string, string>>({});
/** 成员添加表单的字段级错误 */
const memberFieldErrors = ref<Record<string, string>>({});

/* === 集中式确认弹窗 === */
interface ConfirmRequest {
    tone: "warning" | "danger";
    title: string;
    description: string;
    confirmText: string;
    cancelText?: string;
    warning: string;
    footerHint?: string;
    summary?: { icon: string; title: string; description?: string; color: string };
    onConfirm: () => void | Promise<void>;
}
const confirmRequest = ref<ConfirmRequest | null>(null);
const confirmLoading = ref(false);
const runConfirm = async () => {
    const request = confirmRequest.value;
    if (!request || confirmLoading.value) return;
    confirmLoading.value = true;
    try {
        await request.onConfirm();
        confirmRequest.value = null;
    } catch {
        // 业务异常已由调用方处理，保持弹窗关闭
        confirmRequest.value = null;
    } finally {
        confirmLoading.value = false;
    }
};

/* === 移动端分区标签（从统一配置生成） === */
const mobileSections = computed(() =>
    settingsSections.map((s) => ({ id: s.id, label: s.shortLabel })),
);

/* === 更多操作下拉菜单 === */
const moreActionsOpen = ref(false);
const moreActionsRef = ref<HTMLElement | null>(null);
const toggleMoreActions = () => {
    moreActionsOpen.value = !moreActionsOpen.value;
};
const closeMoreActions = (event: MouseEvent) => {
    if (
        moreActionsRef.value &&
        !moreActionsRef.value.contains(event.target as Node)
    ) {
        moreActionsOpen.value = false;
    }
};

/* === 恢复默认确认 === */
const confirmReset = () => {
    confirmRequest.value = {
        tone: "danger",
        title: "恢复默认设置",
        description: "以下配置将恢复为出厂默认值：界面外观、智能助手配置、Home Assistant 接入凭证、通知与安全偏好。",
        confirmText: "确认恢复",
        warning: "此操作不可撤销；账户与家庭信息不受影响。",
        footerHint: "确认后会立即执行重置",
        summary: {
            icon: "refresh",
            title: "恢复默认设置",
            description: "界面 · 智能助手 · 接入凭证 · 通知与安全",
            color: "var(--color-danger)",
        },
        onConfirm: () => {
            settingsStore.resetSettings();
            syncAccountForm();
            syncIntegrationSnapshot();
            syncPreferencesSnapshot();
            ElMessage.success("已恢复默认设置");
            moreActionsOpen.value = false;
        },
    };
};

// 滚动监听（单 IntersectionObserver 实例）
const scrollContainer = ref<HTMLElement | null>(null);
let sectionObserver: IntersectionObserver | null = null;
/** 点击目录后短时间锁定，避免平滑滚动过程中高亮跳动 */
let scrollLockUntil = 0;

const setupScrollObserver = () => {
    const container = scrollContainer.value;
    if (!container) return;

    sectionObserver = new IntersectionObserver(
        (entries) => {
            if (Date.now() < scrollLockUntil) return;
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    const id = entry.target.id as SettingsSectionId;
                    if (sectionIds.includes(id)) {
                        activeSection.value = id;
                    }
                    break;
                }
            }
        },
        {
            root: container,
            rootMargin: "-50% 0px -50% 0px",
            threshold: 0,
        },
    );

    settingsSections.forEach(({ id }) => {
        const el = document.getElementById(id);
        if (el) sectionObserver?.observe(el);
    });
};

const cleanupScrollObserver = () => {
    sectionObserver?.disconnect();
    sectionObserver = null;
};

const settings = computed(() => settingsStore.settings);
const accountForm = reactive<AccountForm>({
    name: "",
    email: "",
    avatarUrl: null,
    householdName: "",
    address: "",
    timezone: "Asia/Shanghai",
});
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const accountSnapshot = computed(() => JSON.stringify(accountForm));
const accountDirty = computed(
    () => initialAccountSnapshot.value !== undefined && accountSnapshot.value !== initialAccountSnapshot.value,
);
const integrationSnapshot = computed(() =>
    JSON.stringify({
        aiAssistant: settings.value.aiAssistant,
        homeAssistant: settings.value.homeAssistant,
    }),
);
const integrationDirty = computed(
    () => initialIntegrationSnapshot.value !== undefined && integrationSnapshot.value !== initialIntegrationSnapshot.value,
);
const preferencesSnapshot = computed(() =>
    JSON.stringify({
        appearance: settings.value.appearance,
        aiAssistant: {
            detailLevel: settings.value.aiAssistant.detailLevel,
            autoExecuteLowRisk: settings.value.aiAssistant.autoExecuteLowRisk,
            confirmHighRisk: settings.value.aiAssistant.confirmHighRisk,
        },
        notifications: settings.value.notifications,
        security: settings.value.security,
        autoBackup: settings.value.backup.autoBackup,
    }),
);
const preferencesDirty = computed(
    () => initialPreferencesSnapshot.value !== undefined && preferencesSnapshot.value !== initialPreferencesSnapshot.value,
);
const settingsDirty = computed(
    () => accountDirty.value || integrationDirty.value || preferencesDirty.value,
);

/** 具体修改项数 */
const dirtyCount = computed(() => {
    let count = 0;
    if (accountDirty.value) count++;
    if (integrationDirty.value) count++;
    if (preferencesDirty.value) count++;
    return count;
});

const householdMembers = computed(() => settings.value.account.members ?? []);

/** 已完成的配置项数量（用于目录进度条） */
const completedConfigCount = computed(() => {
    let count = 2; // 账户 + 界面 默认已完成
    if (settings.value.aiAssistant.model) count++;
    if (settings.value.homeAssistant.tokenConfigured) count++;
    count++; // 通知 默认已完成
    if (settings.value.security.twoFactorEnabled) count++;
    if (settings.value.backup.autoBackup) count++;
    if (householdMembers.value.length > 0) count++;
    return count;
});
const members = computed<FamilyMember[]>(() =>
    householdMembers.value.map((member) => ({
        id: member.membershipId,
        name: member.name,
        email: member.email,
        avatarUrl: member.avatarUrl,
        role: member.role,
    })),
);
const currentMemberId = computed(() => {
    const accountId = settings.value.account.id;

    if (!accountId) {
        return null;
    }

    return (
        householdMembers.value.find((member) => member.userId === accountId)
            ?.membershipId ?? null
    );
});
const currentMemberRole = computed(
    () =>
        householdMembers.value.find(
            (member) => member.membershipId === currentMemberId.value,
        )?.role,
);
const adminCount = computed(
    () =>
        householdMembers.value.filter((member) => member.role === "admin")
            .length,
);
const canManageMembers = computed(
    () =>
        householdStore.activeRole === "admin" ||
        currentMemberRole.value === "admin",
);

const syncAccountForm = () => {
    accountForm.name = settings.value.account.username;
    accountForm.email = settings.value.account.email;
    accountForm.avatarUrl = settings.value.account.avatarUrl ?? null;
    accountForm.householdName = settings.value.account.familyName;
    accountForm.address = settings.value.account.householdAddress ?? "";
    accountForm.timezone =
        settings.value.account.householdTimezone ?? "Asia/Shanghai";
    initialAccountSnapshot.value = accountSnapshot.value;
};

const syncIntegrationSnapshot = () => {
    initialIntegrationSnapshot.value = integrationSnapshot.value;
};

const syncPreferencesSnapshot = () => {
    initialPreferencesSnapshot.value = preferencesSnapshot.value;
};

const selectSection = (section: SettingsSectionId) => {
    activeSection.value = section;
    // 锁定 800ms，避免平滑滚动过程中 observer 反复切换
    scrollLockUntil = Date.now() + 800;
    document
        .getElementById(section)
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
};

const handleBeforeUnload = (event: BeforeUnloadEvent) => {
    if (!settingsDirty.value) {
        return;
    }

    event.preventDefault();
    event.returnValue = "";
};

const loadSettings = async () => {
    await Promise.all([
        settingsStore
            .loadAccountHome()
            .catch((error: unknown) => {
                ElMessage.error(getErrorMessage(error, "账户与家庭信息加载失败"));
            }),
        settingsStore
            .loadAIModel()
            .catch((error: unknown) => {
                ElMessage.error(getErrorMessage(error, "AI 模型配置加载失败"));
            }),
        settingsStore
            .loadUserPreferences()
            .catch((error: unknown) => {
                ElMessage.error(getErrorMessage(error, "用户偏好加载失败"));
            }),
    ]);

    syncAccountForm();
    syncIntegrationSnapshot();
    syncPreferencesSnapshot();
};

useAuthenticatedLoader(loadSettings);

onMounted(() => {
    syncAccountForm();
    syncIntegrationSnapshot();
    syncPreferencesSnapshot();
    window.addEventListener("beforeunload", handleBeforeUnload);
    document.addEventListener("click", closeMoreActions);

    void nextTick(() => {
        setupScrollObserver();
    });
});

onBeforeUnmount(() => {
    window.removeEventListener("beforeunload", handleBeforeUnload);
    document.removeEventListener("click", closeMoreActions);
    cleanupScrollObserver();
});

watch(
    () => settings.value.account,
    () => {
        if (!accountDirty.value) {
            syncAccountForm();
        }
    },
    { deep: true, immediate: true },
);

// 表单内容变化时清除字段级校验错误
watch(
    accountForm,
    () => {
        if (Object.keys(accountFieldErrors.value).length) {
            accountFieldErrors.value = {};
        }
    },
    { deep: true },
);

onBeforeRouteLeave(() => {
    if (!settingsDirty.value) {
        return true;
    }

    return window.confirm("设置中心有未保存修改，确定离开吗？");
});





const saveAccountFamily = async () => {
    accountFieldErrors.value = {};
    if (!emailPattern.test(accountForm.email.trim())) {
        ElMessage.warning("请输入正确的邮箱");
        return;
    }

    savingAccount.value = true;

    try {
        settings.value.account.username = accountForm.name.trim();
        settings.value.account.email = accountForm.email.trim();
        settings.value.account.familyName = accountForm.householdName.trim();
        settings.value.account.householdAddress =
            accountForm.address.trim() || null;
        settings.value.account.householdTimezone = accountForm.timezone;
        await settingsStore.saveAccountHome();
        await settingsStore.saveSettings();
        syncAccountForm();
        syncPreferencesSnapshot();
        ElMessage.success("账户与家庭已保存");
    } catch (error) {
        // 将 422 字段校验错误定位到具体字段
        if (error instanceof ApiError && error.fieldErrors) {
            accountFieldErrors.value = error.fieldErrors;
            const firstMessage = Object.values(error.fieldErrors)[0];
            if (firstMessage) ElMessage.error(firstMessage);
        } else {
            ElMessage.error(getErrorMessage(error, "保存失败"));
        }
    } finally {
        savingAccount.value = false;
    }
};

const performSwitchHousehold = async (householdId: number) => {
    switchingHousehold.value = true;
    try {
        await householdStore.switchHousehold(householdId);
        settingsStore.applyHouseholdContext(
            householdStore.activeHousehold,
            householdStore.members,
        );
        syncAccountForm();
        const name = householdStore.activeHousehold?.name ?? "";
        ElMessage.success(`已切换到「${name}」`);
    } catch (error) {
        ElMessage.error(getErrorMessage(error, "家庭切换失败"));
    } finally {
        switchingHousehold.value = false;
    }
};

const switchHousehold = (householdId: number) => {
    // 有未保存的账户/家庭修改时先确认，避免切换家庭丢编辑
    if (accountDirty.value) {
        confirmRequest.value = {
            tone: "warning",
            title: "切换家庭",
            description: "切换家庭将丢弃当前未保存的账户与家庭修改。",
            confirmText: "继续切换",
            cancelText: "取消",
            warning: "未保存的修改将被丢弃，且无法恢复。",
            footerHint: "可先保存再切换",
            summary: {
                icon: "home",
                title: "切换活动家庭",
                description: "未保存的账户与家庭修改将被丢弃",
                color: "var(--color-warning)",
            },
            onConfirm: () => performSwitchHousehold(householdId),
        };
        return;
    }

    void performSwitchHousehold(householdId);
};

const createHousehold = async (payload: { name: string; address: string }) => {
    try {
        await settingsStore.createHousehold({
            name: payload.name,
            address: payload.address || null,
            timezone: accountForm.timezone,
        });
        syncAccountForm();
        ElMessage.success("家庭已创建并切换");
    } catch (error) {
        if (error instanceof ApiError && error.fieldErrors) {
            const firstMessage = Object.values(error.fieldErrors)[0];
            if (firstMessage) {
                ElMessage.error(firstMessage);
                return;
            }
        }
        ElMessage.error(getErrorMessage(error, "家庭创建失败"));
    }
};

const saveAllSettings = async () => {
    const tasks: Promise<void>[] = [];

    if (accountDirty.value) tasks.push(saveAccountFamily());
    if (integrationDirty.value || preferencesDirty.value) {
        tasks.push(
            (async () => {
                try {
                    if (integrationDirty.value) {
                        await settingsStore.saveAIModel();
                    }
                    if (preferencesDirty.value) {
                        await settingsStore.saveSettings();
                    }
                    syncIntegrationSnapshot();
                    syncPreferencesSnapshot();
                } catch (error) {
                    ElMessage.error(
                        getErrorMessage(error, "设置保存失败"),
                    );
                }
            })(),
        );
    }

    await Promise.all(tasks);
};

const uploadAvatar = async (file: File) => {
    savingAccount.value = true;

    try {
        await settingsStore.uploadAccountAvatar(file);
        accountForm.avatarUrl = settings.value.account.avatarUrl ?? null;
        initialAccountSnapshot.value = accountSnapshot.value;
        ElMessage.success("头像已上传");
    } catch (error) {
        ElMessage.error(
            getErrorMessage(error, "头像上传失败"),
        );
    } finally {
        savingAccount.value = false;
    }
};

const deleteAvatar = async () => {
    savingAccount.value = true;

    try {
        await settingsStore.deleteAccountAvatar();
        accountForm.avatarUrl = null;
        initialAccountSnapshot.value = accountSnapshot.value;
        ElMessage.success("头像已删除");
    } catch (error) {
        ElMessage.error(
            getErrorMessage(error, "头像删除失败"),
        );
    } finally {
        savingAccount.value = false;
    }
};

const addMember = async (email: string, role: HouseholdRole) => {
    if (!canManageMembers.value) {
        ElMessage.warning("普通成员只能查看成员列表");
        return;
    }

    addingMember.value = true;

    try {
        await settingsStore.addHouseholdMember(email, role);
        memberFieldErrors.value = {};
        ElMessage.success("成员已添加");
    } catch (error) {
        if (error instanceof ApiError && error.fieldErrors) {
            memberFieldErrors.value = error.fieldErrors;
            const firstMessage = Object.values(error.fieldErrors)[0];
            if (firstMessage) ElMessage.error(firstMessage);
        } else {
            ElMessage.error(getErrorMessage(error, "成员添加失败"));
        }
    } finally {
        addingMember.value = false;
    }
};

const clearMemberFieldErrors = () => {
    memberFieldErrors.value = {};
};

const performUpdateMemberRole = async (membershipId: number, role: HouseholdRole) => {
    loadingMemberId.value = membershipId;
    try {
        await settingsStore.updateMemberRole(membershipId, role);
        ElMessage.success("成员角色已更新");
    } catch (error) {
        ElMessage.error(getErrorMessage(error, "成员角色更新失败"));
    } finally {
        loadingMemberId.value = null;
    }
};

const updateMemberRole = (membershipId: number, role: HouseholdRole) => {
    const member = householdMembers.value.find(
        (item) => item.membershipId === membershipId,
    );

    if (!member) return;

    if (member.role === "admin" && role === "member" && adminCount.value <= 1) {
        ElMessage.error("家庭至少保留一名管理员");
        return;
    }

    // 高影响操作（管理员降级）二次确认
    if (member.role === "admin" && role === "member") {
        confirmRequest.value = {
            tone: "warning",
            title: "修改角色",
            description: `将 ${member.name} 的角色从管理员降为普通成员。`,
            confirmText: "确认降级",
            cancelText: "取消",
            warning: "降级后该成员将无法管理本家庭。",
            footerHint: "可在成员管理中改回",
            summary: {
                icon: "members",
                title: member.name,
                description: `管理员 → 普通成员`,
                color: "var(--color-warning)",
            },
            onConfirm: () => performUpdateMemberRole(membershipId, role),
        };
        return;
    }

    void performUpdateMemberRole(membershipId, role);
};

const performRemoveMember = async (membershipId: number) => {
    loadingMemberId.value = membershipId;
    try {
        await settingsStore.deleteHouseholdMember(membershipId);
        ElMessage.success("成员已移除");
    } catch (error) {
        ElMessage.error(getErrorMessage(error, "成员移除失败"));
    } finally {
        loadingMemberId.value = null;
    }
};

const removeMember = (membershipId: number) => {
    const member = householdMembers.value.find(
        (item) => item.membershipId === membershipId,
    );

    if (!member) return;

    if (membershipId === currentMemberId.value) {
        ElMessage.error("不能移除当前用户");
        return;
    }

    if (member.role === "admin") {
        ElMessage.error("只能移除普通成员");
        return;
    }

    confirmRequest.value = {
        tone: "danger",
        title: "移除成员",
        description: `移除后，${member.name} 将无法访问本家庭。`,
        confirmText: "移除",
        cancelText: "取消",
        warning: "移除后需重新邀请才能恢复访问。",
        footerHint: "此操作不可撤销",
        summary: {
            icon: "members",
            title: member.name,
            description: member.email,
            color: "var(--color-danger)",
        },
        onConfirm: () => performRemoveMember(membershipId),
    };
};
</script>

<template>
    <div
        class="app-page-layout m-0 min-w-0 border-0 p-0"
        :inert="!authStore.isAuthenticated"
    >
        <section
            class="settings-main page-enter flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] p-5 shadow-soft"
        >
            <header
                class="shrink-0 border-b border-[var(--color-divider)] pb-4 mb-4"
            >
                <div class="flex items-center gap-3">
                    <span
                        class="grid h-10 w-10 place-items-center rounded-xl text-[var(--color-info)] shadow-sm"
                        style="background: var(--color-info-soft)"
                    >
                        <SvgIcon name="settings" />
                    </span>
                    <div>
                        <h1
                            class="bg-gradient-to-r from-[var(--color-primary-700)] to-[var(--color-ai)] bg-clip-text text-2xl font-extrabold text-transparent"
                        >
                            设置中心
                        </h1>
                        <p
                            class="mt-1 text-sm font-medium text-[var(--color-text-tertiary)]"
                        >
                            管理账户、界面、AI 助手与平台接入配置
                        </p>
                    </div>
                </div>
            </header>

            <!-- 移动端横向吸顶标签 -->
            <nav class="settings-mobile-tabs" aria-label="设置分区导航">
                <button
                    v-for="tab in mobileSections"
                    :key="tab.id"
                    class="mobile-tab"
                    :class="{ 'is-active': activeSection === tab.id }"
                    type="button"
                    @click="selectSection(tab.id)"
                >
                    <span class="mobile-tab-label">{{ tab.label }}</span>
                </button>
            </nav>

            <div
                ref="scrollContainer"
                class="settings-scroll-area min-h-0 flex-1 overflow-y-auto pr-1"
            >
                <!-- 个人与家庭 -->
                <section class="settings-group">
                    <header class="settings-group-header">
                        <SvgIcon name="account" size="sm" />
                        个人与家庭
                    </header>
                    <div class="settings-group-grid">
                        <AccountFamilyCard
                            :active-household-id="householdStore.activeHouseholdId"
                            :dirty="accountDirty"
                            :field-errors="accountFieldErrors"
                            :form="accountForm"
                            :households="householdStore.households"
                            :loading="savingAccount"
                            :switching="switchingHousehold"
                            @create-household="createHousehold"
                            @delete-avatar="deleteAvatar"
                            @save="saveAccountFamily"
                            @switch-household="switchHousehold"
                            @update-form="Object.assign(accountForm, $event)"
                            @upload-avatar="uploadAvatar"
                        />
                        <MemberManagementCard
                            :admin-count="adminCount"
                            :can-manage="canManageMembers"
                            :current-member-id="currentMemberId"
                            :field-errors="memberFieldErrors"
                            :loading-member-id="loadingMemberId"
                            :members="members"
                            :submitting="addingMember"
                            @add-member="addMember"
                            @clear-field-errors="clearMemberFieldErrors"
                            @remove-member="removeMember"
                            @update-member-role="updateMemberRole"
                        />
                    </div>
                </section>

                <!-- 使用体验 -->
                <section class="settings-group">
                    <header class="settings-group-header">
                        <SvgIcon name="appearance" size="sm" />
                        使用体验
                    </header>
                    <div class="settings-group-grid">
                        <AppearanceSettingsCard :appearance="settings.appearance" />
                        <NotificationSettingsCard
                            :notifications="settings.notifications"
                        />
                    </div>
                </section>

                <!-- 智能服务 -->
                <section class="settings-group">
                    <header class="settings-group-header">
                        <SvgIcon name="ai" size="sm" />
                        智能服务
                    </header>
                    <div class="settings-group-grid">
                        <AiAssistantSettingsCard :ai="settings.aiAssistant" />
                        <HomeAssistantSettingsCard
                            :ai="settings.aiAssistant"
                            :home-assistant="settings.homeAssistant"
                        />
                    </div>
                </section>

                <!-- 安全与数据 -->
                <section class="settings-group">
                    <header class="settings-group-header">
                        <SvgIcon name="security" size="sm" />
                        安全与数据
                    </header>
                    <div class="settings-group-grid">
                        <SecuritySettingsCard :security="settings.security" />
                        <BackupSettingsCard
                            :backup="settings.backup"
                        />
                    </div>
                </section>
            </div>

            <footer class="settings-actions">
                <div class="settings-save-state">
                    <span class="settings-save-state-icon" aria-hidden="true">
                        <SvgIcon
                            :name="settingsDirty ? 'edit' : 'check-circle'"
                            size="sm"
                        />
                    </span>
                    <span>
                        <strong>{{ settingsDirty ? `${dirtyCount} 项更改尚未保存` : "所有设置均已保存" }}</strong>
                        <small>{{ settingsDirty ? "请及时保存以避免丢失" : "设置将同步到当前家庭账户" }}</small>
                    </span>
                </div>

                <Transition name="status-crossfade">
                    <span
                        v-if="settingsStore.saveStatus === 'saved'"
                        class="settings-saved-at"
                    >
                        <SvgIcon name="check-circle" size="sm" />
                        已保存 {{ settingsStore.savedAt }}
                    </span>
                </Transition>

                <div class="settings-action-buttons">
                    <div
                        ref="moreActionsRef"
                        class="settings-more-actions"
                    >
                        <button
                            class="more-actions-btn"
                            type="button"
                            @click="toggleMoreActions"
                        >
                            <SvgIcon name="settings" size="sm" />
                            <span class="more-actions-label">更多操作</span>
                            <SvgIcon
                                name="chevron-down"
                                size="sm"
                                class="more-actions-arrow"
                                :class="{ 'is-open': moreActionsOpen }"
                            />
                        </button>
                        <Transition name="status-crossfade">
                            <div
                                v-if="moreActionsOpen"
                                class="more-actions-menu"
                            >
                                <button
                                    class="more-actions-item is-danger"
                                    type="button"
                                    @click="confirmReset"
                                >
                                    <SvgIcon name="refresh" size="sm" />
                                    恢复默认设置
                                </button>
                            </div>
                        </Transition>
                    </div>
                    <button
                        class="settings-save-button"
                        :class="{ 'button-loading': savingAccount }"
                        :disabled="savingAccount || !settingsDirty"
                        type="button"
                        @click="saveAllSettings"
                    >
                        <SvgIcon :name="savingAccount ? 'refresh' : 'check-circle'" size="sm" />
                        {{ savingAccount ? "保存中" : "保存更改" }}
                    </button>
                </div>
            </footer>
        </section>

        <BaseCollapsibleRail
            title="设置导航"
            subtitle="快速定位与配置状态"
            storage-key="orion.settings-rail-collapsed"
        >
            <template #collapsed>
                <SettingsDirectory
                    :active="activeSection"
                    compact
                    @select="selectSection"
                />
            </template>

            <template #default>
                <div class="settings-rail-card-list">
                    <SettingsDirectory
                        :active="activeSection"
                        :total-items="8"
                        :completed-items="completedConfigCount"
                        @select="selectSection"
                    />
                    <ConfigHealthCard
                        :security="settings.security"
                        :backup="settings.backup"
                        :notifications="settings.notifications"
                        :account-status="settings.summary.accountStatus"
                        :home-assistant-connected="settings.summary.homeAssistantStatus === 'online'"
                        @navigate="selectSection"
                    />
                    <SettingsSummaryPanel
                        :summary="settings.summary"
                        :member-count="householdMembers.length"
                    />
                    <SettingsSuggestionPanel
                        :suggestions="settings.suggestions"
                        @select="selectSection"
                    />
                </div>
            </template>
        </BaseCollapsibleRail>

        <ConfirmActionDialog
            v-if="confirmRequest"
            :model-value="true"
            :tone="confirmRequest.tone"
            :title="confirmRequest.title"
            :description="confirmRequest.description"
            :confirm-text="confirmRequest.confirmText"
            :cancel-text="confirmRequest.cancelText"
            :loading="confirmLoading"
            :warning="confirmRequest.warning"
            :footer-hint="confirmRequest.footerHint"
            @confirm="runConfirm"
            @update:model-value="!$event && (confirmRequest = null)"
        >
            <ConfirmEntitySummary
                v-if="confirmRequest.summary"
                :icon="confirmRequest.summary.icon"
                :title="confirmRequest.summary.title"
                :description="confirmRequest.summary.description"
                :color="confirmRequest.summary.color"
            />
        </ConfirmActionDialog>
    </div>
</template>

<style scoped>
/* === 右侧导航卡片列表 === */
.settings-rail-card-list {
    display: grid;
    gap: 16px;
    padding: 12px;
}

/* === 左栏滚动区 === */
.settings-scroll-area {
    container-name: settings-content;
    container-type: inline-size;
    contain: layout paint;
    overscroll-behavior: contain;
    scroll-behavior: smooth;
    scrollbar-gutter: stable;
}

/* === 设置分组 === */
.settings-group + .settings-group {
    margin-top: 20px;
}

.settings-group-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.settings-group-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: stretch;
    gap: 14px;
    padding: 1px 2px 4px;
}

.settings-group-grid > :deep(.settings-section) {
    height: 100%;
}

/* === 底部操作栏 === */
.settings-actions {
    position: relative;
    z-index: 5;
    display: flex;
    min-height: 72px;
    flex: 0 0 auto;
    align-items: center;
    gap: 18px;
    margin-top: 14px;
    border: 1px solid var(--color-border-default);
    border-radius: 14px;
    background: linear-gradient(
        135deg,
        var(--color-panel-background),
        var(--color-primary-50)
    );
    padding: 12px 14px;
    box-shadow: var(--shadow-card);
}

.settings-save-state {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 10px;
}

.settings-save-state-icon {
    display: grid;
    width: 38px;
    height: 38px;
    flex: 0 0 38px;
    place-items: center;
    border-radius: 11px;
    background: var(--color-primary-100);
    color: var(--color-primary-700);
}

.settings-save-state > span:last-child {
    display: grid;
    gap: 2px;
}

.settings-save-state strong {
    color: var(--color-text-primary);
    font-size: 13px;
    font-weight: 900;
}

.settings-save-state small {
    color: var(--color-text-tertiary);
    font-size: 11px;
    font-weight: 700;
}

.settings-saved-at {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-left: auto;
    color: var(--color-success);
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
}

.settings-action-buttons {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-left: auto;
}

.settings-save-button {
    display: inline-flex;
    min-width: 124px;
    height: 40px;
    align-items: center;
    justify-content: center;
    gap: 7px;
    border-radius: 10px;
    padding: 0 16px;
    font-size: 13px;
    font-weight: 900;
    transition:
        transform 160ms var(--motion-ease),
        border-color 160ms var(--motion-ease),
        background-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease);
}

.settings-save-button {
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    box-shadow: 0 6px 14px var(--color-focus-ring);
}

.settings-save-button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px var(--color-focus-ring);
}

.settings-save-button:disabled {
    border-color: var(--color-border-default);
    background: var(--color-surface-subtle);
    color: var(--color-text-tertiary);
    box-shadow: none;
    cursor: not-allowed;
}

.settings-save-button.button-loading svg {
    animation: settings-save-spin 800ms linear infinite;
}

@keyframes settings-save-spin {
    to {
        transform: rotate(360deg);
    }
}

/* === 更多操作下拉菜单 === */
.settings-more-actions {
    position: relative;
}

.more-actions-btn {
    display: inline-flex;
    height: 40px;
    align-items: center;
    gap: 6px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    padding: 0 14px;
    font-size: 13px;
    font-weight: 800;
    color: var(--color-text-secondary);
    background: var(--color-panel-background);
    transition:
        border-color 160ms ease,
        background-color 160ms ease,
        color 160ms ease;
    white-space: nowrap;
}

.more-actions-btn:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
}

.more-actions-arrow {
    transition: transform 200ms var(--motion-ease);
}

.more-actions-arrow.is-open {
    transform: rotate(180deg);
}

.more-actions-label {
    display: inline;
}

.more-actions-menu {
    position: absolute;
    right: 0;
    bottom: calc(100% + 8px);
    z-index: 20;
    min-width: 180px;
    border: 1px solid var(--color-border-default);
    border-radius: 10px;
    background: var(--color-card-bg);
    padding: 6px;
    box-shadow: 0 8px 24px rgb(15 23 42 / 12%);
    transform-origin: bottom right;
}

.more-actions-item {
    display: flex;
    width: 100%;
    align-items: center;
    gap: 8px;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-text-secondary);
    transition:
        background-color 150ms ease,
        color 150ms ease;
}

.more-actions-item:hover {
    background: var(--color-surface-hover);
    color: var(--color-text-primary);
}

.more-actions-item.is-danger {
    color: var(--color-danger);
}

.more-actions-item.is-danger:hover {
    background: var(--color-danger-soft);
    color: var(--color-danger);
}

@media (min-width: 1024px) {
    .app-page-layout {
        grid-template-columns: minmax(0, 1fr) auto;
    }
}

/* === 移动端吸顶标签（桌面端隐藏） === */
.settings-mobile-tabs {
    display: none;
}

/* === 响应式 === */
@media (max-width: 1180px) {
    .settings-save-state small {
        display: none;
    }

    .settings-save-button {
        min-width: auto;
    }

    .more-actions-label {
        display: none;
    }

    .more-actions-btn {
        padding: 0 10px;
    }
}

@container settings-content (max-width: 680px) {
    .settings-group-grid {
        grid-template-columns: minmax(0, 1fr);
    }
}

@media (max-width: 1023px) {
    .base-collapsible-rail {
        display: none;
    }

    .settings-mobile-tabs {
        display: flex;
        gap: 4px;
        margin-bottom: 14px;
        padding-bottom: 10px;
        overflow-x: auto;
        overscroll-behavior: contain;
        scrollbar-width: none;
        position: sticky;
        top: 0;
        z-index: 3;
        background: var(--color-workspace-background);
        border-bottom: 1px solid var(--color-divider);
    }

    .settings-mobile-tabs::-webkit-scrollbar {
        display: none;
    }

    .mobile-tab {
        flex: 0 0 auto;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        color: var(--color-text-tertiary);
        white-space: nowrap;
        transition:
            background-color 150ms ease,
            color 150ms ease;
    }

    .mobile-tab:hover {
        background: var(--color-surface-hover);
        color: var(--color-text-primary);
    }

    .mobile-tab.is-active {
        background: var(--color-primary-50);
        color: var(--color-primary-700);
    }
}

@media (max-width: 767px) {
    .settings-main {
        padding: 12px;
    }

    .settings-group-grid {
        grid-template-columns: minmax(0, 1fr);
    }

    .settings-actions {
        width: 100%;
        align-items: stretch;
        flex-direction: column;
        flex-wrap: wrap;
    }

    .settings-saved-at,
    .settings-action-buttons {
        margin-left: 0;
    }

    .settings-action-buttons > button {
        flex: 1 1 0;
    }
}

@media (prefers-reduced-motion: reduce) {
    .settings-save-button {
        transition-duration: 1ms;
    }

    .settings-save-button:hover:not(:disabled) {
        transform: none;
    }

    .settings-save-button.button-loading svg {
        animation: none;
    }
}
</style>
