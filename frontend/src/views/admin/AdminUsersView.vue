<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import { useAuthStore } from '@/stores/auth'
import type { UserMetric } from '@/types'

const toast = useToast()
const auth = useAuthStore()

const users = ref<UserMetric[]>([])
const loading = ref(false)
const actingOn = ref<string | null>(null)

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await api.get<UserMetric[]>('/api/v1/admin/metrics')
    users.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar los usuarios.'))
  } finally {
    loading.value = false
  }
}

async function promote(username: string) {
  actingOn.value = username
  try {
    await api.post('/api/v1/admin/users/promote', null, { params: { username } })
    toast.success(`'${username}' ahora es admin.`)
    await loadUsers()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo promover al usuario.'))
  } finally {
    actingOn.value = null
  }
}

async function cancel(username: string) {
  if (!confirm(`¿Cancelar la cuenta de '${username}'?`)) return
  actingOn.value = username
  try {
    await api.patch(`/api/v1/admin/users/${username}/cancel`)
    toast.success(`'${username}' fue cancelado.`)
    await loadUsers()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo cancelar al usuario.'))
  } finally {
    actingOn.value = null
  }
}

async function reactivate(username: string) {
  actingOn.value = username
  try {
    await api.patch(`/api/v1/admin/users/${username}/reactivate`)
    toast.success(`'${username}' fue reactivado.`)
    await loadUsers()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo reactivar al usuario.'))
  } finally {
    actingOn.value = null
  }
}

onMounted(loadUsers)
</script>

<template>
  <div class="space-y-4">
    <p v-if="loading" class="text-sm text-[var(--color-text-muted)]">Cargando…</p>

    <div v-else class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-x-auto">
      <table class="w-full text-sm">
        <thead class="text-left text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
          <tr>
            <th class="px-4 py-2 font-medium">Usuario</th>
            <th class="px-4 py-2 font-medium">Rol</th>
            <th class="px-4 py-2 font-medium">Estado</th>
            <th class="px-4 py-2 font-medium text-right">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.user_id" class="border-b border-[var(--color-border)] last:border-0">
            <td class="px-4 py-2 font-medium">{{ u.username }}</td>
            <td class="px-4 py-2 capitalize">{{ u.role }}</td>
            <td class="px-4 py-2">
              <span :class="u.is_active ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                {{ u.is_active ? 'Activo' : 'Cancelado' }}
              </span>
            </td>
            <td class="px-4 py-2">
              <div class="flex justify-end gap-2">
                <button
                  v-if="u.role !== 'admin'"
                  :disabled="actingOn === u.username"
                  class="rounded-md border border-[var(--color-border)] px-2.5 py-1 text-xs hover:bg-[var(--color-bg)] disabled:opacity-50"
                  @click="promote(u.username)"
                >
                  Promover
                </button>
                <button
                  v-if="u.is_active"
                  :disabled="actingOn === u.username || u.username === auth.username"
                  :title="u.username === auth.username ? 'No podés cancelar tu propia cuenta' : ''"
                  class="rounded-md border border-[var(--color-danger)]/30 text-[var(--color-danger)] px-2.5 py-1 text-xs hover:bg-[var(--color-danger-soft)] disabled:opacity-50"
                  @click="cancel(u.username)"
                >
                  Cancelar
                </button>
                <button
                  v-else
                  :disabled="actingOn === u.username"
                  class="rounded-md border border-[var(--color-success)]/30 text-[var(--color-success)] px-2.5 py-1 text-xs hover:bg-[var(--color-success-soft)] disabled:opacity-50"
                  @click="reactivate(u.username)"
                >
                  Reactivar
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!loading && users.length === 0" class="px-4 py-6 text-sm text-[var(--color-text-muted)]">
        No hay usuarios registrados.
      </p>
    </div>
  </div>
</template>
