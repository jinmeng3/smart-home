import { createRouter, createWebHistory } from "vue-router";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home-assistant",
      component: () => import("../views/HomeAssistant.vue"),
    },
    {
      path: "/rooms",
      name: "room-control",
      component: () => import("../views/RoomControlView.vue"),
    },
    {
      path: "/settings",
      name: "settings-center",
      component: () => import("../views/SettingsCenter.vue"),
    },
    {
      path: "/devices",
      name: "device-management",
      component: () => import("../views/DeviceManagement.vue"),
    },
    {
      path: "/scenes",
      name: "scene-mode",
      component: () => import("../views/SceneModeView.vue"),
    },
    {
      path: "/overview",
      name: "whole-home-overview",
      component: () => import("../views/WholeHomeOverview.vue"),
    },
    {
      path: "/automations",
      name: "automation-center",
      component: () => import("../views/AutomationCenter.vue"),
    },
  ],
});
