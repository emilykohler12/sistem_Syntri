<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import NavBar from '@/components/NavBar.vue'
import ToastHost from '@/components/ToastHost.vue'
import OfflineBanner from '@/components/OfflineBanner.vue'

const auth = useAuthStore()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <OfflineBanner />
    <NavBar v-if="auth.isAuthenticated" />
    <main class="flex-1">
      <router-view />
    </main>
    <ToastHost />
  </div>
</template>
