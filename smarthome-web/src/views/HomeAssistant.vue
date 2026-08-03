<script setup lang="ts">
import { onMounted, watch } from "vue";
import ChatWindow from "../components/chat/ChatWindow.vue";
import Header from "../components/layout/Header.vue";
import RightPanel from "../components/layout/RightPanel.vue";
import { useAuthStore } from "../stores/auth";
import { useHomeStore } from "../stores/home";

const store = useHomeStore();
const authStore = useAuthStore();

const refreshHomeData = () => {
    if (!authStore.isAuthenticated) {
        return;
    }

    void store.loadDevices();
    void store.refreshRecentConversations();
};

onMounted(() => {
    refreshHomeData();
});

watch(
    () => authStore.isAuthenticated,
    (isAuthenticated) => {
        if (isAuthenticated) {
            refreshHomeData();
        }
    },
);
</script>

<template>
    <div class="contents">
        <section
            class="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-workspace-background)] shadow-soft"
        >
            <Header />
            <ChatWindow />
        </section>
        <RightPanel />
    </div>
</template>
