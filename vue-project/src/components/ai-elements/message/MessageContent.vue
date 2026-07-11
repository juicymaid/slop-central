<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  class?: string
}

const props = defineProps<Props>()

const classes = computed(() => [
  'flex flex-col gap-2 overflow-hidden px-4 py-3 text-sm rounded-2xl',
  'group-[.is-user]:bg-[#2A2A35] group-[.is-user]:text-[#FAF8F5] group-[.is-user]:rounded-tr-sm',
  'group-[.is-assistant]:bg-[#1A1A24] group-[.is-assistant]:border group-[.is-assistant]:border-[#2A2A35] group-[.is-assistant]:text-[#FAF8F5]/90 group-[.is-assistant]:rounded-tl-sm',
  'max-w-[85%] shadow-sm relative overflow-hidden',
  props.class,
])
</script>

<template>
  <div :class="classes">
    <div class="absolute inset-0 bg-noise opacity-5 pointer-events-none" />
    <slot />
  </div>
</template>
