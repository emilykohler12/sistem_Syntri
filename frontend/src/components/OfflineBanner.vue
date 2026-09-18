<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

const isOnline = ref(navigator.onLine)

function updateStatus() {
  isOnline.value = navigator.onLine
}

onMounted(() => {
  window.addEventListener('online', updateStatus)
  window.addEventListener('offline', updateStatus)
})

onUnmounted(() => {
  window.removeEventListener('online', updateStatus)
  window.removeEventListener('offline', updateStatus)
})
</script>

<template>
  <div
    v-if="!isOnline"
    class="fixed top-3 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 rounded-full bg-[var(--color-danger)] text-white text-sm font-medium px-4 py-2 shadow-lg"
  >
    <span class="h-2 w-2 rounded-full bg-white animate-pulse" />
    Sin conexión a internet
  </div>
</template>
