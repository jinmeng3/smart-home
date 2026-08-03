<script setup lang="ts">
import type { ChatMessage } from "../../types/chat";
import AssistantMessage from "./AssistantMessage.vue";
import UserMessage from "./UserMessage.vue";

defineProps<{
    message: ChatMessage;
}>();
</script>

<template>
    <UserMessage v-if="message.role === 'user'" :message="message" />
    <AssistantMessage v-else-if="message.content.trim()" :message="message" />
</template>
