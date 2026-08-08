import { apiRequest } from "./client";
import type {
  HouseholdMember,
  HouseholdRole,
  UserPreferences,
} from "../types/settings";

// ── DTO 类型 ──────────────────────────────────────────────────────────────────────

interface AccountRead {
  id: number;
  name: string;
  email: string;
  avatar_url: string | null;
}

interface HouseholdRead {
  id: number;
  name: string;
  address: string | null;
  timezone: string;
  role?: HouseholdRole | "ADMIN" | "MEMBER";
  member_count?: number;
}

interface MemberRead {
  membership_id: number;
  user_id: number;
  name: string;
  email: string;
  avatar_url: string | null;
  role: HouseholdRole;
  joined_at: string;
}

interface MemberListResponse {
  items: MemberRead[];
  total: number;
}

// ── 映射函数 ──────────────────────────────────────────────────────────────────────

const toMember = (member: MemberRead): HouseholdMember => ({
  membershipId: member.membership_id,
  userId: member.user_id,
  name: member.name,
  email: member.email,
  avatarUrl: member.avatar_url,
  role: member.role,
  joinedAt: member.joined_at,
});

// ── API 导出函数 ──────────────────────────────────────────────────────────────────

export const getAccount = () => apiRequest<AccountRead>("/api/account/me");

export const updateAccount = (payload: { name?: string; email?: string }) =>
  apiRequest<AccountRead>("/api/account/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const uploadAvatar = (file: File) => {
  const formData = new FormData();
  formData.append("avatar", file);

  return apiRequest<{ avatar_url: string | null }>("/api/account/me/avatar", {
    method: "POST",
    body: formData,
  });
};

export const deleteAvatar = () =>
  apiRequest<{ avatar_url: string | null }>("/api/account/me/avatar", {
    method: "DELETE",
  });

export const listHouseholds = () =>
  apiRequest<HouseholdRead[]>("/api/households");

export const createHousehold = (payload: {
  name: string;
  address?: string | null;
  timezone?: string;
}) =>
  apiRequest<HouseholdRead>("/api/households", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const getHouseholdDetail = (householdId: number) =>
  apiRequest<HouseholdRead>(`/api/households/${householdId}`);

export const updateHousehold = (
  householdId: number,
  payload: { name?: string; address?: string | null; timezone?: string },
) =>
  apiRequest<HouseholdRead>(`/api/households/${householdId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const listMembers = async (householdId: number) => {
  const response = await apiRequest<MemberListResponse>(
    `/api/households/${householdId}/members`,
  );
  return response.items.map(toMember);
};

export const addMember = async (
  householdId: number,
  payload: { email: string; role: HouseholdRole },
) => {
  const response = await apiRequest<MemberRead>(
    `/api/households/${householdId}/members`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
  return toMember(response);
};

export const updateMemberRole = async (
  householdId: number,
  membershipId: number,
  role: HouseholdRole,
) => {
  const response = await apiRequest<MemberRead>(
    `/api/households/${householdId}/members/${membershipId}`,
    {
      method: "PATCH",
      body: JSON.stringify({ role }),
    },
  );
  return toMember(response);
};

export const deleteMember = (householdId: number, membershipId: number) =>
  apiRequest<void>(`/api/households/${householdId}/members/${membershipId}`, {
    method: "DELETE",
  });

export const getUserPreferences = () =>
  apiRequest<UserPreferences>("/api/account/me/preferences");

export const updateUserPreferences = (payload: UserPreferences) =>
  apiRequest<UserPreferences>("/api/account/me/preferences", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
