<script setup lang="ts">
import SvgIcon from "../common/SvgIcon.vue";
import { platformIconMap } from "./deviceMeta";

const platformToneMap: Record<string, string> = {
    "Home Assistant": "orange",
    Matter: "blue",
    Zigbee: "green",
    MQTT: "purple",
};

defineProps<{
    platforms: {
        name: string;
        status: string;
        connected: boolean;
    }[];
}>();
</script>

<template>
    <section class="device-side-card">
        <h2>接入平台</h2>
        <div class="platform-list">
            <article
                v-for="platform in platforms"
                :key="platform.name"
                :class="{ 'is-connected': platform.connected }"
            >
                <span
                    class="platform-icon tone-chip"
                    :class="`is-${platformToneMap[platform.name] ?? 'blue'}`"
                >
                    <SvgIcon
                        :name="platformIconMap[platform.name] ?? 'layers'"
                        size="sm"
                    />
                </span>
                <strong>{{ platform.name }}</strong>
                <em
                    class="platform-status"
                    :class="{ 'is-connected': platform.connected }"
                >
                    <i></i>
                    {{ platform.status }}
                </em>
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
    gap: 8px;
}

article {
    display: grid;
    grid-template-columns: 30px minmax(0, 1fr) auto;
    align-items: center;
    gap: 9px;
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 8px 9px;
    background: var(--color-panel-secondary);
    transition:
        border-color 160ms var(--motion-ease),
        box-shadow 160ms var(--motion-ease),
        transform 160ms var(--motion-ease);
}

article.is-connected {
    border-color: var(--color-success-border);
    background: var(--color-success-soft);
}

article:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-1px);
}

.platform-icon {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border-radius: 8px;
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

.platform-status {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border-radius: 999px;
    padding: 3px 9px;
    color: var(--color-text-tertiary);
    background: var(--color-surface-subtle);
    font-size: 11px;
    font-style: normal;
    font-weight: 900;
}

.platform-status i {
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: currentColor;
}

.platform-status.is-connected {
    background: var(--color-success-soft);
    color: var(--color-success);
}

@media (prefers-reduced-motion: reduce) {
    article {
        transition-duration: 1ms;
    }

    article:hover {
        transform: none;
    }
}
</style>
