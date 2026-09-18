<script setup lang="ts">
const props = defineProps<{
  page: number
  limit: number
  total: number
}>()

const emit = defineEmits<{ (e: 'update:page', page: number): void }>()

function totalPages() {
  return Math.max(1, Math.ceil(props.total / props.limit))
}

function goTo(page: number) {
  const clamped = Math.min(Math.max(1, page), totalPages())
  if (clamped !== props.page) emit('update:page', clamped)
}
</script>

<template>
  <div v-if="total > 0" class="flex items-center justify-between text-sm text-[var(--color-text-muted)] pt-2">
    <span>{{ total }} resultado{{ total === 1 ? '' : 's' }} · página {{ page }} de {{ totalPages() }}</span>
    <div class="flex gap-2">
      <button
        :disabled="page <= 1"
        class="rounded-md border border-[var(--color-border)] px-3 py-1 hover:bg-[var(--color-bg)] disabled:opacity-40"
        @click="goTo(page - 1)"
      >
        Anterior
      </button>
      <button
        :disabled="page >= totalPages()"
        class="rounded-md border border-[var(--color-border)] px-3 py-1 hover:bg-[var(--color-bg)] disabled:opacity-40"
        @click="goTo(page + 1)"
      >
        Siguiente
      </button>
    </div>
  </div>
</template>
