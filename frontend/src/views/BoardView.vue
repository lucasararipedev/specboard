<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { formatDate, isOverdue, timeAgo } from '../format'
import { STATUSES, STATUS_LABEL, type Activity, type Card, type ProjectDetail, type Status } from '../types'
import CardModal from '../components/CardModal.vue'
import MarkdownView from '../components/MarkdownView.vue'

const props = defineProps<{ slug: string }>()
const route = useRoute()
const router = useRouter()

// A IA mexe no board pela API; a tela busca de novo a cada 5 s para mostrar as mudanças.
const POLL_MS = 5000
const DONE_VISIBLE = 15

type Tab = 'board' | 'spec' | 'activity'
const tab = ref<Tab>('board')
const project = ref<ProjectDetail | null>(null)
const cards = ref<Card[]>([])
const activity = ref<Activity[]>([])
const loading = ref(true)
const error = ref('')

const columns = computed(() => {
  const byStatus = Object.fromEntries(STATUSES.map((s) => [s, [] as Card[]])) as Record<Status, Card[]>
  for (const card of cards.value) byStatus[card.status].push(card)
  for (const s of STATUSES) byStatus[s].sort((a, b) => a.position - b.position)
  // Feito: mais recente em cima.
  byStatus.done.sort((a, b) => (b.done_at ?? '').localeCompare(a.done_at ?? ''))
  return byStatus
})
const showAllDone = ref(false)

// ---- carregamento ----
async function loadCards() {
  cards.value = await api.cards(props.slug)
}

async function loadActivity() {
  activity.value = await api.activity(props.slug, { limit: 100 })
}

async function loadAll() {
  error.value = ''
  try {
    const [p] = await Promise.all([api.project(props.slug), loadCards(), loadActivity()])
    project.value = p
    if (!editingSpec.value) specDraft.value = p.spec
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

let timer: number | undefined
async function poll() {
  if (document.hidden || dragging.value || saving.value) return
  try {
    await Promise.all([loadCards(), loadActivity()])
    if (tab.value === 'spec' && !editingSpec.value) {
      project.value = await api.project(props.slug)
      specDraft.value = project.value.spec
    }
  } catch {
    // erro de rede passageiro: tenta de novo no próximo ciclo
  }
}

onMounted(() => {
  loadAll()
  timer = window.setInterval(poll, POLL_MS)
})
onUnmounted(() => window.clearInterval(timer))
watch(
  () => props.slug,
  () => {
    loading.value = true
    loadAll()
  },
)

// ---- card aberto (?card=<id>, o link que a IA manda) ----
const openCard = computed(() => {
  const id = Number(route.query.card)
  return id ? (cards.value.find((c) => c.id === id) ?? null) : null
})

function showCard(id: number) {
  router.push({ query: { ...route.query, card: String(id) } })
}

function closeCard() {
  const { card: _, ...rest } = route.query
  router.push({ query: rest })
}

function onSaved(card: Card) {
  cards.value = cards.value.map((c) => (c.id === card.id ? card : c))
  closeCard()
  loadActivity()
}

function onDeleted(id: number) {
  cards.value = cards.value.filter((c) => c.id !== id)
  closeCard()
  loadActivity()
}

// ---- criação rápida ----
const adding = ref<Status | null>(null)
const newTitle = ref('')
const saving = ref(false)

async function addCard(status: Status) {
  const title = newTitle.value.trim()
  if (!title) return
  saving.value = true
  try {
    const card = await api.createCard(props.slug, { title, status })
    cards.value.push(card)
    newTitle.value = ''
    loadActivity()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

// ---- arrastar e soltar ----
const dragging = ref<Card | null>(null)
const dropAt = ref<{ status: Status; index: number } | null>(null)

function onDragStart(card: Card, e: DragEvent) {
  dragging.value = card
  e.dataTransfer?.setData('text/plain', String(card.id))
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onDragOver(status: Status, e: DragEvent) {
  if (!dragging.value) return
  e.preventDefault()
  const list = e.currentTarget as HTMLElement
  const items = [...list.querySelectorAll<HTMLElement>('[data-card]')].filter(
    (el) => Number(el.dataset.card) !== dragging.value!.id,
  )
  let index = items.findIndex((el) => {
    const box = el.getBoundingClientRect()
    return e.clientY < box.top + box.height / 2
  })
  if (index === -1) index = items.length
  dropAt.value = { status, index }
}

function onDragEnd() {
  dragging.value = null
  dropAt.value = null
}

async function onDrop(status: Status) {
  const card = dragging.value
  const target = dropAt.value
  onDragEnd()
  if (!card || !target) return

  const siblings = columns.value[status].filter((c) => c.id !== card.id)
  const prev = siblings[target.index - 1]?.position
  const next = siblings[target.index]?.position
  const position =
    prev === undefined && next === undefined
      ? 1
      : prev === undefined
        ? next! - 1
        : next === undefined
          ? prev + 1
          : (prev + next) / 2
  if (status === card.status && position === card.position) return

  const before = { ...card }
  Object.assign(card, { status, position }) // otimista
  saving.value = true
  try {
    const saved = await api.updateCard(card.id, { status, position })
    Object.assign(card, saved)
    if (before.status !== status) loadActivity()
  } catch (e) {
    Object.assign(card, before)
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

function visibleCards(status: Status) {
  const list = columns.value[status]
  return status === 'done' && !showAllDone.value ? list.slice(0, DONE_VISIBLE) : list
}

/** Cards visíveis da coluna sem o que está sendo arrastado: é nessa lista que dropAt.index aponta. */
function others(status: Status) {
  return visibleCards(status).filter((c) => c.id !== dragging.value?.id)
}

function lineBefore(status: Status, card: Card) {
  return dropAt.value?.status === status && others(status).indexOf(card) === dropAt.value.index
}

// ---- spec ----
const editingSpec = ref(false)
const specDraft = ref('')

async function saveSpec() {
  saving.value = true
  try {
    project.value = await api.updateProject(props.slug, { spec: specDraft.value })
    editingSpec.value = false
    loadActivity()
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

function cancelSpec() {
  specDraft.value = project.value?.spec ?? ''
  editingSpec.value = false
}

// ---- atividade ----
const note = ref('')

async function addNote() {
  if (!note.value.trim()) return
  await api.logActivity(props.slug, { message: note.value.trim() })
  note.value = ''
  loadActivity()
}

async function toggleArchived() {
  if (!project.value) return
  project.value = await api.updateProject(props.slug, { archived: !project.value.archived })
}

const copied = ref(false)
async function copyBoardLink() {
  if (!project.value) return
  await navigator.clipboard.writeText(project.value.url)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}
</script>

<template>
  <main class="board-page">
    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="loading" class="muted loading">Carregando…</div>

    <template v-else-if="project">
      <header class="head">
        <div>
          <h1>
            {{ project.name }}
            <span v-if="project.archived" class="chip">arquivado</span>
          </h1>
          <p v-if="project.summary" class="muted">{{ project.summary }}</p>
          <p v-if="project.repo" class="muted small"><code>{{ project.repo }}</code></p>
        </div>
        <div class="head-actions">
          <button class="btn small" @click="copyBoardLink">{{ copied ? 'Copiado' : 'Copiar link' }}</button>
          <button class="btn ghost small" @click="toggleArchived">
            {{ project.archived ? 'Desarquivar' : 'Arquivar' }}
          </button>
        </div>
      </header>

      <nav class="tabs">
        <button :class="{ active: tab === 'board' }" @click="tab = 'board'">Board</button>
        <button :class="{ active: tab === 'spec' }" @click="tab = 'spec'">
          Spec <span v-if="!project.spec.trim()" class="chip p1">vazia</span>
        </button>
        <button :class="{ active: tab === 'activity' }" @click="tab = 'activity'">Atividade</button>
      </nav>

      <!-- BOARD -->
      <section v-if="tab === 'board'" class="columns">
        <div
          v-for="status in STATUSES"
          :key="status"
          class="column"
          :class="{ over: dropAt?.status === status }"
          :style="{ background: `var(--col-${status})` }"
          @dragover="onDragOver(status, $event)"
          @drop.prevent="onDrop(status)"
        >
          <div class="col-head">
            <h2>{{ STATUS_LABEL[status] }}</h2>
            <span class="count">{{ columns[status].length }}</span>
            <button class="btn ghost add" :aria-label="`Novo card em ${STATUS_LABEL[status]}`" @click="adding = status">
              +
            </button>
          </div>

          <form v-if="adding === status" class="quick-add" @submit.prevent="addCard(status)">
            <input
              v-model="newTitle"
              placeholder="Título e Enter"
              autofocus
              @keydown.esc="adding = null"
              @blur="!newTitle && (adding = null)"
            />
          </form>

          <div class="list">
            <template v-for="card in visibleCards(status)" :key="card.id">
              <div v-if="lineBefore(status, card)" class="drop-line" />
              <article
                class="card"
                :class="{ dragging: dragging?.id === card.id }"
                :data-card="card.id"
                draggable="true"
                @dragstart="onDragStart(card, $event)"
                @dragend="onDragEnd"
                @click="showCard(card.id)"
              >
                <p class="card-title">{{ card.title }}</p>
                <div class="meta">
                  <span class="id">#{{ card.id }}</span>
                  <span v-if="card.priority <= 1" class="chip" :class="`p${card.priority}`">P{{ card.priority }}</span>
                  <span v-if="card.due_date" class="chip" :class="{ late: card.status !== 'done' && isOverdue(card.due_date) }">
                    {{ formatDate(card.due_date) }}
                  </span>
                  <span v-if="card.spec_ref" class="chip" :title="`Spec: ${card.spec_ref}`">§ {{ card.spec_ref }}</span>
                  <span v-for="l in card.labels" :key="l" class="chip">{{ l }}</span>
                </div>
                <p v-if="status === 'doing' || status === 'blocked'" class="muted tiny">
                  atualizado {{ timeAgo(card.updated_at) }}
                </p>
              </article>
            </template>
            <div v-if="dropAt?.status === status && dropAt.index >= others(status).length" class="drop-line" />
            <button
              v-if="status === 'done' && columns.done.length > DONE_VISIBLE"
              class="btn ghost small"
              @click="showAllDone = !showAllDone"
            >
              {{ showAllDone ? 'Mostrar menos' : `Ver todos (${columns.done.length})` }}
            </button>
          </div>
        </div>
      </section>

      <!-- SPEC -->
      <section v-else-if="tab === 'spec'" class="panel spec">
        <div class="spec-head">
          <p class="muted small">
            A spec é a fonte da verdade do projeto. Decisões e mudanças de escopo entram aqui antes de virar card; a
            IA atualiza pela API.
          </p>
          <div v-if="!editingSpec">
            <button class="btn" @click="editingSpec = true">Editar</button>
          </div>
        </div>
        <template v-if="editingSpec">
          <textarea v-model="specDraft" rows="24" placeholder="# Nome do projeto&#10;&#10;## 1. Problema e público" />
          <div class="spec-actions">
            <button class="btn" @click="cancelSpec">Cancelar</button>
            <button class="btn primary" :disabled="saving" @click="saveSpec">{{ saving ? 'Salvando…' : 'Salvar' }}</button>
          </div>
        </template>
        <MarkdownView v-else-if="project.spec.trim()" :source="project.spec" />
        <div v-else class="empty">
          Sem spec ainda. Peça para sua IA: <em>"escreva a spec deste projeto no Specboard"</em>, ou clique em Editar.
        </div>
      </section>

      <!-- ATIVIDADE -->
      <section v-else class="panel activity">
        <form class="note" @submit.prevent="addNote">
          <input v-model="note" placeholder="Anotar algo (o que foi feito, uma decisão…)" />
          <button class="btn">Anotar</button>
        </form>
        <ul v-if="activity.length">
          <li v-for="a in activity" :key="a.id">
            <span class="chip" :class="{ ai: a.actor !== 'user' }">{{ a.actor }}</span>
            <span v-if="a.kind === 'decision'" class="chip p1">decisão</span>
            <span class="msg">{{ a.message }}</span>
            <button v-if="a.card_id && cards.some((c) => c.id === a.card_id)" class="link" @click="showCard(a.card_id)">
              abrir #{{ a.card_id }}
            </button>
            <span class="muted small when">{{ timeAgo(a.created_at) }}</span>
          </li>
        </ul>
        <p v-else class="empty">Nada registrado ainda.</p>
      </section>
    </template>

    <CardModal v-if="openCard" :key="openCard.id" :card="openCard" @close="closeCard" @saved="onSaved" @deleted="onDeleted" />
  </main>
</template>

<style scoped>
.board-page {
  padding: 20px 16px 40px;
}

.loading {
  padding: 40px 0;
  text-align: center;
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.head h1 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 30px;
}

.head p {
  margin: 4px 0 0;
}

.head-actions {
  display: flex;
  gap: 6px;
  align-items: flex-start;
}

.tabs {
  display: flex;
  gap: 4px;
  margin: 16px 0;
  border-bottom: 1px solid var(--border);
}

.tabs button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: none;
  cursor: pointer;
  color: var(--muted);
}

.tabs button.active {
  color: var(--text);
  font-weight: 600;
  border-bottom-color: var(--accent);
}

.columns {
  display: grid;
  grid-template-columns: repeat(5, minmax(240px, 1fr));
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.column {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 220px;
  padding: 12px 10px 10px;
  border-radius: var(--radius);
  border: 1px solid rgb(38 34 30 / 6%);
}

.column.over {
  border: 1px dashed var(--text);
}

.col-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.col-head h2 {
  font-size: 17px;
}

.count {
  font: 12px/1 var(--font-mono);
  color: var(--muted);
}

.add {
  margin-left: auto;
  padding: 0 8px;
  font-size: 18px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.card {
  padding: 10px 12px;
  border-radius: 6px;
  background: var(--surface);
  border: 1px solid rgb(38 34 30 / 10%);
  box-shadow: var(--shadow);
  cursor: grab;
  transition:
    transform 0.15s ease-out,
    box-shadow 0.15s ease-out;
}

.card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-lift);
}

.card.dragging {
  opacity: 0.4;
}

.card-title {
  margin: 0 0 6px;
  font-weight: 470;
  overflow-wrap: anywhere;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.id {
  margin-right: 2px;
  font: 11.5px var(--font-mono);
  color: var(--muted);
}

.tiny {
  margin: 6px 0 0;
  font-size: 12px;
}

.drop-line {
  height: 3px;
  border-radius: 2px;
  background: var(--accent);
}

.spec {
  display: grid;
  gap: 12px;
  padding: 20px;
}

.spec-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.spec-head p {
  margin: 0;
}

.spec-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.activity {
  padding: 16px;
}

.note {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.activity ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.activity li {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 8px;
  padding: 8px 0;
  border-top: 1px solid var(--border);
}

.msg {
  flex: 1;
  min-width: 200px;
  overflow-wrap: anywhere;
}

.link {
  border: 0;
  background: none;
  color: var(--accent);
  cursor: pointer;
  padding: 0;
  font-size: 13px;
}

@media (max-width: 700px) {
  .head {
    flex-direction: column;
  }

  .columns {
    grid-template-columns: repeat(5, 82vw);
    scroll-snap-type: x mandatory;
  }

  .column {
    scroll-snap-align: start;
  }
}
</style>
