export interface AccountForm {
  name: string
  email: string
  avatarUrl: string | null
  householdName: string
  address: string
  timezone: string
}

export type MemberRole = 'admin' | 'member'

export interface FamilyMember {
  id: number
  name: string
  email: string
  avatarUrl: string | null
  role: MemberRole
}
