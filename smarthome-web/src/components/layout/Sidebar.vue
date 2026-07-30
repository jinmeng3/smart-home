<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useHomeStore } from '../../stores/home'
import { useSettingsStore } from '../../stores/settings'
import AnimatedList from '../animation/AnimatedList.vue'

const store = useHomeStore()
const settingsStore = useSettingsStore()
const route = useRoute()
const router = useRouter()

const menuItems = [
  { icon: '✦', label: '智能对话', path: '/' },
  { icon: '▦', label: '全屋总览' },
  { icon: '▣', label: '房间控制' },
  { icon: '☷', label: '设备管理' },
  { icon: '♙', label: '场景模式' },
  { icon: '⌘', label: '自动化' },
  { icon: '▥', label: '能耗分析' },
  { icon: '◇', label: '安防中心' },
  { icon: '⚙', label: '设置', path: '/settings' },
]

const activeLabel = computed(() => (route.path === '/settings' ? '设置' : store.activeMenu))
const activeIndex = computed(() => Math.max(menuItems.findIndex((item) => item.label === activeLabel.value), 0))
const account = computed(() => settingsStore.settings.account)
const accountInitial = computed(() => account.value.username.trim().slice(0, 1).toUpperCase())

const selectMenu = async (item: (typeof menuItems)[number]) => {
  store.setActiveMenu(item.label)

  if (item.path && item.path !== route.path) {
    await router.push(item.path)
  }
}
</script>

<template>
  <aside
    class="page-enter-stagger relative min-h-0 overflow-hidden rounded-2xl border border-[var(--color-border-default)] border-r-[var(--color-border-default)] bg-[var(--color-sidebar-background)] py-5 shadow-soft backdrop-blur transition-[padding] duration-500 ease-out"
    :class="store.sidebarCollapsed ? 'px-2' : 'px-4'"
    style="animation-delay: 0ms"
  >
    <div class="flex items-center transition-all duration-500 ease-out" :class="store.sidebarCollapsed ? 'relative mb-4 h-11 gap-0' : 'mb-5 h-[58px] justify-start gap-3'">
      <button
        class="motion-button grid shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-sky-400 text-lg font-bold text-white shadow-lg shadow-blue-500/20 transition-all duration-300 hover:scale-105"
        :class="store.sidebarCollapsed ? 'absolute left-1/2 h-10 w-10 -translate-x-1/2' : 'h-10 w-10'"
        type="button"
        :title="store.sidebarCollapsed ? '展开菜单' : 'Orion Home Assistant'"
        @click="store.sidebarCollapsed && store.toggleSidebar()"
      >
        ✦
      </button>

      <strong class="block overflow-hidden whitespace-normal text-lg font-extrabold leading-7 text-blue-700 transition-all duration-300 ease-out" :class="store.sidebarCollapsed ? 'w-0 translate-x-2 opacity-0' : 'w-[132px] translate-x-0 opacity-100'">
        Orion Home Assistant
      </strong>

      <button
        class="motion-button ml-auto grid h-8 w-8 shrink-0 place-items-center rounded-lg text-slate-500 transition-all duration-300 hover:bg-blue-50 hover:text-blue-700"
        :class="store.sidebarCollapsed ? 'w-0 scale-75 overflow-hidden opacity-0' : 'w-8 scale-100 opacity-100'"
        type="button"
        title="折叠菜单"
        @click="store.toggleSidebar"
      >
        ‹
      </button>
    </div>

    <div class="sidebar-scroll overflow-y-auto overscroll-contain" :class="store.sidebarCollapsed ? 'h-[calc(100%-128px)] pr-0' : 'h-[calc(100%-154px)] pr-1'">
      <nav class="relative grid gap-1">
        <span
          v-if="!store.sidebarCollapsed"
          class="absolute left-0 h-7 w-1 rounded-full bg-[var(--color-primary-600)] transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]"
          :style="{ transform: `translateY(${activeIndex * 48 + 8}px)` }"
        ></span>

        <button
          v-for="item in menuItems"
          :key="item.label"
          class="motion-button group flex h-11 items-center rounded-lg text-sm font-semibold text-slate-600 transition duration-200 hover:bg-blue-50 hover:text-blue-700 active:scale-[0.98]"
          :class="[
            activeLabel === item.label ? 'bg-[var(--color-primary-100)] text-[var(--color-primary-700)] shadow-sm' : '',
            store.sidebarCollapsed ? 'justify-center px-0' : 'gap-3 px-3 pl-5 text-left',
          ]"
          type="button"
          :title="item.label"
          @click="selectMenu(item)"
        >
          <span class="w-5 text-center transition duration-200 group-hover:translate-x-0.5 group-hover:scale-110">{{ item.icon }}</span>
          <span v-show="!store.sidebarCollapsed" class="truncate">{{ item.label }}</span>
        </button>
      </nav>

      <section class="mt-5 overflow-hidden transition-all duration-300 ease-out" :class="store.sidebarCollapsed ? 'max-h-0 translate-y-2 opacity-0' : 'max-h-[360px] translate-y-0 opacity-100'">
        <h2 class="mb-3 px-2 text-xs font-bold uppercase tracking-wide text-slate-400">最近会话</h2>
        <AnimatedList tag="div" name="recent-list">
          <button v-for="conversation in store.recentConversations" :key="conversation.id" class="motion-button mb-2 grid w-full grid-cols-[28px_minmax(0,1fr)_auto] items-center gap-2 rounded-lg px-2 py-2 text-left transition hover:bg-slate-100" type="button">
            <span class="grid h-7 w-7 place-items-center rounded-lg bg-[var(--color-surface-subtle)] text-xs text-[var(--color-text-tertiary)]">{{ conversation.icon.slice(0, 1) }}</span>
            <span class="truncate text-sm font-medium text-slate-700">{{ conversation.title }}</span>
            <span class="text-xs text-slate-400">{{ conversation.time }}</span>
          </button>
        </AnimatedList>
      </section>
    </div>

    <section
      class="absolute bottom-5 flex items-center overflow-hidden border border-slate-200 bg-white shadow-sm transition-all duration-500 ease-out"
      :class="store.sidebarCollapsed ? 'left-1/2 h-11 w-11 -translate-x-1/2 justify-center gap-0 rounded-full p-0' : 'left-4 right-4 h-[74px] translate-x-0 justify-start gap-3 rounded-xl p-3'"
    >
      <img v-if="account.avatarUrl" class="h-10 w-10 shrink-0 rounded-full object-cover" :src="account.avatarUrl" alt="" />
      <div v-else class="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gradient-to-br from-rose-100 to-slate-700 text-sm font-extrabold text-white">
        {{ accountInitial }}
      </div>
      <div class="min-w-0 overflow-hidden transition-all duration-300 ease-out" :class="store.sidebarCollapsed ? 'w-0 translate-x-3 opacity-0' : 'w-[132px] translate-x-0 opacity-100'">
        <strong class="block truncate text-sm">{{ account.username }}</strong>
        <span class="block truncate text-xs text-slate-500">{{ account.email }}</span>
      </div>
      <span class="ml-auto text-slate-400 transition-all duration-300 ease-out" :class="store.sidebarCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'">⌄</span>
    </section>
  </aside>
</template>
