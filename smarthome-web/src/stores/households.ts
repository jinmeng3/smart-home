import { computed, ref } from "vue";
import { defineStore } from "pinia";
import {
  listHouseholds as apiListHouseholds,
  listMembers as apiListMembers,
} from "../api/account";
import type { HouseholdContext, HouseholdMember } from "../types/settings";

/**
 * 活动家庭 ID 的本地持久化键。
 * 属用户级选择偏好：刷新后恢复同一家庭，不随服务端偏好同步。
 */
export const activeHouseholdStorageKey = "smart-home-active-household-id";

const readStoredActiveId = (): number | null => {
  const raw = window.localStorage.getItem(activeHouseholdStorageKey);
  const id = raw ? Number(raw) : NaN;
  return Number.isFinite(id) && id > 0 ? id : null;
};

const persistActiveId = (id: number | null) => {
  if (id == null) {
    window.localStorage.removeItem(activeHouseholdStorageKey);
  } else {
    window.localStorage.setItem(activeHouseholdStorageKey, String(id));
  }
};

/**
 * 全局家庭上下文。
 *
 * 承担三件事：
 * 1. 家庭列表 + 活动家庭 + 当前角色 的唯一真相（households / activeHouseholdId / activeRole）；
 * 2. 活动家庭的成员列表缓存（members）；
 * 3. 刷新恢复（localStorage）与切换/清理动作，供总览、自动化、聊天等统一消费。
 *
 * 其他页面/store 不再各自“取列表第一项”或硬编码家庭 ID。
 */
export const useHouseholdStore = defineStore("households", () => {
  const households = ref<HouseholdContext[]>([]);
  const activeHouseholdId = ref<number | null>(null);
  const members = ref<HouseholdMember[]>([]);
  const loading = ref(false);
  const loadedOnce = ref(false);
  const switching = ref(false);
  const error = ref<string | null>(null);

  const activeHousehold = computed(
    () =>
      households.value.find((item) => item.id === activeHouseholdId.value) ??
      null,
  );
  const activeRole = computed(() => activeHousehold.value?.role ?? null);
  const isAdmin = computed(() => activeRole.value === "admin");
  const activeMemberCount = computed(
    () => activeHousehold.value?.memberCount ?? members.value.length,
  );

  const resolveActiveId = (
    list: HouseholdContext[],
    stored: number | null,
  ): number | null => {
    if (stored != null && list.some((item) => item.id === stored)) {
      return stored;
    }
    return list[0]?.id ?? null;
  };

  const refreshMembers = async () => {
    const id = activeHouseholdId.value;
    if (id == null) {
      members.value = [];
      return;
    }
    const nextMembers = await apiListMembers(id);
    // 仅当仍指向同一家庭时提交，避免切换竞态覆盖错误数据
    if (activeHouseholdId.value === id) {
      members.value = nextMembers;
    }
  };

  const load = async (force = false) => {
    if (loadedOnce.value && !force) return;
    loading.value = true;
    error.value = null;
    try {
      const list = await apiListHouseholds();
      households.value = list;
      const resolved = resolveActiveId(list, readStoredActiveId());
      activeHouseholdId.value = resolved;
      persistActiveId(resolved);
      await refreshMembers();
      loadedOnce.value = true;
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : "家庭列表加载失败";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const switchHousehold = async (householdId: number) => {
    if (householdId === activeHouseholdId.value) return;
    if (!households.value.some((item) => item.id === householdId)) {
      throw new Error("家庭不存在");
    }
    switching.value = true;
    try {
      activeHouseholdId.value = householdId;
      persistActiveId(householdId);
      await refreshMembers();
    } finally {
      switching.value = false;
    }
  };

  /** 重新拉取家庭列表（家庭创建/更新后调用）。 */
  const refresh = async () => {
    await load(true);
  };

  /** 退出登录 / 会话失效时清理全部用户级家庭状态。 */
  const clear = () => {
    households.value = [];
    activeHouseholdId.value = null;
    members.value = [];
    loadedOnce.value = false;
    switching.value = false;
    error.value = null;
    persistActiveId(null);
  };

  return {
    activeHousehold,
    activeHouseholdId,
    activeMemberCount,
    activeRole,
    clear,
    error,
    households,
    isAdmin,
    load,
    loadedOnce,
    loading,
    members,
    refresh,
    refreshMembers,
    switchHousehold,
    switching,
  };
});