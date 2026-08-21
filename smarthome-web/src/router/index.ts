import { createRouter, createWebHistory } from "vue-router";
import { navigationItems } from "./navigation";
import { useAuthStore } from "../stores/auth";

export const router = createRouter({
  history: createWebHistory(),
  routes: navigationItems.map((item) => ({
    path: item.path,
    name: item.routeName,
    component: item.loadComponent,
  })),
});

let loginPromptShown = false;

router.beforeEach((to) => {
  const authStore = useAuthStore();

  if (authStore.isAuthenticated) {
    loginPromptShown = false;
    return true;
  }

  if (!loginPromptShown) {
    loginPromptShown = true;
    authStore.openLogin();
  }

  if (to.path !== "/") {
    return { path: "/" };
  }

  return true;
});
