<script setup lang="ts">
import type { SettingsSummary } from '../../types/settings'

defineProps<{
  summary: SettingsSummary
}>()
</script>

<template>
  <section class="motion-card rounded-xl border border-[var(--color-border-default)] bg-[var(--color-panel-background)] p-5">
    <div class="mb-4 flex items-center gap-3">
      <span class="grid h-9 w-9 place-items-center rounded-lg bg-[var(--color-ai-soft)] text-[var(--color-ai)]">♙</span>
      <h2 class="text-base font-extrabold">账户与系统</h2>
    </div>
    <div class="grid gap-4 text-sm">
      <div class="flex justify-between"><span class="text-[var(--color-text-tertiary)]">当前家庭</span><strong>{{ summary.currentHome }}</strong></div>
      <div class="flex justify-between"><span class="text-[var(--color-text-tertiary)]">账号状态</span><span class="rounded-lg bg-[var(--color-primary-50)] px-2 py-1 font-semibold text-[var(--color-primary-700)]">{{ summary.accountStatus }}</span></div>
      <div class="flex justify-between"><span class="text-[var(--color-text-tertiary)]">平台接入</span><span class="font-semibold text-[var(--color-success)]">● 在线</span></div>
      <div class="flex justify-between"><span class="text-[var(--color-text-tertiary)]">最近同步</span><strong>{{ summary.lastSync }}</strong></div>
    </div>
  </section>
</template>
