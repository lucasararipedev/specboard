<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '../api'
import { timeAgo } from '../format'
import { PRIORITY_LABEL, STATUSES, STATUS_LABEL, type Activity, type Card } from '../types'
import MarkdownView from './MarkdownView.vue'

const props = defineProps<{ card: Card }>()
const emit = defineEmits<{ close: []; saved: [card: Card]; deleted: [id: number] }>()

const form = ref({
  title: props.card.title,
  description: props.card.description,
  status: props.card.status,
  priority: props.card.priority,
  labels: props.card.labels.join(', '),
  spec_ref: props.card.spec_ref,
  due_date: props.card.due_date ?? '',
})
const editingDescription = ref(!props.card.description)
const history = ref<Activity[]>([])
const saving = ref(false)
const error = ref('')
const copied = ref(false)

async function save() {
  saving.value = true
  error.value = ''
  try {
    const card = await api.updateCard(props.card.id, {
      title: form.value.title.trim(),
      description: form.value.description,
      status: form.value.status,
      priority: Number(form.value.priority),
      labels: form.value.labels
        .split(',')
        .map((l) => l.trim())
        .filter(Boolean),
      spec_ref: form.value.spec_ref.trim(),
      due_date: form.value.due_date || null,
    })
    emit('saved', card)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!confirm(`Apagar #${props.card.id} "${props.card.title}"? Prefira mover para Feito se foi concluído.`)) return
  await api.deleteCard(props.card.id)
  emit('deleted', props.card.id)
}

async function copyLink() {
  await navigator.clipboard.writeText(props.card.url)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(async () => {
  document.addEventListener('keydown', onKey)
  history.value = await api.activity(props.card.project, { cardId: props.card.id, limit: 30 }).catch(() => [])
})
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="backdrop" @mousedown.self="emit('close')">
    <form class="panel modal" @submit.prevent="save">
      <div class="top">
        <span class="muted small">#{{ card.id }} · criado {{ timeAgo(card.created_at) }}</span>
        <div>
          <button type="button" class="btn ghost small" @click="copyLink">{{ copied ? 'Copiado' : 'Copiar link' }}</button>
          <button type="button" class="btn ghost" aria-label="Fechar" @click="emit('close')">✕</button>
        </div>
      </div>

      <input v-model="form.title" class="title" required aria-label="Título" />

      <div class="fields">
        <label>
          Status
          <select v-model="form.status">
            <option v-for="s in STATUSES" :key="s" :value="s">{{ STATUS_LABEL[s] }}</option>
          </select>
        </label>
        <label>
          Prioridade
          <select v-model.number="form.priority">
            <option v-for="(label, p) in PRIORITY_LABEL" :key="p" :value="Number(p)">{{ label }}</option>
          </select>
        </label>
        <label>Prazo <input v-model="form.due_date" type="date" /></label>
        <label>Seção da spec <input v-model="form.spec_ref" placeholder="ex.: 2.1 Login" /></label>
        <label class="wide">Etiquetas <input v-model="form.labels" placeholder="bug, front" /></label>
      </div>

      <div class="desc">
        <div class="desc-head">
          <span class="muted small">Descrição</span>
          <button type="button" class="btn ghost small" @click="editingDescription = !editingDescription">
            {{ editingDescription ? 'Pré-visualizar' : 'Editar' }}
          </button>
        </div>
        <textarea
          v-if="editingDescription"
          v-model="form.description"
          rows="8"
          placeholder="Contexto, critérios de aceite, links (Markdown)"
        />
        <MarkdownView v-else-if="form.description" :source="form.description" class="preview" />
        <p v-else class="muted small">Sem descrição.</p>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="actions">
        <button type="button" class="btn danger" @click="remove">Apagar</button>
        <span class="spacer" />
        <button type="button" class="btn" @click="emit('close')">Cancelar</button>
        <button class="btn primary" :disabled="saving">{{ saving ? 'Salvando…' : 'Salvar' }}</button>
      </div>

      <div v-if="history.length" class="history">
        <h3 class="small muted">Histórico</h3>
        <ul>
          <li v-for="a in history" :key="a.id" class="small">
            <span class="chip" :class="{ ai: a.actor !== 'user' }">{{ a.actor }}</span>
            {{ a.message }}
            <span class="muted">· {{ timeAgo(a.created_at) }}</span>
          </li>
        </ul>
      </div>
    </form>
  </div>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 5vh 16px;
  background: rgb(38 34 30 / 32%);
  overflow-y: auto;
}

.modal {
  display: grid;
  gap: 14px;
  width: min(720px, 100%);
  padding: 18px;
}

.top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font: 500 20px var(--font-serif);
  font-variation-settings: 'SOFT' 60;
}

.fields {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.wide {
  grid-column: 1 / -1;
}

.desc {
  display: grid;
  gap: 6px;
}

.desc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
}

.actions {
  display: flex;
  gap: 8px;
}

.spacer {
  flex: 1;
}

.history ul {
  list-style: none;
  padding: 0;
  margin: 6px 0 0;
  display: grid;
  gap: 6px;
}
</style>
