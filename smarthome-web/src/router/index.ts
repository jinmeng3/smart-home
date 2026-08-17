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

// 路由层认证守卫：
// - 未登录访问受保护业务页时，只弹一次登录引导并回到 “/”；
// - 已登录时放行，并把“已引导”标记复位，下次失效重新引导。
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
