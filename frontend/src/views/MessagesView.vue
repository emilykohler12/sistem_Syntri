<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import { AVAILABLE_DESTINATIONS, type Message, type MessageFilters, type Paginated } from '@/types'
import StatusBadge from '@/components/StatusBadge.vue'
import ServiceIcon from '@/components/ServiceIcon.vue'
import Pagination from '@/components/Pagination.vue'
import MessageFilterBar from '@/components/MessageFilterBar.vue'

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
const page = ref(1)
const limit = 20
const total = ref(0)

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
    const params = {
      ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value)),
      page: page.value,
      limit,
    }
    const { data } = await api.get<Paginated<Message>>('/api/v1/messages/', { params })
    messages.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error(extractErrorMessage(err, 'No se pudieron cargar los mensajes.'))
  } finally {
    loading.value = false
  }
}

watch(
  filters,
  () => {
    page.value = 1
    loadMessages()
  },
  { deep: true },
)

function handlePageChange(newPage: number) {
  page.value = newPage
  loadMessages()
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
    page.value = 1
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
  <div class="max-w-3xl mx-auto px-4 py-8 space-y-6">
    <section class="card p-6 space-y-4">
      <div>
        <h2 class="text-base font-semibold text-[var(--color-text)]">Enviar mensaje</h2>
        <p class="text-sm text-[var(--color-text-muted)]">Se envía firmado con tu cuenta a los destinos que elijas.</p>
      </div>

      <textarea
        v-model="content"
        rows="3"
        placeholder="Escribí tu mensaje…"
        class="input resize-none"
      />

      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="dest in AVAILABLE_DESTINATIONS"
          :key="dest"
          type="button"
          class="flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm capitalize transition-colors"
          :class="selectedDestinations.includes(dest)
            ? 'border-[var(--color-accent)] bg-[var(--color-accent-soft)] text-[var(--color-accent)] font-medium'
            : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-[var(--color-bg)]'"
          @click="toggleDestination(dest)"
        >
          <ServiceIcon :service="dest" />
          {{ dest }}
        </button>
      </div>

      <div class="flex justify-end">
        <button :disabled="sending" class="btn-primary" @click="handleSend">
          {{ sending ? 'Enviando…' : 'Enviar' }}
        </button>
      </div>
    </section>

    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-base font-semibold text-[var(--color-text)]">Mis mensajes</h2>
        <span v-if="total > 0" class="text-xs text-[var(--color-text-muted)]">{{ total }} en total</span>
      </div>

      <MessageFilterBar v-model="filters" />

      <p v-if="loading" class="text-sm text-[var(--color-text-muted)] py-6 text-center">Cargando…</p>
      <div v-else-if="messages.length === 0" class="card py-12 text-center">
        <p class="text-sm text-[var(--color-text-muted)]">Todavía no hay mensajes que coincidan.</p>
      </div>

      <div v-else class="space-y-3">
        <article
          v-for="msg in messages"
          :key="msg.id"
          class="card p-4 space-y-2.5"
        >
          <div class="flex items-start justify-between gap-4">
            <p class="text-sm text-[var(--color-text)] leading-relaxed">{{ msg.content }}</p>
            <span class="text-xs text-[var(--color-text-muted)] whitespace-nowrap shrink-0">
              {{ new Date(msg.created_at).toLocaleString() }}
            </span>
          </div>
          <div class="flex flex-wrap gap-3 pt-1 border-t border-[var(--color-border)] -mx-4 px-4 pt-2.5">
            <div
              v-for="(delivery, i) in msg.deliveries"
              :key="i"
              class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]"
            >
              <ServiceIcon :service="delivery.service" />
              <StatusBadge :status="delivery.status" />
              <span v-if="delivery.attempt > 1">(intento {{ delivery.attempt }})</span>
            </div>
          </div>
        </article>
      </div>

      <Pagination :page="page" :limit="limit" :total="total" @update:page="handlePageChange" />
    </section>
  </div>
</template>
