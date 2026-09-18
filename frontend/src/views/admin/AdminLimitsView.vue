<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import type { AuditRecord, LimitsResponse } from '@/types'

const toast = useToast()

const limits = ref<LimitsResponse | null>(null)
const audit = ref<AuditRecord[]>([])
const loading = ref(false)

const globalLimitInput = ref<number | null>(null)
const savingGlobal = ref(false)

const userLimitDrafts = ref<Record<string, string>>({})
const savingUser = ref<string | null>(null)

async function loadAll() {
  loading.value = true
  try {
    const [limitsRes, auditRes] = await Promise.all([
      api.get<LimitsResponse>('/api/v1/admin/limits'),
      api.get<AuditRecord[]>('/api/v1/admin/limits/audit'),
    ])
    limits.value = limitsRes.data
    globalLimitInput.value = limitsRes.data.global_limit
    userLimitDrafts.value = Object.fromEntries(
      limitsRes.data.users.map((u) => [u.username, u.custom_limit != null ? String(u.custom_limit) : '']),
    )
    audit.value = auditRes.data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar los límites.'))
  } finally {
    loading.value = false
  }
}

async function saveGlobalLimit() {
  if (!globalLimitInput.value || globalLimitInput.value < 1) {
    toast.error('El límite debe ser mayor a 0.')
    return
  }
  savingGlobal.value = true
  try {
    await api.patch('/api/v1/admin/limits/global', null, { params: { new_limit: globalLimitInput.value } })
    toast.success('Límite global actualizado.')
    await loadAll()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo actualizar el límite global.'))
  } finally {
    savingGlobal.value = false
  }
}

async function saveUserLimit(username: string) {
  const raw = userLimitDrafts.value[username]?.trim()
  const newLimit = raw ? Number(raw) : null

  if (newLimit !== null && (Number.isNaN(newLimit) || newLimit < 1)) {
    toast.error('El límite debe ser mayor a 0.')
    return
  }

  savingUser.value = username
  try {
    await api.patch(`/api/v1/admin/limits/user/${username}`, null, {
      params: newLimit !== null ? { new_limit: newLimit } : {},
    })
    toast.success(`Límite de '${username}' actualizado.`)
    await loadAll()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo actualizar el límite del usuario.'))
  } finally {
    savingUser.value = null
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="space-y-8">
    <p v-if="loading && !limits" class="text-sm text-[var(--color-text-muted)]">Cargando…</p>

    <template v-else-if="limits">
      <section class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 space-y-3">
        <h2 class="font-semibold text-sm">Límite global diario</h2>
        <div class="flex items-center gap-2">
          <input
            v-model.number="globalLimitInput"
            type="number"
            min="1"
            class="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm w-32"
          />
          <button
            :disabled="savingGlobal"
            class="rounded-md bg-[var(--color-accent)] text-white px-4 py-1.5 text-sm font-medium hover:bg-[var(--color-accent-hover)] disabled:opacity-60"
            @click="saveGlobalLimit"
          >
            Guardar
          </button>
        </div>
      </section>

      <section class="space-y-3">
        <h2 class="text-lg font-semibold">Límites por usuario</h2>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-left text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <tr>
                <th class="px-4 py-2 font-medium">Usuario</th>
                <th class="px-4 py-2 font-medium">Límite efectivo</th>
                <th class="px-4 py-2 font-medium">Límite personalizado</th>
                <th class="px-4 py-2 font-medium text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in limits.users" :key="u.user_id" class="border-b border-[var(--color-border)] last:border-0">
                <td class="px-4 py-2 font-medium">{{ u.username }}</td>
                <td class="px-4 py-2">{{ u.effective_limit }}</td>
                <td class="px-4 py-2">
                  <input
                    v-model="userLimitDrafts[u.username]"
                    type="number"
                    min="1"
                    placeholder="usa el global"
                    class="rounded-md border border-[var(--color-border)] px-2 py-1 text-sm w-32"
                  />
                </td>
                <td class="px-4 py-2 text-right">
                  <button
                    :disabled="savingUser === u.username"
                    class="rounded-md border border-[var(--color-border)] px-2.5 py-1 text-xs hover:bg-[var(--color-bg)] disabled:opacity-50"
                    @click="saveUserLimit(u.username)"
                  >
                    Guardar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="space-y-3">
        <h2 class="text-lg font-semibold">Historial de cambios</h2>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="text-left text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
              <tr>
                <th class="px-4 py-2 font-medium">Cambiado por</th>
                <th class="px-4 py-2 font-medium">Objetivo</th>
                <th class="px-4 py-2 font-medium">Antes</th>
                <th class="px-4 py-2 font-medium">Después</th>
                <th class="px-4 py-2 font-medium">Cuándo</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(a, i) in audit" :key="i" class="border-b border-[var(--color-border)] last:border-0">
                <td class="px-4 py-2">{{ a.changed_by }}</td>
                <td class="px-4 py-2 capitalize">{{ a.target }}</td>
                <td class="px-4 py-2">{{ a.old_limit }}</td>
                <td class="px-4 py-2">{{ a.new_limit }}</td>
                <td class="px-4 py-2 text-[var(--color-text-muted)]">{{ new Date(a.changed_at).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="audit.length === 0" class="px-4 py-6 text-sm text-[var(--color-text-muted)]">
            Todavía no hay cambios registrados.
          </p>
        </div>
      </section>
    </template>
  </div>
</template>
