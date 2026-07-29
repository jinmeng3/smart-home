<script setup lang="ts">
import { Bell, Search } from '@element-plus/icons-vue'
</script>

<template>
  <header class="flex h-[88px] shrink-0 items-center justify-between border-b border-blue-100/70 px-6 py-4">
    <div>
      <h1 class="text-xl font-extrabold tracking-normal text-slate-900">上午好，张晓明 👋</h1>
      <p class="mt-1 text-sm font-medium text-slate-500">今天是 2025年5月20日 星期二</p>
    </div>

    <div class="flex items-center gap-3">
      <el-input class="header-search" placeholder="搜索设备、场景或房间" :prefix-icon="Search" />
      <el-badge :value="3">
        <el-button :icon="Bell" circle />
      </el-badge>
      <div class="h-10 w-10 rounded-full bg-gradient-to-br from-blue-100 to-blue-600"></div>
    </div>
  </header>
</template>
