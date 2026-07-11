<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  class?: string
}

const props = defineProps<Props>()

const classes = computed(() => [
  'whitespace-pre-wrap leading-relaxed font-sans relative z-10',
  props.class,
])
</script>

<template>
  <div :class="classes">
    <slot />
  </div>
</template>
