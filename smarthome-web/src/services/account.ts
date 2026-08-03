import {
  addMember as apiAddMember,
  deleteAvatar as apiDeleteAvatar,
  deleteMember as apiDeleteMember,
  getAccount,
  listHouseholds,
  listMembers,
  updateAccount as apiUpdateAccount,
  updateHousehold as apiUpdateHousehold,
  updateMemberRole as apiUpdateMemberRole,
  uploadAvatar as apiUploadAvatar,
  type AccountRead,
  type HouseholdRead,
} from "../api/account";
import type { HouseholdMember, HouseholdRole } from "../types/settings";

/**
 * 账户与家庭领域服务层（DIP：store 只依赖此抽象，
 * 不直接依赖 API 实现；单一职责——仅编排账户/家庭/成员操作）。
 */
export const accountService = {
  getMe(): Promise<AccountRead> {
    return getAccount();
  },

  updateMe(payload: { name?: string; email?: string }): Promise<AccountRead> {
    return apiUpdateAccount(payload);
  },

  uploadAvatar(file: File): Promise<{ avatar_url: string | null }> {
    return apiUploadAvatar(file);
  },

  deleteAvatar(): Promise<{ avatar_url: string | null }> {
    return apiDeleteAvatar();
  },

  listHouseholds(): Promise<HouseholdRead[]> {
    return listHouseholds();
  },

  updateHousehold(
    householdId: number,
    payload: { name?: string; address?: string | null; timezone?: string },
  ): Promise<HouseholdRead> {
    return apiUpdateHousehold(householdId, payload);
  },

  listMembers(householdId: number): Promise<HouseholdMember[]> {
    return listMembers(householdId);
  },

  addMember(
    householdId: number,
    payload: { email: string; role: HouseholdRole },
  ): Promise<HouseholdMember> {
    return apiAddMember(householdId, payload);
  },

  updateMemberRole(
    householdId: number,
    membershipId: number,
    role: HouseholdRole,
  ): Promise<HouseholdMember> {
    return apiUpdateMemberRole(householdId, membershipId, role);
  },

  deleteMember(householdId: number, membershipId: number): Promise<void> {
    return apiDeleteMember(householdId, membershipId);
  },
};
