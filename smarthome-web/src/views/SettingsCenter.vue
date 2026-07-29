<script setup lang="ts">
import { computed, ref } from 'vue'
import AccountSettingsCard from '../components/settings/AccountSettingsCard.vue'
import AiAssistantSettingsCard from '../components/settings/AiAssistantSettingsCard.vue'
import AppearanceSettingsCard from '../components/settings/AppearanceSettingsCard.vue'
import BackupSettingsCard from '../components/settings/BackupSettingsCard.vue'
import HomeAssistantSettingsCard from '../components/settings/HomeAssistantSettingsCard.vue'
import NotificationSettingsCard from '../components/settings/NotificationSettingsCard.vue'
import SecuritySettingsCard from '../components/settings/SecuritySettingsCard.vue'
import SecurityStatusPanel from '../components/settings/SecurityStatusPanel.vue'
import SettingsSuggestionPanel from '../components/settings/SettingsSuggestionPanel.vue'
import SettingsSummaryPanel from '../components/settings/SettingsSummaryPanel.vue'
import SettingsTabs from '../components/settings/SettingsTabs.vue'
import { useSettingsStore } from '../stores/settings'
import type { SettingsSectionId } from '../types/settings'

const settingsStore = useSettingsStore()
const activeSection = ref<SettingsSectionId>('account')

const settings = computed(() => settingsStore.settings)

const selectSection = (section: SettingsSectionId) => {
  activeSection.value = section
  document.getElementById(section)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
          <AccountSettingsCard :account="settings.account" />
          <AppearanceSettingsCard :appearance="settings.appearance" />
          <AiAssistantSettingsCard :ai="settings.aiAssistant" />
          <HomeAssistantSettingsCard :home-assistant="settings.homeAssistant" @sync="settingsStore.syncDevices" />
          <NotificationSettingsCard :notifications="settings.notifications" />
          <SecuritySettingsCard :security="settings.security" />
          <BackupSettingsCard :backup="settings.backup" />
        </div>
      </div>

      <footer class="mt-4 flex shrink-0 items-center gap-4 rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-3">
        <button class="primary-button" type="button" @click="settingsStore.saveSettings">保存更改</button>
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
