<script setup lang="ts"></script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center gap-3 text-center px-4">
    <h1 class="text-3xl font-semibold">404</h1>
    <p class="text-[var(--color-text-muted)]">Esta página no existe.</p>
    <router-link to="/" class="text-[var(--color-accent)] hover:underline">Volver al inicio</router-link>
  </div>
</template>
