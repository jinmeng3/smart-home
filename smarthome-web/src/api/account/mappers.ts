import type { HouseholdMember, HouseholdRole } from "../../types/settings";

/** 账户/家庭 DTO 与领域模型互转（SRP：映射职责独立于请求）。 */

export interface MemberRead {
  membership_id: number;
  user_id: number;
  name: string;
  email: string;
  avatar_url: string | null;
  role: HouseholdRole;
  joined_at: string;
}

export interface MemberListResponse {
  items: MemberRead[];
  total: number;
}

export const toMember = (member: MemberRead): HouseholdMember => ({
  membershipId: member.membership_id,
  userId: member.user_id,
  name: member.name,
  email: member.email,
  avatarUrl: member.avatar_url,
  role: member.role,
  joinedAt: member.joined_at,
});
