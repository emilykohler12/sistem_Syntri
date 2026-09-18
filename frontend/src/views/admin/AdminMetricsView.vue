<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import type { DailyMetric, UserMetric } from '@/types'
import DailyActivityChart from '@/components/DailyActivityChart.vue'

const toast = useToast()

const userMetrics = ref<UserMetric[]>([])
const dailyMetrics = ref<DailyMetric[]>([])
const loading = ref(false)

const dateFilters = reactive({ from_date: '', to_date: '' })

async function loadMetrics() {
  loading.value = true
  try {
    const params = Object.fromEntries(
      Object.entries(dateFilters).filter(([, value]) => value),
    )
    const [usersRes, dailyRes] = await Promise.all([
      api.get<UserMetric[]>('/api/v1/admin/metrics'),
      api.get<DailyMetric[]>('/api/v1/admin/metrics/daily', { params }),
    ])
    userMetrics.value = usersRes.data
    dailyMetrics.value = dailyRes.data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar las métricas.'))
  } finally {
    loading.value = false
  }
}

onMounted(loadMetrics)
</script>

<template>
  <div class="space-y-8">
    <section class="space-y-3">
      <div class="flex items-center justify-between flex-wrap gap-2">
        <h2 class="text-lg font-semibold">Actividad diaria</h2>
        <div class="flex gap-2">
          <input v-model="dateFilters.from_date" type="date" class="rounded-md border border-[var(--color-border)] px-2 py-1.5 text-sm" />
          <input v-model="dateFilters.to_date" type="date" class="rounded-md border border-[var(--color-border)] px-2 py-1.5 text-sm" />
          <button class="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-[var(--color-bg)]" @click="loadMetrics">
            Filtrar
          </button>
        </div>
      </div>

      <div class="card p-6">
        <DailyActivityChart :data="dailyMetrics" />
      </div>
    </section>

    <section class="space-y-3">
      <h2 class="text-lg font-semibold">Por usuario</h2>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="text-left text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
            <tr>
              <th class="px-4 py-2 font-medium">Email</th>
              <th class="px-4 py-2 font-medium">Rol</th>
              <th class="px-4 py-2 font-medium">Estado</th>
              <th class="px-4 py-2 font-medium">Límite diario</th>
              <th class="px-4 py-2 font-medium">Hoy</th>
              <th class="px-4 py-2 font-medium">Restante</th>
              <th class="px-4 py-2 font-medium">Total</th>
              <th class="px-4 py-2 font-medium">Éxito / Fallo</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in userMetrics" :key="m.user_id" class="border-b border-[var(--color-border)] last:border-0">
              <td class="px-4 py-2 font-medium">{{ m.username }}</td>
              <td class="px-4 py-2 capitalize">{{ m.role }}</td>
              <td class="px-4 py-2">
                <span :class="m.is_active ? 'text-[var(--color-success)]' : 'text-[var(--color-danger)]'">
                  {{ m.is_active ? 'Activo' : 'Cancelado' }}
                </span>
              </td>
              <td class="px-4 py-2">{{ m.daily_limit }}</td>
              <td class="px-4 py-2">{{ m.messages_today }}</td>
              <td class="px-4 py-2">{{ m.remaining_today }}</td>
              <td class="px-4 py-2">{{ m.total_messages }}</td>
              <td class="px-4 py-2">
                <span class="text-[var(--color-success)]">{{ m.deliveries.successful }}</span>
                /
                <span class="text-[var(--color-danger)]">{{ m.deliveries.failed }}</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!loading && userMetrics.length === 0" class="px-4 py-6 text-sm text-[var(--color-text-muted)]">
          No hay usuarios registrados.
        </p>
      </div>
    </section>
  </div>
</template>
