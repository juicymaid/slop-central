<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  from?: 'user' | 'assistant' | string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  from: 'assistant',
})

const classes = computed(() => [
  'group flex gap-3 w-full',
  props.from === 'user' ? 'is-user justify-end' : 'is-assistant justify-start',
  props.class,
])
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
