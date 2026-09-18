<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import type { Role } from '@/types'

const toast = useToast()

const roles = ref<Role[]>([])
const loading = ref(false)
const creating = ref(false)
const deletingRole = ref<string | null>(null)

const newName = ref('')
const newDescription = ref('')

const BUILT_IN_ROLES = new Set(['user', 'admin'])

async function loadRoles() {
  loading.value = true
  try {
    const { data } = await api.get<Role[]>('/api/v1/admin/roles')
    roles.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar los roles.'))
  } finally {
    loading.value = false
  }
}

async function createRole() {
  if (!newName.value.trim()) {
    toast.error('El nombre del rol es obligatorio.')
    return
  }
  creating.value = true
  try {
    await api.post('/api/v1/admin/roles', null, {
      params: { name: newName.value.trim(), description: newDescription.value.trim() || undefined },
    })
    toast.success(`Rol '${newName.value}' creado.`)
    newName.value = ''
    newDescription.value = ''
    await loadRoles()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo crear el rol.'))
  } finally {
    creating.value = false
  }
}

async function deleteRole(name: string) {
  if (!confirm(`¿Eliminar el rol '${name}'?`)) return
  deletingRole.value = name
  try {
    await api.delete(`/api/v1/admin/roles/${name}`)
    toast.success(`Rol '${name}' eliminado.`)
    await loadRoles()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo eliminar el rol.'))
  } finally {
    deletingRole.value = null
  }
}

onMounted(loadRoles)
</script>

<template>
  <div class="space-y-6">
    <section class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 space-y-3">
      <h2 class="font-semibold text-sm">Crear rol</h2>
      <div class="flex flex-wrap gap-2">
        <input
          v-model="newName"
          placeholder="Nombre"
          class="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm flex-1 min-w-[140px]"
        />
        <input
          v-model="newDescription"
          placeholder="Descripción (opcional)"
          class="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm flex-1 min-w-[200px]"
        />
        <button
          :disabled="creating"
          class="rounded-md bg-[var(--color-accent)] text-white px-4 py-1.5 text-sm font-medium hover:bg-[var(--color-accent-hover)] disabled:opacity-60"
          @click="createRole"
        >
          Crear
        </button>
      </div>
    </section>

    <section>
      <p v-if="loading" class="text-sm text-[var(--color-text-muted)]">Cargando…</p>
      <div v-else class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="text-left text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
            <tr>
              <th class="px-4 py-2 font-medium">Nombre</th>
              <th class="px-4 py-2 font-medium">Descripción</th>
              <th class="px-4 py-2 font-medium text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="role in roles" :key="role.id" class="border-b border-[var(--color-border)] last:border-0">
              <td class="px-4 py-2 font-medium capitalize">{{ role.name }}</td>
              <td class="px-4 py-2 text-[var(--color-text-muted)]">{{ role.description ?? '—' }}</td>
              <td class="px-4 py-2 text-right">
                <button
                  v-if="!BUILT_IN_ROLES.has(role.name)"
                  :disabled="deletingRole === role.name"
                  class="rounded-md border border-[var(--color-danger)]/30 text-[var(--color-danger)] px-2.5 py-1 text-xs hover:bg-[var(--color-danger-soft)] disabled:opacity-50"
                  @click="deleteRole(role.name)"
                >
                  Eliminar
                </button>
                <span v-else class="text-xs text-[var(--color-text-muted)]">rol del sistema</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
