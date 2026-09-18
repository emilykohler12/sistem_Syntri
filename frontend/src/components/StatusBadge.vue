<script setup lang="ts">
defineProps<{ status: string }>()

const classesByStatus: Record<string, string> = {
  success: 'bg-[var(--color-success-soft)] text-[var(--color-success)]',
  failed: 'bg-[var(--color-danger-soft)] text-[var(--color-danger)]',
  pending: 'bg-[var(--color-warning-soft)] text-[var(--color-warning)]',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize"
    :class="classesByStatus[status] ?? 'bg-gray-100 text-gray-600'"
  >
    {{ status }}
  </span>
</template>
