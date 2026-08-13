<script setup lang="ts">
import { computed } from "vue";
import { useSettingsStore } from "../../stores/settings";
import type { ChatMessage } from "../../types/chat";
import ChatMessageShell from "./ChatMessageShell.vue";

defineProps<{
    message: ChatMessage;
}>();

const settingsStore = useSettingsStore();
const account = computed(() => settingsStore.settings.account);
const accountInitial = computed(() =>
    account.value.username.trim().slice(0, 1).toUpperCase(),
);
</script>

<template>
    <ChatMessageShell side="right" :timestamp="message.timestamp">
        <template #avatar>
            <img
                v-if="account.avatarUrl"
                class="h-10 w-10 self-start rounded-full object-cover ring-2 ring-white/60 avatar-in"
                style="animation-delay: 40ms"
                :src="account.avatarUrl"
                alt=""
            />
            <div
                v-else
                class="grid h-10 w-10 self-start place-items-center rounded-full bg-gradient-to-br from-blue-100 to-blue-200 text-sm font-bold text-blue-700 ring-2 ring-white/60 avatar-in"
                style="animation-delay: 40ms"
            >
                {{ accountInitial }}
            </div>
        </template>

        <div
            class="user-bubble whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-gradient-to-br from-blue-600 via-blue-500 to-sky-500 px-5 py-3 text-sm font-medium leading-6 text-white shadow-md shadow-blue-500/15 ring-1 ring-white/15"
        >
            {{ message.content }}
        </div>
    </ChatMessageShell>
</template>

<style scoped>
.user-bubble {
    position: relative;
    transition:
        transform 180ms var(--motion-ease),
        box-shadow 180ms var(--motion-ease);
}
</style>