<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { FamilyMember, MemberRole } from '../../types/account'
import SettingsSectionCard from './SettingsSectionCard.vue'
import MemberListItem from './MemberListItem.vue'

const props = defineProps<{
  adminCount: number
  canManage: boolean
  currentMemberId: number | null
  loadingMemberId: number | null
  members: FamilyMember[]
  submitting: boolean
}>()

const emit = defineEmits<{
  addMember: [email: string, role: MemberRole]
  removeMember: [id: number]
  updateMemberRole: [id: number, role: MemberRole]
}>()

const memberEmail = ref('')
const memberRole = ref<MemberRole>('member')
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const readonlyMessage = computed(() => (props.canManage ? '' : '普通成员只能查看成员列表'))

const addMember = () => {
  const email = memberEmail.value.trim()

  if (!props.canManage) {
    ElMessage.warning(readonlyMessage.value)
    return
  }

  if (!emailPattern.test(email)) {
    ElMessage.warning('请输入正确的成员邮箱')
    return
  }

  if (props.members.some((member) => member.email.toLowerCase() === email.toLowerCase())) {
    ElMessage.error('该成员已存在')
    return
  }

  emit('addMember', email, memberRole.value)
  memberEmail.value = ''
}

const canRemove = (member: FamilyMember) => {
  if (!props.canManage || member.id === props.currentMemberId) {
    return false
  }

  return member.role === 'member'
}

const updateMemberRole = (member: FamilyMember, role: MemberRole) => {
  if (!props.canManage) {
    ElMessage.warning(readonlyMessage.value)
    return
  }

  if (member.role === 'admin' && role === 'member' && props.adminCount <= 1) {
    ElMessage.error('家庭至少保留一名管理员')
    return
  }

  emit('updateMemberRole', member.id, role)
}
</script>

<template>
  <SettingsSectionCard id="members" icon="▣" title="家庭成员与权限">
    <div class="mb-4 grid grid-cols-[minmax(0,1fr)_104px_76px] gap-2">
      <input v-model="memberEmail" class="settings-input w-full" :disabled="!canManage || submitting" placeholder="成员邮箱" />
      <select v-model="memberRole" class="settings-input w-full px-2" :disabled="!canManage || submitting">
        <option value="admin">管理员</option>
        <option value="member">成员</option>
      </select>
      <button class="secondary-button min-w-0 px-2" :disabled="!canManage || submitting" type="button" @click="addMember">
        {{ submitting ? '添加中' : '添加' }}
      </button>
    </div>

    <p v-if="readonlyMessage" class="mb-3 text-xs font-medium text-[var(--color-text-tertiary)]">{{ readonlyMessage }}</p>

    <div class="grid max-h-[320px] gap-2 overflow-y-auto pr-1">
      <MemberListItem
        v-for="member in members"
        :key="member.id"
        :can-edit="canManage"
        :can-remove="canRemove(member)"
        :member="member"
        :remove-loading="loadingMemberId === member.id"
        :role-loading="loadingMemberId === member.id"
        @remove="emit('removeMember', member.id)"
        @update-role="(_, role) => updateMemberRole(member, role)"
      />
      <div v-if="!members.length" class="rounded-lg border border-dashed border-[var(--color-border-default)] py-10 text-center text-sm text-[var(--color-text-tertiary)]">
        暂无成员
      </div>
    </div>
  </SettingsSectionCard>
</template>
