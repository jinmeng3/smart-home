<script setup lang="ts">
const model = defineModel<boolean>({ required: true })

defineProps<{
  disabled?: boolean
  small?: boolean
}>()
</script>

<template>
  <button
    :aria-checked="model"
    :class="{ active: model, small }"
    :disabled="disabled"
    class="base-switch"
    role="switch"
    type="button"
    @click="model = !model"
  >
    <span />
  </button>
</template>

<style scoped>
.base-switch {
  position: relative;
  width: 40px;
  height: 22px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: var(--color-border-default);
  transition: background-color 160ms ease;
}

.base-switch span {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: white;
  box-shadow: 0 1px 3px rgb(15 23 42 / 22%);
  transition: transform 160ms ease;
}

.base-switch.active {
  background: var(--color-primary-600);
}

.base-switch.active span {
  transform: translateX(18px);
}

.base-switch.small {
  width: 34px;
  height: 18px;
}

.base-switch.small span {
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
}

.base-switch.small.active span {
  transform: translateX(16px);
}
</style>
