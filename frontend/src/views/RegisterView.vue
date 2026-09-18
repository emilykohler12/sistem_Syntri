<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import AuthShell from '@/components/AuthShell.vue'
import PasswordInput from '@/components/PasswordInput.vue'

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const error = ref('')

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

async function handleSubmit() {
  error.value = ''

  if (password.value !== confirmPassword.value) {
    error.value = 'Las contraseñas no coinciden.'
    return
  }
  if (password.value.length < 6) {
    error.value = 'La contraseña debe tener al menos 6 caracteres.'
    return
  }

  loading.value = true
  try {
    await auth.register(email.value.trim(), password.value)
    toast.success('Cuenta creada. Ya podés iniciar sesión.')
    router.push({ name: 'login' })
  } catch (err) {
    error.value = extractErrorMessage(err, 'No se pudo registrar el usuario.')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell title="Creá tu cuenta" subtitle="Registrate para empezar a enviar notificaciones">
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <div v-if="error" class="rounded-lg bg-[var(--color-danger-soft)] text-[var(--color-danger)] text-sm px-3 py-2.5">
        {{ error }}
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="email">Correo electrónico</label>
        <input
          id="email"
          v-model="email"
          type="email"
          required
          autofocus
          placeholder="vos@ejemplo.com"
          class="input"
        />
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="password">Contraseña</label>
        <PasswordInput id="password" v-model="password" required placeholder="Mínimo 6 caracteres" autocomplete="new-password" />
      </div>

      <div class="space-y-1.5">
        <label class="text-sm font-medium text-[var(--color-text)]" for="confirm">Confirmar contraseña</label>
        <PasswordInput id="confirm" v-model="confirmPassword" required placeholder="••••••••" autocomplete="new-password" />
      </div>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? 'Creando cuenta…' : 'Registrarme' }}
      </button>

      <p class="text-center text-sm text-[var(--color-text-muted)]">
        ¿Ya tenés cuenta?
        <router-link to="/login" class="text-[var(--color-accent)] font-medium hover:underline">Iniciá sesión</router-link>
      </p>
    </form>
  </AuthShell>
</template>
