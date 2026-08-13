<script setup lang="ts">
import type { ChatMessage } from "../../types/chat";
import AssistantMessage from "./AssistantMessage.vue";
import UserMessage from "./UserMessage.vue";

const props = defineProps<{
    message: ChatMessage;
    streaming?: boolean;
    generating?: boolean;
    regenerating?: boolean;
}>();

const emit = defineEmits<{
    regenerate: [messageId: string];
}>();
</script>

<template>
    <UserMessage v-if="message.role === 'user'" :message="message" />
    <AssistantMessage
        v-else-if="message.content.trim()"
        :message="message"
        :streaming="streaming"
        :generating="generating"
        :regenerating="regenerating"
        @regenerate="$emit('regenerate', $event)"
    />
</template>
