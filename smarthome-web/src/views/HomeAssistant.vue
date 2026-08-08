<script setup lang="ts">
import ChatWindow from "../components/chat/ChatWindow.vue";
import Header from "../components/layout/Header.vue";
import DeviceListCard from "../components/dashboard/DeviceListCard.vue";
import EnergyCard from "../components/dashboard/EnergyCard.vue";
import ScheduleCard from "../components/dashboard/ScheduleCard.vue";
import SecurityCard from "../components/dashboard/SecurityCard.vue";
import { useAuthenticatedLoader } from "../composables/useAuthenticatedLoader";
import { useAuthStore } from "../stores/auth";
import { useHomeStore } from "../stores/home";

const store = useHomeStore();
const authStore = useAuthStore();

const refreshHomeData = () => {
    return Promise.all([
        store.loadDevices(),
        store.refreshRecentConversations(),
    ]).then(() => undefined);
};

useAuthenticatedLoader(refreshHomeData);
</script>

<template>
    <div class="app-page-layout">
        <section
            :inert="!authStore.isAuthenticated"
            :aria-disabled="!authStore.isAuthenticated"
            class="page-enter flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] shadow-soft"
        >
            <Header />
            <ChatWindow />
        </section>
        <div
            :inert="!authStore.isAuthenticated"
            :aria-disabled="!authStore.isAuthenticated"
            class="assistant-rail flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto"
        >
            <ScheduleCard />
            <DeviceListCard />
            <div class="grid min-h-0 flex-1 grid-cols-2 gap-3">
                <EnergyCard />
                <SecurityCard />
            </div>
        </div>
    </div>
</template>

<style scoped>
@media (max-width: 1279px) {
    .assistant-rail {
        overflow-y: visible;
    }
}

@media (max-width: 767px) {
    .assistant-rail > div:last-child {
        grid-template-columns: minmax(0, 1fr);
    }
}
</style>
