import { createRouter, createWebHistory } from "vue-router";
import { navigationItems } from "./navigation";

export const router = createRouter({
  history: createWebHistory(),
  routes: navigationItems.map((item) => ({
    path: item.path,
    name: item.routeName,
    component: item.loadComponent,
  })),
});
