<script setup lang="ts">
import { computed, ref } from "vue";
import type { HomeAssistantSettings } from "../../types/settings";
import SettingsSectionCard from "./SettingsSectionCard.vue";

const props = defineProps<{
    homeAssistant: HomeAssistantSettings;
}>();

const emit = defineEmits<{
    sync: [];
}>();

const showToken = ref(false);
const connected = computed(
    () => props.homeAssistant.websocketStatus === "connected",
);
const statusClass = computed(() =>
    connected.value ? "status-online" : "status-offline",
);
const statusText = computed(() => (connected.value ? "● 已连接" : "● 未连接"));

const syncDevices = () => {
    emit("sync");
};
</script>

<template>
    <SettingsSectionCard id="homeAssistant" icon="platform" title="平台接入">
        <label class="settings-field integration-field"
            ><span class="integration-label">服务地址</span
            ><input
                v-model="homeAssistant.serviceUrl"
                class="settings-input integration-control"
        /></label>
        <label class="settings-field integration-field">
            <span class="integration-label">Access Token</span>
            <div class="integration-control relative">
                <input
                    v-model="homeAssistant.accessToken"
                    class="settings-input w-full pr-10"
                    :placeholder="
                        homeAssistant.tokenConfigured
                            ? '已配置，留空表示不修改'
                            : '请输入 Access Token'
                    "
                    :type="showToken ? 'text' : 'password'"
                />
                <button
                    class="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--color-text-tertiary)]"
                    type="button"
                    @click="showToken = !showToken"
                >
                    ●
                </button>
            </div>
        </label>
        <div class="settings-field integration-field">
            <span class="integration-label">WebSocket 状态</span>
            <span
                class="device-status-label rounded-lg px-3 py-1 text-sm font-semibold"
                :class="statusClass"
                >{{ statusText }}</span
            >
        </div>
        <button
            class="secondary-button mx-auto mt-3"
            :disabled="!connected"
            type="button"
            @click="syncDevices"
        >
            同步设备
        </button>
    </SettingsSectionCard>
</template>

<style scoped>
.integration-field {
    gap: 16px;
}

.integration-label {
    flex: 0 0 112px;
    white-space: nowrap;
}

.integration-control {
    width: auto;
    min-width: 0;
    flex: 1;
}

@media (max-width: 640px) {
    .integration-field {
        align-items: stretch;
        flex-direction: column;
        gap: 6px;
    }

    .integration-label {
        flex-basis: auto;
    }
}
</style>
