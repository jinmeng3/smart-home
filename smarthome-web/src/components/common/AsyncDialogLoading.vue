<template>
    <Teleport to="body">
        <div class="async-dialog-loading" role="status" aria-live="polite">
            <span class="async-dialog-loading-spinner" aria-hidden="true" />
            <span>正在打开</span>
        </div>
    </Teleport>
</template>

<style scoped>
.async-dialog-loading {
    position: fixed;
    inset: 0;
    z-index: 2199;
    display: grid;
    place-content: center;
    gap: 10px;
    background: color-mix(in srgb, var(--color-overlay) 72%, transparent);
    color: var(--color-card-bg);
    font-size: 13px;
    font-weight: 700;
    text-align: center;
}

.async-dialog-loading-spinner {
    width: 28px;
    height: 28px;
    margin: auto;
    border: 3px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: async-dialog-spin 600ms linear infinite;
}

@keyframes async-dialog-spin {
    to {
        transform: rotate(1turn);
    }
}
</style>
