<script setup lang="ts">
import DeviceListCard from '../dashboard/DeviceListCard.vue'
import EnergyCard from '../dashboard/EnergyCard.vue'
import ScheduleCard from '../dashboard/ScheduleCard.vue'
import SecurityCard from '../dashboard/SecurityCard.vue'
</script>

<template>
  <aside class="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto pr-1">
    <ScheduleCard />
    <DeviceListCard />
    <div class="grid min-h-0 flex-1 grid-cols-2 gap-3">
      <EnergyCard />
      <SecurityCard />
    </div>
  </aside>
</template>
