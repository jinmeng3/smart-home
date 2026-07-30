<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { AccountSettings } from '../../types/settings'
import SettingsSectionCard from './SettingsSectionCard.vue'

defineOptions({
  inheritAttrs: false,
})

const props = defineProps<{
  account: AccountSettings
}>()

const emit = defineEmits<{
  addMember: [email: string, role: 'admin' | 'member']
  deleteAvatar: []
  deleteMember: [membershipId: number]
  updateMemberRole: [membershipId: number, role: 'admin' | 'member']
  uploadAvatar: [file: File]
}>()

const memberEmail = ref('')
const memberRole = ref<'admin' | 'member'>('member')
const avatarInput = ref<HTMLInputElement | null>(null)
const accountInitial = computed(() => props.account.username.trim().slice(0, 1))

const selectAvatar = () => {
  avatarInput.value?.click()
}

const uploadAvatar = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) {
    return
  }

  emit('uploadAvatar', file)
  target.value = ''
}

const addMember = () => {
  const email = memberEmail.value.trim()

  if (!email) {
    ElMessage.warning('请输入成员邮箱')
    return
  }

  emit('addMember', email, memberRole.value)
  memberEmail.value = ''
}
</script>

<template>
  <SettingsSectionCard v-bind="$attrs" id="account" icon="♙" title="账户">
    <div class="account-settings-grid">
      <section class="account-profile-section min-w-0 border-b border-[var(--color-divider)] pb-4">
        <div class="flex items-center gap-4">
          <img v-if="account.avatarUrl" class="h-12 max-h-12 w-12 max-w-12 shrink-0 rounded-full object-cover" :src="account.avatarUrl" alt="" />
          <div v-else class="grid h-12 max-h-12 w-12 max-w-12 shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-100 to-blue-600 text-base font-extrabold text-white">
            {{ accountInitial }}
          </div>
          <div class="min-w-0">
            <strong class="block truncate text-[var(--color-text-primary)]">{{ account.username || '未命名账户' }}</strong>
            <span class="block truncate text-sm text-[var(--color-text-tertiary)]">{{ account.email || '未设置邮箱' }}</span>
          </div>
        </div>
        <div class="mt-3 flex gap-2">
          <button class="secondary-button h-8 min-w-[70px]" type="button" @click="selectAvatar">上传</button>
          <button class="secondary-button h-8 min-w-[70px]" type="button" @click="emit('deleteAvatar')">删除</button>
          <input ref="avatarInput" class="hidden" accept="image/jpeg,image/png,image/webp" type="file" @change="uploadAvatar" />
        </div>
        <div class="mt-4 grid gap-2">
          <label class="grid grid-cols-[64px_minmax(0,1fr)] items-center gap-2 text-sm text-[var(--color-text-secondary)]">
            <span>姓名</span>
            <input v-model="account.username" class="settings-input w-full" />
          </label>
          <label class="grid grid-cols-[64px_minmax(0,1fr)] items-center gap-2 text-sm text-[var(--color-text-secondary)]">
            <span>邮箱</span>
            <input v-model="account.email" class="settings-input w-full" />
          </label>
          <label class="grid grid-cols-[64px_minmax(0,1fr)] items-center gap-2 text-sm text-[var(--color-text-secondary)]">
            <span>家庭名称</span>
            <input v-model="account.familyName" class="settings-input w-full" />
          </label>
          <label class="grid grid-cols-[64px_minmax(0,1fr)] items-center gap-2 text-sm text-[var(--color-text-secondary)]">
            <span>家庭地址</span>
            <input v-model="account.householdAddress" class="settings-input w-full" />
          </label>
          <label class="grid grid-cols-[64px_minmax(0,1fr)] items-center gap-2 text-sm text-[var(--color-text-secondary)]">
            <span>家庭时区</span>
            <input v-model="account.householdTimezone" class="settings-input w-full" />
          </label>
        </div>
      </section>

      <section class="min-w-0">
        <div class="mb-3 flex items-center justify-between">
          <strong class="text-sm text-[var(--color-text-primary)]">家庭成员</strong>
          <span class="text-xs text-[var(--color-text-tertiary)]">{{ props.account.members?.length ?? 0 }} 人</span>
        </div>
        <div class="mb-3 grid grid-cols-[minmax(0,1fr)_92px_64px] gap-2">
          <input v-model="memberEmail" class="settings-input w-full" placeholder="成员邮箱" />
          <select v-model="memberRole" class="settings-input w-full px-2">
            <option value="member">成员</option>
            <option value="admin">管理员</option>
          </select>
          <button class="secondary-button min-w-0 px-2" type="button" @click="addMember">添加</button>
        </div>
        <div class="grid max-h-[188px] gap-2 overflow-y-auto pr-1">
          <div v-for="member in account.members" :key="member.membershipId" class="grid min-h-[48px] grid-cols-[minmax(0,1fr)_92px_60px] items-center gap-2 rounded-lg border border-[var(--color-border-subtle)] px-3 py-2">
            <span class="min-w-0">
              <strong class="block truncate text-sm">{{ member.name }}</strong>
              <span class="block truncate text-xs text-[var(--color-text-tertiary)]">{{ member.email }}</span>
            </span>
            <select class="settings-input w-full px-2" :value="member.role" @change="emit('updateMemberRole', member.membershipId, ($event.target as HTMLSelectElement).value as 'admin' | 'member')">
              <option value="member">成员</option>
              <option value="admin">管理员</option>
            </select>
            <button class="secondary-button min-w-0 px-2" type="button" @click="emit('deleteMember', member.membershipId)">移除</button>
          </div>
          <div v-if="!account.members?.length" class="rounded-lg border border-dashed border-[var(--color-border-default)] py-7 text-center text-sm text-[var(--color-text-tertiary)]">
            暂无成员
          </div>
        </div>
      </section>
    </div>
  </SettingsSectionCard>
</template>

<style scoped>
.account-settings-grid {
  display: grid;
  gap: 16px;
}

.account-profile-section {
  border-bottom-width: 1px;
}

@media (min-width: 760px) {
  .account-settings-grid {
    grid-template-columns: minmax(280px, 0.9fr) minmax(340px, 1.1fr);
  }

  .account-profile-section {
    border-right: 1px solid var(--color-divider);
    border-bottom-width: 0;
    padding-right: 16px;
    padding-bottom: 0;
  }
}
</style>
