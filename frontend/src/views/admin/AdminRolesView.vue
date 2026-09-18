<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import type { Permission, Role } from '@/types'

const toast = useToast()

const roles = ref<Role[]>([])
const permissions = ref<Permission[]>([])
const loading = ref(false)
const creating = ref(false)
const deletingRole = ref<string | null>(null)
const savingRole = ref<string | null>(null)

const newName = ref('')
const newDescription = ref('')

// borrador de checkboxes por rol, para no pegarle al backend en cada click
const drafts = reactive<Record<string, string[]>>({})

const BUILT_IN_ROLES = new Set(['user', 'admin'])

async function loadRoles() {
  loading.value = true
  try {
    const [rolesRes, permsRes] = await Promise.all([
      api.get<Role[]>('/api/v1/admin/roles'),
      api.get<Permission[]>('/api/v1/admin/permissions'),
    ])
    roles.value = rolesRes.data
    permissions.value = permsRes.data
    for (const role of rolesRes.data) {
      drafts[role.name] = [...role.permissions]
    }
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar los roles.'))
  } finally {
    loading.value = false
  }
}

function togglePermission(roleName: string, key: string) {
  const current = drafts[roleName] ?? []
  drafts[roleName] = current.includes(key)
    ? current.filter((p) => p !== key)
    : [...current, key]
}

function hasUnsavedChanges(role: Role) {
  const draft = drafts[role.name] ?? []
  return draft.length !== role.permissions.length || draft.some((p) => !role.permissions.includes(p))
}

async function savePermissions(roleName: string) {
  savingRole.value = roleName
  try {
    await api.patch(`/api/v1/admin/roles/${roleName}/permissions`, { permissions: drafts[roleName] ?? [] })
    toast.success(`Permisos de '${roleName}' actualizados.`)
    await loadRoles()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron guardar los permisos.'))
  } finally {
    savingRole.value = null
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
    <section class="card p-5 space-y-3">
      <h2 class="font-semibold text-sm">Crear rol</h2>
      <div class="flex flex-wrap gap-2">
        <input v-model="newName" placeholder="Nombre" class="input flex-1 min-w-[140px]" />
        <input v-model="newDescription" placeholder="Descripción (opcional)" class="input flex-1 min-w-[200px]" />
        <button :disabled="creating" class="btn-primary" @click="createRole">
          Crear
        </button>
      </div>
    </section>

    <section class="space-y-3">
      <p v-if="loading" class="text-sm text-[var(--color-text-muted)]">Cargando…</p>

      <div v-else v-for="role in roles" :key="role.id" class="card p-5 space-y-3">
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3 class="font-semibold capitalize">{{ role.name }}</h3>
            <p class="text-xs text-[var(--color-text-muted)]">{{ role.description ?? 'Sin descripción' }}</p>
          </div>
          <button
            v-if="!BUILT_IN_ROLES.has(role.name)"
            :disabled="deletingRole === role.name"
            class="rounded-md border border-[var(--color-danger)]/30 text-[var(--color-danger)] px-2.5 py-1 text-xs hover:bg-[var(--color-danger-soft)] disabled:opacity-50 shrink-0"
            @click="deleteRole(role.name)"
          >
            Eliminar rol
          </button>
          <span v-else class="text-xs text-[var(--color-text-muted)] shrink-0">rol del sistema</span>
        </div>

        <div>
          <p class="text-xs font-medium text-[var(--color-text-muted)] mb-2">Acceso al panel de administración</p>

          <p v-if="role.name === 'admin'" class="text-sm text-[var(--color-text-muted)]">
            Acceso total a todas las secciones. No se puede editar.
          </p>

          <div v-else class="flex flex-wrap items-center gap-4">
            <label
              v-for="perm in permissions"
              :key="perm.key"
              class="flex items-center gap-1.5 text-sm cursor-pointer"
            >
              <input
                type="checkbox"
                :checked="(drafts[role.name] ?? []).includes(perm.key)"
                @change="togglePermission(role.name, perm.key)"
              />
              {{ perm.label }}
            </label>

            <button
              v-if="hasUnsavedChanges(role)"
              :disabled="savingRole === role.name"
              class="btn-primary text-xs !py-1.5 !px-3"
              @click="savePermissions(role.name)"
            >
              Guardar
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
