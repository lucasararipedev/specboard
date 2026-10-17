<script setup lang="ts">
import { computed, nextTick, onUnmounted, ref } from 'vue'

// Filtro do board por etiquetas (tipo, área, versão…). Várias escolhidas = o card precisa ter todas.
// À vista ficam as mais usadas; o botão ao lado abre todas, com busca, para marcar várias.
const props = defineProps<{ counts: Record<string, number>; selected: string[] }>()
const emit = defineEmits<{ change: [labels: string[]] }>()

const INLINE = 5

const isOn = (label: string) => props.selected.some((s) => s.toLowerCase() === label.toLowerCase())

const ordered = computed(() =>
  Object.entries(props.counts)
    .sort(([a, na], [b, nb]) => nb - na || a.localeCompare(b, 'pt-BR', { numeric: true }))
    .map(([label]) => label),
)
// As escolhidas ficam sempre à vista, mesmo fora das mais usadas.
const inline = computed(() => {
  const top = ordered.value.slice(0, INLINE)
  return [...top, ...ordered.value.filter((l) => isOn(l) && !top.includes(l))]
})

function toggle(label: string) {
  const rest = props.selected.filter((s) => s.toLowerCase() !== label.toLowerCase())
  emit('change', isOn(label) ? rest : [...props.selected, label])
}

// ---- popup com todas ----
const open = ref(false)
const query = ref('')
const root = ref<HTMLElement>()
const search = ref<HTMLInputElement>()

const matching = computed(() => {
  const q = query.value.trim().toLowerCase()
  return q ? ordered.value.filter((l) => l.toLowerCase().includes(q)) : ordered.value
})

function onOutside(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) close()
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

async function show() {
  open.value = true
  query.value = ''
  document.addEventListener('mousedown', onOutside)
  document.addEventListener('keydown', onKey)
  await nextTick()
  search.value?.focus()
}

function close() {
  open.value = false
  document.removeEventListener('mousedown', onOutside)
  document.removeEventListener('keydown', onKey)
}

onUnmounted(close)
</script>

<template>
  <div v-if="ordered.length || selected.length" ref="root" class="label-filter" role="group" aria-label="Filtrar por etiquetas">
    <span class="muted small">Etiquetas</span>
    <button
      v-for="label in inline"
      :key="label"
      type="button"
      class="tag"
      :class="{ on: isOn(label) }"
      :aria-pressed="isOn(label)"
      @click="toggle(label)"
    >
      {{ label }} <span class="n">{{ counts[label] ?? 0 }}</span>
    </button>

    <div class="more">
      <button
        type="button"
        class="more-btn"
        :class="{ active: open }"
        :aria-expanded="open"
        aria-haspopup="true"
        :title="`Todas as etiquetas (${ordered.length})`"
        @click="open ? close() : show()"
      >
        <span class="mono">{{ ordered.length }}</span>
        <span class="caret" aria-hidden="true" />
      </button>

      <div v-if="open" class="popup" role="dialog" aria-label="Todas as etiquetas">
        <input ref="search" v-model="query" class="search" placeholder="Buscar etiqueta" />
        <ul>
          <li v-for="label in matching" :key="label">
            <label class="option">
              <input type="checkbox" :checked="isOn(label)" @change="toggle(label)" />
              <span class="mono name">{{ label }}</span>
              <span class="n">{{ counts[label] ?? 0 }}</span>
            </label>
          </li>
          <li v-if="!matching.length" class="muted small empty-list">Nenhuma etiqueta com "{{ query }}".</li>
        </ul>
        <div class="popup-foot">
          <span class="muted small">{{ selected.length > 1 ? 'Cards com todas as marcadas' : 'Marque uma ou várias' }}</span>
          <button v-if="selected.length" type="button" class="btn ghost small" @click="emit('change', [])">Limpar</button>
        </div>
      </div>
    </div>

    <template v-if="selected.length">
      <span v-if="selected.length > 1" class="muted small">com todas</span>
      <button type="button" class="btn ghost small" @click="emit('change', [])">Limpar</button>
    </template>
  </div>
</template>

<style scoped>
.label-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.label-filter > .muted:first-child {
  margin-right: 2px;
}

.tag,
.more-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  background: var(--surface);
  box-shadow: var(--shadow);
  color: var(--text);
  font: 12.5px var(--font-mono);
  cursor: pointer;
  transition:
    transform 0.15s ease-out,
    box-shadow 0.15s ease-out;
}

.tag:hover,
.more-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lift);
}

.tag.on {
  background: var(--text);
  border-color: var(--text);
  color: var(--surface);
}

.n {
  font: 11px var(--font-mono);
  color: var(--muted);
}

.tag.on .n {
  color: var(--border-strong);
}

.more {
  position: relative;
}

.more-btn {
  gap: 7px;
  padding: 3px 9px 3px 10px;
  color: var(--muted);
}

.more-btn.active {
  border-color: var(--text);
  color: var(--text);
}

/* Mesmo "v" de traço fino dos selects. */
.caret {
  width: 7px;
  height: 7px;
  margin-top: -3px;
  border-right: 1.5px solid currentColor;
  border-bottom: 1.5px solid currentColor;
  transform: rotate(45deg);
}

.popup {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 20;
  display: grid;
  gap: 8px;
  width: 260px;
  padding: 10px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-lift);
}

.search {
  padding: 6px 9px;
  font-size: 13px;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 280px;
  overflow-y: auto;
}

.option {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 5px 6px;
  border-radius: 6px;
  color: var(--text);
  cursor: pointer;
}

.option:hover {
  background: var(--surface-2);
}

.option input {
  width: auto;
  margin: 0;
  accent-color: var(--text);
}

.name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12.5px;
}

.empty-list {
  padding: 6px;
}

.popup-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}

@media (max-width: 560px) {
  .popup {
    position: fixed;
    top: auto;
    bottom: 16px;
    left: 16px;
    right: 16px;
    width: auto;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tag,
  .more-btn {
    transition: none;
  }
}
</style>
