<script setup lang="ts">
import { computed } from "vue";
import { useSettingsStore } from "../../stores/settings";
import type { ChatMessage } from "../../types/chat";

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
    <article
        class="user-message-enter mb-5 ml-auto grid max-w-[620px] grid-cols-[minmax(0,1fr)_42px] gap-3"
    >
        <div
            class="whitespace-pre-wrap break-words rounded-lg bg-gradient-to-br from-blue-600 to-blue-500 px-5 py-3 text-sm font-semibold leading-6 text-white"
        >
            {{ message.content }}
        </div>
        <img
            v-if="account.avatarUrl"
            class="h-10 w-10 rounded-full object-cover"
            :src="account.avatarUrl"
            alt=""
        />
        <div
            v-else
            class="grid h-10 w-10 place-items-center rounded-full bg-blue-100 text-sm font-bold text-blue-700"
        >
            {{ accountInitial }}
        </div>
        <time class="col-start-1 justify-self-end text-xs text-slate-400">{{
            message.timestamp
        }}</time>
    </article>
</template>
