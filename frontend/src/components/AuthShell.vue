<script setup lang="ts">
import logoIcon from '@/assets/logo-icon.png'

defineProps<{
  title: string
  subtitle: string
}>()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-10 relative overflow-hidden bg-[var(--color-bg)]">
    <div
      class="pointer-events-none absolute -top-32 -left-24 h-80 w-80 rounded-full opacity-40 blur-3xl"
      style="background: radial-gradient(circle, var(--color-accent-soft), transparent 70%)"
    />
    <div
      class="pointer-events-none absolute -bottom-32 -right-16 h-96 w-96 rounded-full opacity-50 blur-3xl"
      style="background: radial-gradient(circle, var(--color-accent-soft), transparent 70%)"
    />

    <div class="relative w-full max-w-sm">
      <div class="flex flex-col items-center text-center mb-7">
        <img :src="logoIcon" alt="System Syntri" class="h-16 w-16 rounded-2xl shadow-lg shadow-black/10 mb-4" />
        <h1 class="text-2xl font-semibold text-[var(--color-text)]">{{ title }}</h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1.5">{{ subtitle }}</p>
      </div>

      <div class="card p-7">
        <slot />
      </div>

      <p class="text-center text-xs text-[var(--color-text-muted)] mt-6">
        System Syntri — notificaciones centralizadas
      </p>
    </div>
  </div>
</template>
