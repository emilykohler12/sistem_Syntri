<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { api, extractErrorMessage } from '@/lib/api'
import { useToast } from '@/stores/toast'
import type { AdminMessage, MessageFilters, Paginated } from '@/types'
import StatusBadge from '@/components/StatusBadge.vue'
import ServiceIcon from '@/components/ServiceIcon.vue'
import Pagination from '@/components/Pagination.vue'
import MessageFilterBar from '@/components/MessageFilterBar.vue'

const toast = useToast()

const filters = reactive<MessageFilters>({
  status: '',
  service: '',
  from_date: '',
  to_date: '',
})

const messages = ref<AdminMessage[]>([])
const loading = ref(false)
const page = ref(1)
const limit = 20
const total = ref(0)

async function loadMessages() {
  loading.value = true
  try {
    const params = {
      ...Object.fromEntries(Object.entries(filters).filter(([, value]) => value)),
      page: page.value,
      limit,
    }
    const { data } = await api.get<Paginated<AdminMessage>>('/api/v1/admin/messages', { params })
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

onMounted(loadMessages)
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <MessageFilterBar v-model="filters" />
      <span v-if="total > 0" class="text-xs text-[var(--color-text-muted)] shrink-0 ml-4">{{ total }} en total</span>
    </div>

    <p v-if="loading" class="text-sm text-[var(--color-text-muted)] py-6 text-center">Cargando…</p>
    <div v-else-if="messages.length === 0" class="card py-12 text-center">
      <p class="text-sm text-[var(--color-text-muted)]">No hay mensajes que coincidan.</p>
    </div>

    <div v-else class="space-y-3">
      <article
        v-for="msg in messages"
        :key="msg.id"
        class="card p-4 space-y-2.5"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <span class="text-xs font-medium text-[var(--color-accent)]">{{ msg.user }}</span>
            <p class="text-sm text-[var(--color-text)] leading-relaxed">{{ msg.content }}</p>
          </div>
          <span class="text-xs text-[var(--color-text-muted)] whitespace-nowrap shrink-0">
            {{ new Date(msg.created_at).toLocaleString() }}
          </span>
        </div>
        <div class="flex flex-wrap gap-3 border-t border-[var(--color-border)] -mx-4 px-4 pt-2.5">
          <div
            v-for="(delivery, i) in msg.deliveries"
            :key="i"
            class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]"
          >
            <ServiceIcon :service="delivery.service" />
            <StatusBadge :status="delivery.status" />
          </div>
        </div>
      </article>
    </div>

    <Pagination :page="page" :limit="limit" :total="total" @update:page="handlePageChange" />
  </div>
</template>
