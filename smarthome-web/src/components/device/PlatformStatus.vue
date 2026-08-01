<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";

defineProps<{
    platforms: {
        name: string;
        status: string;
        connected: boolean;
    }[];
}>();

const iconMap: Record<string, string> = {
    "Home Assistant": "home-assistant",
    Matter: "matter",
    Zigbee: "zigbee",
    MQTT: "mqtt",
};
</script>

<template>
    <section class="device-side-card">
        <h2>接入平台</h2>
        <div class="platform-list">
            <article v-for="platform in platforms" :key="platform.name">
                <span class="platform-icon">
                    <SvgIcon :name="iconMap[platform.name] ?? 'layers'" size="sm" />
                </span>
                <strong>{{ platform.name }}</strong>
                <em>{{ platform.status }}</em>
                <i :class="{ 'is-connected': platform.connected }"></i>
            </article>
        </div>
    </section>
</template>

<style scoped>
.device-side-card {
    border: 1px solid var(--color-border-default);
    border-radius: 12px;
    background: var(--color-panel-background);
    padding: 14px;
    box-shadow: var(--shadow-card);
}

h2 {
    margin: 0 0 12px;
    font-size: 16px;
    font-weight: 900;
}

.platform-list {
    display: grid;
    gap: 9px;
}

article {
    display: grid;
    grid-template-columns: 30px minmax(0, 1fr) auto 8px;
    align-items: center;
    gap: 9px;
    border-radius: 8px;
    padding: 8px 6px;
    background: var(--color-panel-secondary);
}

.platform-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
    background: var(--color-primary-100);
    color: var(--color-primary-700);
    font-size: 12px;
    font-weight: 900;
}

strong {
    overflow: hidden;
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 900;
    text-overflow: ellipsis;
    white-space: nowrap;
}

em {
    color: var(--color-text-tertiary);
    font-size: 12px;
    font-style: normal;
    font-weight: 800;
}

i {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--color-text-muted);
}

i.is-connected {
    background: var(--color-success);
}
</style>
