<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import type { AdminMessage, MessageFilters } from '@/types'
import StatusBadge from '@/components/StatusBadge.vue'

const toast = useToast()

const filters = reactive<MessageFilters>({
  status: '',
  service: '',
  from_date: '',
  to_date: '',
})

const messages = ref<AdminMessage[]>([])
const loading = ref(false)

async function loadMessages() {
  loading.value = true
  try {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, value]) => value),
    )
    const { data } = await api.get<AdminMessage[]>('/api/v1/admin/messages', { params })
    messages.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar los mensajes.'))
  } finally {
    loading.value = false
  }
}

onMounted(loadMessages)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-wrap gap-2">
      <select v-model="filters.status" class="rounded-md border border-[var(--color-border)] px-2 py-1.5 text-sm">
        <option value="">Todos los estados</option>
        <option value="success">Éxito</option>
        <option value="failed">Fallido</option>
        <option value="pending">Pendiente</option>
      </select>
      <select v-model="filters.service" class="rounded-md border border-[var(--color-border)] px-2 py-1.5 text-sm">
        <option value="">Todos los servicios</option>
        <option value="slack">Slack</option>
        <option value="discord">Discord</option>
      </select>
      <input v-model="filters.from_date" type="date" class="rounded-md border border-[var(--color-border)] px-2 py-1.5 text-sm" />
      <input v-model="filters.to_date" type="date" class="rounded-md border border-[var(--color-border)] px-2 py-1.5 text-sm" />
      <button class="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-[var(--color-bg)]" @click="loadMessages">
        Filtrar
      </button>
    </div>

    <p v-if="loading" class="text-sm text-[var(--color-text-muted)]">Cargando…</p>
    <p v-else-if="messages.length === 0" class="text-sm text-[var(--color-text-muted)]">No hay mensajes que coincidan.</p>

    <div v-else class="space-y-3">
      <article
        v-for="msg in messages"
        :key="msg.id"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-2"
      >
        <div class="flex items-center justify-between">
          <div>
            <span class="text-xs font-medium text-[var(--color-accent)]">{{ msg.user }}</span>
            <p class="text-sm">{{ msg.content }}</p>
          </div>
          <span class="text-xs text-[var(--color-text-muted)] whitespace-nowrap ml-4">
            {{ new Date(msg.created_at).toLocaleString() }}
          </span>
        </div>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="(delivery, i) in msg.deliveries"
            :key="i"
            class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]"
          >
            <span class="capitalize font-medium text-[var(--color-text)]">{{ delivery.service }}</span>
            <StatusBadge :status="delivery.status" />
          </div>
        </div>
      </article>
    </div>
  </div>
</template>
