<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import { AVAILABLE_DESTINATIONS, type Message, type MessageFilters } from '@/types'
import StatusBadge from '@/components/StatusBadge.vue'

const toast = useToast()

const content = ref('')
const selectedDestinations = ref<string[]>(['slack'])
const sending = ref(false)

const filters = reactive<MessageFilters>({
  status: '',
  service: '',
  from_date: '',
  to_date: '',
})

const messages = ref<Message[]>([])
const loading = ref(false)

function toggleDestination(dest: string) {
  const idx = selectedDestinations.value.indexOf(dest)
  if (idx === -1) {
    selectedDestinations.value.push(dest)
  } else {
    selectedDestinations.value.splice(idx, 1)
  }
}

async function loadMessages() {
  loading.value = true
  try {
    const params = Object.fromEntries(
      Object.entries(filters).filter(([, value]) => value),
    )
    const { data } = await api.get<Message[]>('/api/v1/messages/', { params })
    messages.value = data
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar los mensajes.'))
  } finally {
    loading.value = false
  }
}

async function handleSend() {
  if (!content.value.trim()) {
    toast.error('El mensaje no puede estar vacío.')
    return
  }
  if (selectedDestinations.value.length === 0) {
    toast.error('Elegí al menos un destino.')
    return
  }

  sending.value = true
  try {
    const { data } = await api.post<Message>('/api/v1/messages/', {
      content: content.value,
      destinations: selectedDestinations.value,
    })
    const summary = data.deliveries
      .map((d) => `${d.service}: ${d.status === 'success' ? 'enviado' : 'falló'}`)
      .join(' · ')
    const anyFailed = data.deliveries.some((d) => d.status !== 'success')
    if (anyFailed) {
      toast.error(`Mensaje guardado con errores → ${summary}`)
    } else {
      toast.success(`Mensaje enviado → ${summary}`)
    }
    content.value = ''
    await loadMessages()
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudo enviar el mensaje.'))
  } finally {
    sending.value = false
  }
}

onMounted(loadMessages)
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-8 space-y-8">
    <section class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6 shadow-sm space-y-4">
      <h2 class="text-lg font-semibold">Enviar mensaje</h2>

      <textarea
        v-model="content"
        rows="3"
        placeholder="Escribí tu mensaje…"
        class="w-full rounded-md border border-[var(--color-border)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/40"
      />

      <div class="flex items-center gap-4">
        <span class="text-sm font-medium text-[var(--color-text-muted)]">Destinos:</span>
        <label
          v-for="dest in AVAILABLE_DESTINATIONS"
          :key="dest"
          class="flex items-center gap-2 text-sm cursor-pointer capitalize"
        >
          <input
            type="checkbox"
            :checked="selectedDestinations.includes(dest)"
            @change="toggleDestination(dest)"
          />
          {{ dest }}
        </label>
      </div>

      <button
        :disabled="sending"
        class="rounded-md bg-[var(--color-accent)] text-white px-4 py-2 text-sm font-medium hover:bg-[var(--color-accent-hover)] disabled:opacity-60"
        @click="handleSend"
      >
        {{ sending ? 'Enviando…' : 'Enviar' }}
      </button>
    </section>

    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">Mis mensajes</h2>
      </div>

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
        <button
          class="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-[var(--color-surface)]"
          @click="loadMessages"
        >
          Filtrar
        </button>
      </div>

      <p v-if="loading" class="text-sm text-[var(--color-text-muted)]">Cargando…</p>
      <p v-else-if="messages.length === 0" class="text-sm text-[var(--color-text-muted)]">Todavía no enviaste mensajes.</p>

      <div v-else class="space-y-3">
        <article
          v-for="msg in messages"
          :key="msg.id"
          class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 space-y-2"
        >
          <div class="flex items-center justify-between">
            <p class="text-sm">{{ msg.content }}</p>
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
              <span v-if="delivery.attempt > 1">(intento {{ delivery.attempt }})</span>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
