<script setup lang="ts">
import { computed } from 'vue'
import type { MessageFilters } from '@/types'

const filters = defineModel<MessageFilters>({ required: true })

const hasActiveFilters = computed(() =>
  Object.values(filters.value).some((value) => !!value),
)

function clearFilters() {
  // Mutamos las propiedades en vez de reemplazar el objeto: el padre pasa un
  // objeto reactive() por v-model, y reasignarlo entero no se propaga porque
  // "filters" es una const ahí (no un ref reasignable).
  filters.value.status = ''
  filters.value.service = ''
  filters.value.from_date = ''
  filters.value.to_date = ''
}
</script>

<template>
  <div class="flex flex-wrap items-end gap-3">
    <div class="space-y-1">
      <label class="block text-xs font-medium text-[var(--color-text-muted)]">Estado</label>
      <select v-model="filters.status" class="input py-1.5">
        <option value="">Todos</option>
        <option value="success">Éxito</option>
        <option value="failed">Fallido</option>
        <option value="pending">Pendiente</option>
      </select>
    </div>

    <div class="space-y-1">
      <label class="block text-xs font-medium text-[var(--color-text-muted)]">Servicio</label>
      <select v-model="filters.service" class="input py-1.5">
        <option value="">Todos</option>
        <option value="slack">Slack</option>
        <option value="discord">Discord</option>
        <option value="telegram">Telegram</option>
      </select>
    </div>

    <div class="space-y-1">
      <label class="block text-xs font-medium text-[var(--color-text-muted)]">Desde</label>
      <input v-model="filters.from_date" type="date" class="input py-1.5" />
    </div>

    <div class="space-y-1">
      <label class="block text-xs font-medium text-[var(--color-text-muted)]">Hasta</label>
      <input v-model="filters.to_date" type="date" class="input py-1.5" />
    </div>

    <button
      v-if="hasActiveFilters"
      type="button"
      class="rounded-md border border-[var(--color-border)] px-3 py-1.5 text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-bg)] hover:text-[var(--color-text)]"
      @click="clearFilters"
    >
      Eliminar filtros
    </button>
  </div>
</template>
