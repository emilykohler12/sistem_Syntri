<script setup lang="ts">
import { computed, ref } from 'vue'
import type { DailyMetric } from '@/types'

const props = defineProps<{ data: DailyMetric[] }>()

const WIDTH = 720
const HEIGHT = 280
const PAD_LEFT = 40
const PAD_RIGHT = 12
const PAD_TOP = 16
const PAD_BOTTOM = 28
const GAP = 2 // surface gap entre segmentos y entre barras
const BAR_MAX = 24

const chartWidth = WIDTH - PAD_LEFT - PAD_RIGHT
const chartHeight = HEIGHT - PAD_TOP - PAD_BOTTOM

// más reciente a la derecha, como una línea de tiempo normal
const ordered = computed(() => [...props.data].sort((a, b) => a.dia.localeCompare(b.dia)))

// La barra dibuja exitosas+fallidas (intentos de entrega, no mensajes: un
// mensaje con reintentos o con varios destinos genera varias deliveries), así
// que la escala tiene que basarse en esa misma suma o la barra se sale del gráfico.
const maxTotal = computed(() =>
  Math.max(1, ...ordered.value.map((d) => d.deliveries_exitosas + d.deliveries_fallidas)),
)

function niceMax(value: number): number {
  if (value <= 5) return 5
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)))
  const normalized = value / magnitude
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10
  return step * magnitude
}

const yMax = computed(() => niceMax(maxTotal.value))

const yTicks = computed(() => {
  const steps = 4
  return Array.from({ length: steps + 1 }, (_, i) => Math.round((yMax.value / steps) * i))
})

const barSlotWidth = computed(() => chartWidth / Math.max(1, ordered.value.length))
const barWidth = computed(() => Math.max(4, Math.min(BAR_MAX, barSlotWidth.value - GAP * 2)))
const showTotalLabels = computed(() => ordered.value.length <= 14)

function yFor(value: number): number {
  return PAD_TOP + chartHeight - (value / yMax.value) * chartHeight
}

function barX(index: number): number {
  return PAD_LEFT + index * barSlotWidth.value + (barSlotWidth.value - barWidth.value) / 2
}

function formatDay(iso: string): string {
  const [, month, day] = iso.split('-')
  return `${day}/${month}`
}

const hovered = ref<number | null>(null)

function tooltipStyle(index: number) {
  const x = barX(index) + barWidth.value / 2
  const okLimit = WIDTH - PAD_RIGHT - 90
  const left = Math.min(Math.max(x - 70, PAD_LEFT), okLimit)
  return { left: `${(left / WIDTH) * 100}%`, top: '4px' }
}
</script>

<template>
  <div class="relative">
    <div class="flex items-center gap-4 mb-2 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="h-2.5 w-2.5 rounded-sm" style="background: var(--color-success)" />
        Exitosos
      </span>
      <span class="flex items-center gap-1.5">
        <span class="h-2.5 w-2.5 rounded-sm" style="background: var(--color-danger)" />
        Fallidos
      </span>
    </div>

    <p v-if="ordered.length === 0" class="text-sm text-[var(--color-text-muted)] py-10 text-center">
      Sin datos en el rango seleccionado.
    </p>

    <svg v-else :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="w-full h-auto select-none" role="img" aria-label="Mensajes exitosos y fallidos por día">
      <!-- gridlines -->
      <g>
        <line
          v-for="tick in yTicks"
          :key="tick"
          :x1="PAD_LEFT" :x2="WIDTH - PAD_RIGHT"
          :y1="yFor(tick)" :y2="yFor(tick)"
          stroke="var(--color-border)" stroke-width="1"
        />
        <text
          v-for="tick in yTicks"
          :key="'label-' + tick"
          :x="PAD_LEFT - 8" :y="yFor(tick) + 3"
          text-anchor="end" font-size="10" fill="var(--color-text-muted)"
        >{{ tick }}</text>
      </g>

      <!-- barras -->
      <g v-for="(d, i) in ordered" :key="d.dia">
        <rect
          :x="barX(i)" :width="barWidth"
          :y="yFor(d.deliveries_exitosas)" :height="Math.max(0, yFor(0) - yFor(d.deliveries_exitosas))"
          fill="var(--color-success)"
          :rx="d.deliveries_fallidas === 0 ? 4 : 0" :ry="d.deliveries_fallidas === 0 ? 4 : 0"
        />
        <rect
          v-if="d.deliveries_fallidas > 0"
          :x="barX(i)" :width="barWidth"
          :y="yFor(d.deliveries_exitosas + d.deliveries_fallidas) + (d.deliveries_exitosas > 0 ? GAP : 0)"
          :height="Math.max(0, yFor(d.deliveries_exitosas) - yFor(d.deliveries_exitosas + d.deliveries_fallidas) - (d.deliveries_exitosas > 0 ? GAP : 0))"
          fill="var(--color-danger)" rx="4" ry="4"
        />

        <text
          v-if="showTotalLabels"
          :x="barX(i) + barWidth / 2" :y="yFor(d.deliveries_exitosas + d.deliveries_fallidas) - 6"
          text-anchor="middle" font-size="10" fill="var(--color-text-muted)"
        >{{ d.deliveries_exitosas + d.deliveries_fallidas }}</text>

        <text
          :x="barX(i) + barWidth / 2" :y="HEIGHT - PAD_BOTTOM + 14"
          text-anchor="middle" font-size="10" fill="var(--color-text-muted)"
        >{{ formatDay(d.dia) }}</text>

        <!-- hit target invisible, más ancho que la barra para hover cómodo -->
        <rect
          :x="PAD_LEFT + i * barSlotWidth" :width="barSlotWidth"
          :y="PAD_TOP" :height="chartHeight"
          fill="transparent"
          @mouseenter="hovered = i"
          @mouseleave="hovered = null"
        />
      </g>

      <!-- eje base -->
      <line :x1="PAD_LEFT" :x2="WIDTH - PAD_RIGHT" :y1="yFor(0)" :y2="yFor(0)" stroke="var(--color-text-muted)" stroke-width="1" />
    </svg>

    <div
      v-if="hovered !== null"
      class="absolute pointer-events-none card px-3 py-2 text-xs shadow-md"
      :style="tooltipStyle(hovered)"
    >
      <p class="font-medium text-[var(--color-text)] mb-1">{{ ordered[hovered].dia }}</p>
      <p class="text-[var(--color-success)]">Exitosos: {{ ordered[hovered].deliveries_exitosas }}</p>
      <p class="text-[var(--color-danger)]">Fallidos: {{ ordered[hovered].deliveries_fallidas }}</p>
      <p class="text-[var(--color-text-muted)] mt-1 pt-1 border-t border-[var(--color-border)]">
        {{ ordered[hovered].total_mensajes }} mensaje{{ ordered[hovered].total_mensajes === 1 ? '' : 's' }} enviado{{ ordered[hovered].total_mensajes === 1 ? '' : 's' }}
      </p>
    </div>
  </div>
</template>
