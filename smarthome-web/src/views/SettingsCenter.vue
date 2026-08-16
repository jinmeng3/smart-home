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
import { ElMessage, ElMessageBox } from "element-plus";
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
import { useAuthStore } from "../stores/auth";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { getErrorMessage } from "../utils/error";
import { settingsSections, sectionIds } from "../constants/settingsSections";
import type { AccountForm, FamilyMember, HouseholdRole } from "../types/settings";
import type { SettingsSectionId } from "../types/settings";

const settingsStore = useSettingsStore();
const authStore = useAuthStore();

const activeSection = ref<SettingsSectionId>("account");
const savingAccount = ref(false);
const addingMember = ref(false);
const loadingMemberId = ref<number | null>(null);
const initialAccountSnapshot = ref<string>();
const initialIntegrationSnapshot = ref<string>();
const initialPreferencesSnapshot = ref<string>();

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
const confirmReset = async () => {
    try {
        await ElMessageBox.confirm(
            "此操作将重置以下设置为出厂默认值：<br><br>" +
                "• 界面外观（主题、语言、时区）<br>" +
                "• 智能助手配置（模型参数、自动执行规则）<br>" +
                "• Home Assistant 接入凭证将清空<br>" +
                "• 通知与安全偏好<br><br>" +
                "<strong>账户与家庭信息不受影响。</strong>",
            "恢复默认设置",
            {
                confirmButtonText: "确认恢复",
                cancelButtonText: "取消",
                type: "warning",
                dangerouslyUseHTMLString: true,
                confirmButtonClass: "el-button--danger",
            },
        );
        settingsStore.resetSettings();
        syncAccountForm();
        syncIntegrationSnapshot();
        syncPreferencesSnapshot();
        ElMessage.success("已恢复默认设置");
    } catch {
        // 用户取消
    } finally {
        moreActionsOpen.value = false;
    }
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
const canManageMembers = computed(() => currentMemberRole.value === "admin");

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

onBeforeRouteLeave(() => {
    if (!settingsDirty.value) {
        return true;
    }

    return window.confirm("设置中心有未保存修改，确定离开吗？");
});





const saveAccountFamily = async () => {
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
        ElMessage.error(getErrorMessage(error, "保存失败"));
    } finally {
        savingAccount.value = false;
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

const syncDevices = async () => {
    try {
        await settingsStore.syncDevices();
        ElMessage.success("设备同步完成");
    } catch (error) {
        ElMessage.error(
            getErrorMessage(error, "WebSocket 状态刷新失败"),
        );
    }
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
        ElMessage.success("成员已添加");
    } catch (error) {
        ElMessage.error(
            getErrorMessage(error, "成员添加失败"),
        );
    } finally {
        addingMember.value = false;
    }
};

const updateMemberRole = async (membershipId: number, role: HouseholdRole) => {
    const member = householdMembers.value.find(
        (item) => item.membershipId === membershipId,
    );

    if (!member) {
        return;
    }

    if (member.role === "admin" && role === "member" && adminCount.value <= 1) {
        ElMessage.error("家庭至少保留一名管理员");
        return;
    }

    loadingMemberId.value = membershipId;

    try {
        await settingsStore.updateMemberRole(membershipId, role);
        ElMessage.success("成员角色已更新");
    } catch (error) {
        ElMessage.error(
            getErrorMessage(error, "成员角色更新失败"),
        );
    } finally {
        loadingMemberId.value = null;
    }
};

const removeMember = async (membershipId: number) => {
    const member = householdMembers.value.find(
        (item) => item.membershipId === membershipId,
    );

    if (!member) {
        return;
    }

    if (membershipId === currentMemberId.value) {
        ElMessage.error("不能移除当前用户");
        return;
    }

    if (member.role === "admin") {
        ElMessage.error("只能移除普通成员");
        return;
    }

    try {
        await ElMessageBox.confirm(`确认移除 ${member.name}？`, "移除成员", {
            confirmButtonText: "移除",
            cancelButtonText: "取消",
            type: "warning",
        });
    } catch {
        return;
    }

    loadingMemberId.value = membershipId;

    try {
        await settingsStore.deleteHouseholdMember(membershipId);
        ElMessage.success("成员已移除");
    } catch (error) {
        ElMessage.error(
            getErrorMessage(error, "成员移除失败"),
        );
    } finally {
        loadingMemberId.value = null;
    }
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
                            :dirty="accountDirty"
                            :form="accountForm"
                            :loading="savingAccount"
                            @delete-avatar="deleteAvatar"
                            @save="saveAccountFamily"
                            @update-form="Object.assign(accountForm, $event)"
                            @upload-avatar="uploadAvatar"
                        />
                        <MemberManagementCard
                            :admin-count="adminCount"
                            :can-manage="canManageMembers"
                            :current-member-id="currentMemberId"
                            :loading-member-id="loadingMemberId"
                            :members="members"
                            :submitting="addingMember"
                            @add-member="addMember"
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
                            @sync="syncDevices"
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
            </template>
        </BaseCollapsibleRail>
    </div>
</template>

<style scoped>
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
