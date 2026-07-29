<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { AccountSettings } from '../../types/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'

defineProps<{
  account: AccountSettings
}>()

const showPending = (name: string) => {
  ElMessage.info(`${name}功能已进入待办流程`)
}
</script>

<template>
  <SettingsSectionCard id="account" icon="♙" title="账户">
    <div class="mb-4 flex items-center gap-4">
      <div class="h-14 w-14 rounded-full bg-gradient-to-br from-blue-100 to-blue-600"></div>
      <div>
        <strong class="block text-[var(--color-text-primary)]">{{ account.username }}</strong>
        <span class="text-sm text-[var(--color-text-tertiary)]">{{ account.email }}</span>
      </div>
    </div>
    <div class="grid gap-3">
      <button class="settings-row" type="button" @click="showPending('家庭成员管理')"><span>家庭成员管理</span><span>›</span></button>
      <button class="settings-row" type="button" @click="showPending('角色权限')"><span>角色权限</span><span>›</span></button>
    </div>
  </SettingsSectionCard>
</template>
