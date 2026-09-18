<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  id?: string
  placeholder?: string
  required?: boolean
  autocomplete?: string
}>()

const model = defineModel<string>({ required: true })

const visible = ref(false)
</script>

<template>
  <div class="relative">
    <input
      :id="id"
      v-model="model"
      :type="visible ? 'text' : 'password'"
      :placeholder="placeholder"
      :required="required"
      :autocomplete="autocomplete"
      class="input pr-10"
    />
    <button
      type="button"
      tabindex="-1"
      class="absolute inset-y-0 right-0 flex items-center px-3 text-[var(--color-text-muted)] hover:text-[var(--color-text)]"
      :aria-label="visible ? 'Ocultar contraseña' : 'Mostrar contraseña'"
      @click="visible = !visible"
    >
      <svg v-if="visible" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" class="h-4.5 w-4.5">
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
        <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.6" />
      </svg>
      <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" class="h-4.5 w-4.5">
        <path d="M3 3l18 18M10.6 10.6a3 3 0 004.24 4.24M9.9 5.1A10.9 10.9 0 0112 5c6.5 0 10 7 10 7a13.2 13.2 0 01-3.15 3.9M6.5 6.6C4.2 8.1 2 12 2 12a13.3 13.3 0 004.15 4.6"
          stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </button>
  </div>
</template>
