<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import AccountFamilyCard from '../components/settings/AccountFamilyCard.vue'
import AiAssistantSettingsCard from '../components/settings/AiAssistantSettingsCard.vue'
import AppearanceSettingsCard from '../components/settings/AppearanceSettingsCard.vue'
import BackupSettingsCard from '../components/settings/BackupSettingsCard.vue'
import HomeAssistantSettingsCard from '../components/settings/HomeAssistantSettingsCard.vue'
import MemberManagementCard from '../components/settings/MemberManagementCard.vue'
import NotificationSettingsCard from '../components/settings/NotificationSettingsCard.vue'
import SecuritySettingsCard from '../components/settings/SecuritySettingsCard.vue'
import SecurityStatusPanel from '../components/settings/SecurityStatusPanel.vue'
import SettingsSuggestionPanel from '../components/settings/SettingsSuggestionPanel.vue'
import SettingsSummaryPanel from '../components/settings/SettingsSummaryPanel.vue'
import SettingsTabs from '../components/settings/SettingsTabs.vue'
import { useSettingsStore } from '../stores/settings'
import type { AccountForm, FamilyMember, MemberRole } from '../types/account'
import type { SettingsSectionId, SettingsState } from '../types/settings'

const settingsStore = useSettingsStore()
const activeSection = ref<SettingsSectionId>('account')
const savingAccount = ref(false)
const addingMember = ref(false)
const loadingMemberId = ref<number | null>(null)
const initialAccountSnapshot = ref('')
const initialIntegrationSnapshot = ref('')

const settings = computed(() => settingsStore.settings)
const accountForm = reactive<AccountForm>({
  name: '',
  email: '',
  avatarUrl: null,
  householdName: '',
  address: '',
  timezone: 'Asia/Shanghai',
})
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const accountSnapshot = computed(() => JSON.stringify(accountForm))
const accountDirty = computed(() => accountSnapshot.value !== initialAccountSnapshot.value)
const integrationSnapshot = computed(() =>
  JSON.stringify({
    aiAssistant: settings.value.aiAssistant,
    homeAssistant: settings.value.homeAssistant,
  }),
)
const integrationDirty = computed(() => integrationSnapshot.value !== initialIntegrationSnapshot.value)
const settingsDirty = computed(() => accountDirty.value || integrationDirty.value)
const householdMembers = computed(() => settings.value.account.members ?? [])
const members = computed<FamilyMember[]>(() =>
  householdMembers.value.map((member) => ({
    id: member.membershipId,
    name: member.name,
    email: member.email,
    avatarUrl: member.avatarUrl,
    role: member.role,
  })),
)
const currentMemberId = computed(() => {
  const accountId = settings.value.account.id

  if (!accountId) {
    return null
  }

  return householdMembers.value.find((member) => member.userId === accountId)?.membershipId ?? null
})
const currentMemberRole = computed(() => householdMembers.value.find((member) => member.membershipId === currentMemberId.value)?.role)
const adminCount = computed(() => householdMembers.value.filter((member) => member.role === 'admin').length)
const canManageMembers = computed(() => currentMemberRole.value === 'admin')

const syncAccountForm = () => {
  accountForm.name = settings.value.account.username
  accountForm.email = settings.value.account.email
  accountForm.avatarUrl = settings.value.account.avatarUrl ?? null
  accountForm.householdName = settings.value.account.familyName
  accountForm.address = settings.value.account.householdAddress ?? ''
  accountForm.timezone = settings.value.account.householdTimezone ?? 'Asia/Shanghai'
  initialAccountSnapshot.value = accountSnapshot.value
}

const syncIntegrationSnapshot = () => {
  initialIntegrationSnapshot.value = integrationSnapshot.value
}

const selectSection = (section: SettingsSectionId) => {
  activeSection.value = section
  document.getElementById(section)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const handleBeforeUnload = (event: BeforeUnloadEvent) => {
  if (!settingsDirty.value) {
    return
  }

  event.preventDefault()
  event.returnValue = ''
}

onMounted(() => {
  void settingsStore.loadAccountHome()
  void settingsStore.loadAIModel().then(syncIntegrationSnapshot)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

watch(
  () => settings.value.account,
  () => {
    if (!accountDirty.value) {
      syncAccountForm()
    }
  },
  { deep: true, immediate: true },
)

onBeforeRouteLeave(() => {
  if (!settingsDirty.value) {
    return true
  }

  return window.confirm('账户与家庭信息有未保存修改，确定离开吗？')
})

const exportSettings = () => {
  const blob = new Blob([JSON.stringify(settings.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `smart-home-settings-${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)
  settingsStore.updateBackupTime()
  ElMessage.success('配置已导出')
}

const importSettings = (nextSettings: SettingsState) => {
  settingsStore.importSettings(nextSettings)
}

const saveAccountFamily = async () => {
  if (!emailPattern.test(accountForm.email.trim())) {
    ElMessage.warning('请输入正确的邮箱')
    return
  }

  savingAccount.value = true

  try {
    settings.value.account.username = accountForm.name.trim()
    settings.value.account.email = accountForm.email.trim()
    settings.value.account.familyName = accountForm.householdName.trim()
    settings.value.account.householdAddress = accountForm.address.trim() || null
    settings.value.account.householdTimezone = accountForm.timezone
    await settingsStore.saveAccountHome()
    settingsStore.saveSettings()
    syncAccountForm()
    ElMessage.success('账户与家庭已保存')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败')
  } finally {
    savingAccount.value = false
  }
}

const saveAllSettings = async () => {
  await saveAccountFamily()

  try {
    await settingsStore.saveAIModel()
    settingsStore.saveSettings()
    syncIntegrationSnapshot()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : 'AI 鍔╂墜閰嶇疆淇濆瓨澶辫触')
  }
}

const syncDevices = async () => {
  try {
    await settingsStore.syncDevices()
    ElMessage.success('设备同步完成')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : 'WebSocket 状态刷新失败')
  }
}

const uploadAvatar = async (file: File) => {
  savingAccount.value = true

  try {
    await settingsStore.uploadAccountAvatar(file)
    accountForm.avatarUrl = settings.value.account.avatarUrl ?? null
    initialAccountSnapshot.value = accountSnapshot.value
    ElMessage.success('头像已上传')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '头像上传失败')
  } finally {
    savingAccount.value = false
  }
}

const deleteAvatar = async () => {
  savingAccount.value = true

  try {
    await settingsStore.deleteAccountAvatar()
    accountForm.avatarUrl = null
    initialAccountSnapshot.value = accountSnapshot.value
    ElMessage.success('头像已删除')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '头像删除失败')
  } finally {
    savingAccount.value = false
  }
}

const addMember = async (email: string, role: MemberRole) => {
  if (!canManageMembers.value) {
    ElMessage.warning('普通成员只能查看成员列表')
    return
  }

  addingMember.value = true

  try {
    await settingsStore.addHouseholdMember(email, role)
    ElMessage.success('成员已添加')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '成员添加失败')
  } finally {
    addingMember.value = false
  }
}

const updateMemberRole = async (membershipId: number, role: MemberRole) => {
  const member = householdMembers.value.find((item) => item.membershipId === membershipId)

  if (!member) {
    return
  }

  if (member.role === 'admin' && role === 'member' && adminCount.value <= 1) {
    ElMessage.error('家庭至少保留一名管理员')
    return
  }

  loadingMemberId.value = membershipId

  try {
    await settingsStore.updateMemberRole(membershipId, role)
    ElMessage.success('成员角色已更新')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '成员角色更新失败')
  } finally {
    loadingMemberId.value = null
  }
}

const removeMember = async (membershipId: number) => {
  const member = householdMembers.value.find((item) => item.membershipId === membershipId)

  if (!member) {
    return
  }

  if (membershipId === currentMemberId.value) {
    ElMessage.error('不能移除当前用户')
    return
  }

  if (member.role === 'admin') {
    ElMessage.error('只能移除普通成员')
    return
  }

  try {
    await ElMessageBox.confirm(`确认移除 ${member.name}？`, '移除成员', {
      confirmButtonText: '移除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  loadingMemberId.value = membershipId

  try {
    await settingsStore.deleteHouseholdMember(membershipId)
    ElMessage.success('成员已移除')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '成员移除失败')
  } finally {
    loadingMemberId.value = null
  }
}
</script>

<template>
  <div class="contents">
    <section class="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] p-5 shadow-soft">
      <header class="mb-4 shrink-0 border-b border-[var(--color-divider)] pb-4">
        <h1 class="text-2xl font-extrabold">设置中心</h1>
        <p class="mt-1 text-sm font-medium text-[var(--color-text-tertiary)]">管理账户、界面、AI 助手与平台接入配置</p>
      </header>

      <SettingsTabs :active-section="activeSection" @select="selectSection" />

      <div class="mt-4 min-h-0 flex-1 overflow-y-auto pr-1">
        <div class="grid grid-cols-2 gap-4">
          <AccountFamilyCard :dirty="accountDirty" :form="accountForm" :loading="savingAccount" @delete-avatar="deleteAvatar" @save="saveAccountFamily" @update-form="Object.assign(accountForm, $event)" @upload-avatar="uploadAvatar" />
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
          <HomeAssistantSettingsCard :home-assistant="settings.homeAssistant" @sync="syncDevices" />
          <NotificationSettingsCard :notifications="settings.notifications" />
          <SecuritySettingsCard :security="settings.security" />
          <BackupSettingsCard :backup="settings.backup" @export="exportSettings" @import="importSettings" />
        </div>
      </div>

      <footer class="mt-4 flex shrink-0 items-center gap-4 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-3">
        <button class="primary-button" :disabled="savingAccount || !settingsDirty" type="button" @click="saveAllSettings">
          {{ savingAccount ? '保存中' : '保存更改' }}
        </button>
        <button class="secondary-button min-w-[140px]" type="button" @click="settingsStore.resetSettings">恢复默认</button>
        <Transition name="status-crossfade">
          <span v-if="settingsStore.saveStatus === 'saved'" class="text-sm font-semibold text-[var(--color-success)]">已保存 {{ settingsStore.savedAt }}</span>
        </Transition>
      </footer>
    </section>

    <aside class="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto border-l border-[var(--color-border-default)] bg-[var(--color-sidebar-background)] pl-2 pr-1">
      <SettingsSummaryPanel :summary="settings.summary" />
      <SecurityStatusPanel :backup="settings.backup" :notifications="settings.notifications" :security="settings.security" />
      <SettingsSuggestionPanel :suggestions="settings.suggestions" @select="selectSection" />
    </aside>
  </div>
</template>
