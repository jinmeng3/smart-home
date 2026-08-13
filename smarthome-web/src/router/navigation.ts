import type { Component } from "vue";

export interface NavigationItem {
  icon: string;
  label: string;
  path: string;
  routeName: string;
  tone: string;
  soft: string;
  loadComponent: () => Promise<Component>;
}

export interface NavigationGroup {
  label: string;
  icon?: string;
  items: NavigationItem[];
}

export const navigationGroups: NavigationGroup[] = [
  {
    label: "家庭总览",
    items: [
      {
        icon: "home",
        label: "全屋总览",
        path: "/overview",
        routeName: "whole-home-overview",
        tone: "var(--color-primary-600)",
        soft: "var(--color-primary-50)",
        loadComponent: () => import("../views/WholeHomeOverview.vue"),
      },
    ],
  },
  {
    label: "空间与设备",
    items: [
      {
        icon: "room",
        label: "房间控制",
        path: "/rooms",
        routeName: "room-control",
        tone: "var(--color-teal-600)",
        soft: "var(--color-teal-soft)",
        loadComponent: () => import("../views/RoomControlView.vue"),
      },
      {
        icon: "device-management",
        label: "设备管理",
        path: "/devices",
        routeName: "device-management",
        tone: "var(--color-device-light)",
        soft: "var(--color-warning-soft)",
        loadComponent: () => import("../views/DeviceManagement.vue"),
      },
    ],
  },
  {
    label: "智能联动",
    items: [
      {
        icon: "scene",
        label: "场景模式",
        path: "/scenes",
        routeName: "scene-mode",
        tone: "var(--color-success)",
        soft: "var(--color-success-soft)",
        loadComponent: () => import("../views/SceneModeView.vue"),
      },
      {
        icon: "automation",
        label: "自动化中心",
        path: "/automations",
        routeName: "automation-center",
        tone: "var(--tone-indigo)",
        soft: "var(--tone-indigo-soft)",
        loadComponent: () => import("../views/AutomationCenter.vue"),
      },
    ],
  },
  {
    label: "智能助手",
    icon: "chat",
    items: [
      {
        icon: "chat",
        label: "智能对话",
        path: "/",
        routeName: "home-assistant",
        tone: "var(--tone-purple)",
        soft: "var(--tone-purple-soft)",
        loadComponent: () => import("../views/HomeAssistant.vue"),
      },
    ],
  },
  {
    label: "系统设置",
    items: [
      {
        icon: "settings",
        label: "设置",
        path: "/settings",
        routeName: "settings-center",
        tone: "var(--color-info)",
        soft: "var(--color-info-soft)",
        loadComponent: () => import("../views/SettingsCenter.vue"),
      },
    ],
  },
];

/** 扁平列表，供 router 和 App.vue 使用 */
export const navigationItems: NavigationItem[] = navigationGroups.flatMap(
  (group) => group.items,
);