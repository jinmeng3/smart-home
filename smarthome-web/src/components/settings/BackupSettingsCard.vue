<script setup lang="ts">
import type { BackupSettings } from '../../types/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'

defineProps<{
  backup: BackupSettings
}>()
</script>

<template>
  <SettingsSectionCard id="backup" icon="▤" title="备份恢复">
    <div class="settings-field"><span>导出配置</span><button class="secondary-button" type="button">导出</button></div>
    <div class="settings-field"><span>导入备份</span><button class="secondary-button" type="button">导入</button></div>
    <div class="settings-field"><span>自动备份</span><el-switch v-model="backup.autoBackup" /></div>
    <div class="settings-field"><span>最近备份时间</span><strong class="text-sm font-semibold text-[var(--color-text-secondary)]">{{ backup.lastBackupTime }}</strong></div>
  </SettingsSectionCard>
</template>
