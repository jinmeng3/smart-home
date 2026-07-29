<script setup lang="ts">
import ChatWindow from '../components/chat/ChatWindow.vue'
import Header from '../components/layout/Header.vue'
import RightPanel from '../components/layout/RightPanel.vue'
</script>

<template>
  <div class="contents">
    <section class="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] shadow-soft backdrop-blur">
      <Header />
      <ChatWindow />
    </section>
    <RightPanel />
  </div>
</template>
