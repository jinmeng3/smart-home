import { createRouter, createWebHistory } from 'vue-router'
import HomeAssistant from '../views/HomeAssistant.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home-assistant',
      component: HomeAssistant,
    },
  ],
})
