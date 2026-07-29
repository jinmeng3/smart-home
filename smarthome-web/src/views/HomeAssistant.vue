<script setup lang="ts">
import ChatWindow from '../components/chat/ChatWindow.vue'
import Header from '../components/layout/Header.vue'
import RightPanel from '../components/layout/RightPanel.vue'
import Sidebar from '../components/layout/Sidebar.vue'
import { useHomeStore } from '../stores/home'

const store = useHomeStore()
</script>

<template>
  <main class="h-screen overflow-hidden bg-[var(--color-page-background)] text-[var(--color-text-primary)]">
    <div
      class="grid h-full gap-2 bg-[radial-gradient(circle_at_20%_10%,rgba(37,99,235,0.08),transparent_28%),linear-gradient(135deg,var(--color-page-background)_0%,var(--color-sidebar-background)_100%)] p-2 transition-[grid-template-columns] duration-500 ease-out"
      :class="store.sidebarCollapsed ? 'grid-cols-[72px_minmax(0,1fr)_330px]' : 'grid-cols-[240px_minmax(0,1fr)_330px]'"
    >
      <Sidebar />

      <section class="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] shadow-soft backdrop-blur">
        <Header />
        <ChatWindow />
      </section>

      <RightPanel />
    </div>
  </main>
</template>
