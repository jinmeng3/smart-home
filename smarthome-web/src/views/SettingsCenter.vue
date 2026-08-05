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
import SecurityStatusPanel from "../components/settings/SecurityStatusPanel.vue";
import SettingsSuggestionPanel from "../components/settings/SettingsSuggestionPanel.vue";
import SettingsSummaryPanel from "../components/settings/SettingsSummaryPanel.vue";
import SvgIcon from "../components/common/SvgIcon.vue";
import { useSettingsStore } from "../stores/settings";
import { useAuthStore } from "../stores/auth";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import type { AccountForm, FamilyMember, HouseholdRole } from "../types/settings";
import type { SettingsSectionId, SettingsState } from "../types/settings";

const settingsStore = useSettingsStore();
const authStore = useAuthStore();

const activeSection = ref<SettingsSectionId>("account");
const savingAccount = ref(false);
const addingMember = ref(false);
const loadingMemberId = ref<number | null>(null);
const initialAccountSnapshot = ref("");
const initialIntegrationSnapshot = ref("");

// 滚动监听
const scrollContainer = ref<HTMLElement | null>(null);
const sectionObservers = new Map<string, IntersectionObserver>();

const setupScrollObserver = () => {
    if (!scrollContainer.value) return;

    const sections = [
        "account",
        "appearance",
        "ai",
        "homeAssistant",
        "notifications",
        "security",
        "backup",
    ];

    sections.forEach((sectionId) => {
        const sectionElement = document.getElementById(sectionId);
        if (!sectionElement) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        activeSection.value = sectionId as SettingsSectionId;
                    }
                });
            },
            {
                root: scrollContainer.value,
                rootMargin: "-50% 0px -50% 0px",
                threshold: 0,
            }
        );

        observer.observe(sectionElement);
        sectionObservers.set(sectionId, observer);
    });
};

const cleanupScrollObserver = () => {
    sectionObservers.forEach((observer, sectionId) => {
        const element = document.getElementById(sectionId);
        if (element) {
            observer.unobserve(element);
        }
    });
    sectionObservers.clear();
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
    () => accountSnapshot.value !== initialAccountSnapshot.value,
);
const integrationSnapshot = computed(() =>
    JSON.stringify({
        aiAssistant: settings.value.aiAssistant,
        homeAssistant: settings.value.homeAssistant,
    }),
);
const integrationDirty = computed(
    () => integrationSnapshot.value !== initialIntegrationSnapshot.value,
);
const settingsDirty = computed(
    () => accountDirty.value || integrationDirty.value,
);
const householdMembers = computed(() => settings.value.account.members ?? []);
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

const selectSection = (section: SettingsSectionId) => {
    activeSection.value = section;
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

onMounted(() => {
    if (!authStore.isAuthenticated) {
        syncAccountForm();
        syncIntegrationSnapshot();
        authStore.openLogin();
        window.addEventListener("beforeunload", handleBeforeUnload);
        return;
    }

    void settingsStore
        .loadAccountHome()
        .then(syncAccountForm)
        .catch((error: unknown) => {
            ElMessage.error(
                error instanceof Error
                    ? error.message
                    : "账户与家庭信息加载失败",
            );
        });
    void settingsStore
        .loadAIModel()
        .then(syncIntegrationSnapshot)
        .catch((error: unknown) => {
            ElMessage.error(
                error instanceof Error ? error.message : "AI 模型配置加载失败",
            );
        });
    window.addEventListener("beforeunload", handleBeforeUnload);

    void nextTick(() => {
        setupScrollObserver();
    });
});

onBeforeUnmount(() => {
    window.removeEventListener("beforeunload", handleBeforeUnload);
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

    return window.confirm("账户与家庭信息有未保存修改，确定离开吗？");
});

const exportSettings = () => {
    const blob = new Blob(
        [JSON.stringify(settingsStore.getExportSettings(), null, 2)],
        { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `smart-home-settings-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    settingsStore.updateBackupTime();
    ElMessage.success("配置已导出");
};

const importSettings = (nextSettings: SettingsState) => {
    settingsStore.importSettings(nextSettings);
};

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
        settingsStore.saveSettings();
        syncAccountForm();
        ElMessage.success("账户与家庭已保存");
    } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : "保存失败");
    } finally {
        savingAccount.value = false;
    }
};

const saveAllSettings = async () => {
    await saveAccountFamily();

    try {
        await settingsStore.saveAIModel();
        settingsStore.saveSettings();
        syncIntegrationSnapshot();
    } catch (error) {
        ElMessage.error(
            error instanceof Error ? error.message : "AI 助手配置保存失败",
        );
    }
};

const syncDevices = async () => {
    try {
        await settingsStore.syncDevices();
        ElMessage.success("设备同步完成");
    } catch (error) {
        ElMessage.error(
            error instanceof Error ? error.message : "WebSocket 状态刷新失败",
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
            error instanceof Error ? error.message : "头像上传失败",
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
            error instanceof Error ? error.message : "头像删除失败",
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
            error instanceof Error ? error.message : "成员添加失败",
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
            error instanceof Error ? error.message : "成员角色更新失败",
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
            error instanceof Error ? error.message : "成员移除失败",
        );
    } finally {
        loadingMemberId.value = null;
    }
};
</script>

<template>
    <fieldset
        class="app-page-layout m-0 min-w-0 border-0 p-0"
        :disabled="!authStore.isAuthenticated"
    >
        <section
            class="page-enter flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] p-5 shadow-soft"
        >
            <header
                class="mb-4 shrink-0 border-b border-[var(--color-divider)] pb-4"
            >
                <div class="flex items-center gap-3">
                    <span
                        class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-[var(--color-primary-600)] to-[var(--color-ai)] text-white shadow-sm"
                    >
                        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <circle cx="12" cy="12" r="3"></circle>
                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                        </svg>
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

            <div
                ref="scrollContainer"
                class="settings-scroll-area min-h-0 flex-1 overflow-y-auto pr-1"
            >
                <div class="settings-card-grid card-grid-enter grid grid-cols-2 gap-4">
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
                    <AppearanceSettingsCard :appearance="settings.appearance" />
                    <AiAssistantSettingsCard :ai="settings.aiAssistant" />
                    <HomeAssistantSettingsCard
                        :ai="settings.aiAssistant"
                        :home-assistant="settings.homeAssistant"
                        @sync="syncDevices"
                    />
                    <NotificationSettingsCard
                        :notifications="settings.notifications"
                    />
                    <SecuritySettingsCard :security="settings.security" />
                    <BackupSettingsCard
                        :backup="settings.backup"
                        @export="exportSettings"
                        @import="importSettings"
                    />
                </div>
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
                        <strong>{{ settingsDirty ? "有尚未保存的更改" : "所有设置均已保存" }}</strong>
                        <small>设置将同步到当前家庭账户</small>
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
                    <button
                        class="settings-reset-button"
                        type="button"
                        @click="settingsStore.resetSettings"
                    >
                        <SvgIcon name="refresh" size="sm" />
                        恢复默认
                    </button>
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

        <aside
            class="page-enter flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto border-l border-[var(--color-border-default)] bg-[var(--color-sidebar-background)] pl-2 pr-1"
            style="animation-delay: 70ms"
        >
            <SettingsSummaryPanel :summary="settings.summary" />
            <SecurityStatusPanel
                :backup="settings.backup"
                :notifications="settings.notifications"
                :security="settings.security"
            />
            <SettingsSuggestionPanel
                :suggestions="settings.suggestions"
                @select="selectSection"
            />
        </aside>
    </fieldset>
</template>

<style scoped>
.settings-scroll-area {
    contain: layout paint;
    overscroll-behavior: contain;
    scroll-behavior: smooth;
    scrollbar-gutter: stable;
}

.settings-actions {
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

.settings-reset-button,
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

.settings-reset-button {
    border: 1px solid var(--color-border-default);
    background: var(--color-panel-background);
    color: var(--color-text-secondary);
}

.settings-save-button {
    border: 1px solid var(--color-primary-600);
    background: var(--color-primary-600);
    color: var(--color-text-on-primary);
    box-shadow: 0 6px 14px var(--color-focus-ring);
}

.settings-reset-button:hover {
    border-color: var(--color-primary-200);
    background: var(--color-primary-50);
    color: var(--color-primary-700);
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

@media (max-width: 1180px) {
    .settings-save-state small {
        display: none;
    }

    .settings-reset-button,
    .settings-save-button {
        min-width: auto;
    }
}

@media (prefers-reduced-motion: reduce) {
    .settings-reset-button,
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
