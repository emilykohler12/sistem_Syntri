<script setup lang="ts">
import { useToast } from '@/stores/toast'

const { toasts, dismiss } = useToast()

const kindClasses: Record<string, string> = {
  success: 'bg-[var(--color-success-soft)] text-[var(--color-success)] border-[var(--color-success)]/30',
  error: 'bg-[var(--color-danger-soft)] text-[var(--color-danger)] border-[var(--color-danger)]/30',
  info: 'bg-[var(--color-accent-soft)] text-[var(--color-accent)] border-[var(--color-accent)]/30',
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="rounded-lg border px-4 py-3 text-sm shadow-md flex items-start justify-between gap-3"
      :class="kindClasses[toast.kind]"
    >
      <span>{{ toast.message }}</span>
      <button class="opacity-60 hover:opacity-100" @click="dismiss(toast.id)">✕</button>
    </div>
  </div>
</template>
