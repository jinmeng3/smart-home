import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { ElMessage } from 'element-plus'
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
} from '../api/account'
import { defaultSettings } from '../mock/settings'
import type { HouseholdRole, SettingsState } from '../types/settings'

const storageKey = 'smart-home-settings'

const cloneSettings = (): SettingsState => structuredClone(defaultSettings)

const mergeNonAccountSettings = (nextSettings: Partial<SettingsState>): SettingsState => {
  const baseSettings = cloneSettings()

  return {
    ...baseSettings,
    ...nextSettings,
    account: baseSettings.account,
    summary: {
      ...baseSettings.summary,
      ...nextSettings.summary,
    },
  }
}

const loadSettings = (): SettingsState => {
  const savedSettings = window.localStorage.getItem(storageKey)

  if (!savedSettings) {
    return cloneSettings()
  }

  try {
    return mergeNonAccountSettings(JSON.parse(savedSettings))
  } catch {
    return cloneSettings()
  }
}

const isAdminRole = (role: string | undefined) => role?.toLowerCase() === 'admin'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<SettingsState>(loadSettings())
  const savedAt = ref<string | null>(null)
  const saveStatus = ref<'idle' | 'saved'>('idle')
  const loading = ref(false)

  watch(
    settings,
    (currentSettings) => {
      window.localStorage.setItem(storageKey, JSON.stringify(mergeNonAccountSettings(currentSettings)))
    },
    { deep: true },
  )

  const saveSettings = () => {
    savedAt.value = new Intl.DateTimeFormat('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(new Date())
    saveStatus.value = 'saved'

    window.setTimeout(() => {
      saveStatus.value = 'idle'
    }, 1600)
  }

  const loadAccountHome = async () => {
    loading.value = true

    try {
      const account = await getAccount()
      settings.value.account = {
        ...settings.value.account,
        id: account.id,
        username: account.name,
        email: account.email,
        avatarUrl: account.avatar_url,
      }

      const households = await listHouseholds()
      const household = households[0]
      const members = household ? await listMembers(household.id) : []

      const role = isAdminRole(household?.role) ? '管理员' : '成员'

      settings.value.account = {
        ...settings.value.account,
        familyName: household?.name ?? '',
        householdId: household?.id,
        householdAddress: household?.address ?? null,
        householdTimezone: household?.timezone ?? 'Asia/Shanghai',
        role,
        members,
      }
      settings.value.summary.currentHome = household?.name ?? ''
      settings.value.summary.accountStatus = role
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '账户与家庭信息加载失败')
    } finally {
      loading.value = false
    }
  }

  const saveAccountHome = async () => {
    const householdId = settings.value.account.householdId

    await updateAccount({
      name: settings.value.account.username,
      email: settings.value.account.email,
    })

    if (householdId) {
      await updateHousehold(householdId, {
        name: settings.value.account.familyName,
        address: settings.value.account.householdAddress,
        timezone: settings.value.account.householdTimezone,
      })
    }

    await loadAccountHome()
  }

  const uploadAccountAvatar = async (file: File) => {
    const response = await apiUploadAvatar(file)
    settings.value.account.avatarUrl = response.avatar_url
  }

  const deleteAccountAvatar = async () => {
    await apiDeleteAvatar()
    settings.value.account.avatarUrl = null
  }

  const addHouseholdMember = async (email: string, role: HouseholdRole) => {
    const householdId = settings.value.account.householdId

    if (!householdId) {
      return
    }

    await apiAddMember(householdId, { email, role })
    settings.value.account.members = await listMembers(householdId)
  }

  const updateMemberRole = async (membershipId: number, role: HouseholdRole) => {
    const householdId = settings.value.account.householdId

    if (!householdId) {
      return
    }

    await apiUpdateMemberRole(householdId, membershipId, role)
    settings.value.account.members = await listMembers(householdId)
  }

  const deleteHouseholdMember = async (membershipId: number) => {
    const householdId = settings.value.account.householdId

    if (!householdId) {
      return
    }

    await apiDeleteMember(householdId, membershipId)
    settings.value.account.members = await listMembers(householdId)
  }

  const resetSettings = () => {
    settings.value = mergeNonAccountSettings({
      account: settings.value.account,
      summary: settings.value.summary,
    })
    saveStatus.value = 'idle'
  }

  const syncDevices = () => {
    settings.value.summary.lastSync = '刚刚'
  }

  const updateBackupTime = () => {
    settings.value.backup.lastBackupTime = new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(new Date())
  }

  const importSettings = (nextSettings: SettingsState) => {
    settings.value = mergeNonAccountSettings(nextSettings)
    saveStatus.value = 'idle'
  }

  return {
    addHouseholdMember,
    deleteAccountAvatar,
    deleteHouseholdMember,
    importSettings,
    loadAccountHome,
    loading,
    resetSettings,
    saveAccountHome,
    saveSettings,
    saveStatus,
    savedAt,
    settings,
    syncDevices,
    updateMemberRole,
    updateBackupTime,
    uploadAccountAvatar,
  }
})
