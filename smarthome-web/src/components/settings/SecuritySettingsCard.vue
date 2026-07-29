<script setup lang="ts">
import type { SecuritySettings } from '../../types/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'

defineProps<{
  security: SecuritySettings
}>()
</script>

<template>
  <SettingsSectionCard id="security" icon="◇" title="安全">
    <div class="settings-field"><span>修改密码</span><button class="secondary-button" type="button">修改</button></div>
    <div class="settings-field"><span>双重认证</span><el-switch v-model="security.twoFactorEnabled" /></div>
    <div class="settings-field"><span>登录设备管理</span><button class="secondary-button" type="button">管理</button></div>
    <div class="settings-field"><span>操作日志</span><button class="secondary-button" type="button">查看</button></div>
  </SettingsSectionCard>
</template>
