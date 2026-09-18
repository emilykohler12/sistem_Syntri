<script setup lang="ts">
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
        <span class="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-accent)] text-white shadow-lg shadow-[var(--color-accent)]/20 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" class="h-6 w-6">
            <path d="M4 4l16 8-16 8 4-8-4-8z" fill="currentColor" />
          </svg>
        </span>
        <h1 class="text-2xl font-semibold text-[var(--color-text)]">{{ title }}</h1>
        <p class="text-sm text-[var(--color-text-muted)] mt-1.5">{{ subtitle }}</p>
      </div>

      <div class="card p-7">
        <slot />
      </div>

      <p class="text-center text-xs text-[var(--color-text-muted)] mt-6">
        Sistem Syntri — notificaciones centralizadas a Slack y Discord
      </p>
    </div>
  </div>
</template>
