<script setup lang="ts">
const props = defineProps<{ service: string }>()

const colors: Record<string, { bg: string; text: string }> = {
  slack: { bg: '#4A154B1a', text: '#4A154B' },
  discord: { bg: '#5865F21a', text: '#5865F2' },
}

function style() {
  const c = colors[props.service] ?? { bg: 'var(--color-bg)', text: 'var(--color-text-muted)' }
  return { backgroundColor: c.bg, color: c.text }
}
</script>

<template>
  <span
    class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[10px] font-bold uppercase"
    :style="style()"
  >
    {{ service.slice(0, 2) }}
  </span>
</template>
