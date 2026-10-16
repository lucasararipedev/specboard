<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { timeAgo } from '../format'
import type { Question } from '../types'

const props = defineProps<{ questions: Question[]; highlight?: number }>()
const emit = defineEmits<{ changed: []; openCard: [id: number] }>()

// Rascunhos por pergunta: sobrevivem ao polling do board.
const drafts = reactive<Record<number, string>>({})
const editing = ref<number | null>(null)
const busy = ref<number | null>(null)
const showDismissed = ref(false)
const error = ref('')

const open = computed(() => props.questions.filter((q) => q.status === 'open'))
const answered = computed(() =>
  props.questions
    .filter((q) => q.status === 'answered' || q.status === 'applied')
    .sort((a, b) => (b.answered_at ?? '').localeCompare(a.answered_at ?? '')),
)
const dismissed = computed(() => props.questions.filter((q) => q.status === 'dismissed'))

async function save(q: Question, patch: Partial<Pick<Question, 'answer' | 'status'>>) {
  busy.value = q.id
  error.value = ''
  try {
    await api.updateQuestion(q.id, patch)
    emit('changed')
    return true
  } catch (e) {
    error.value = (e as Error).message
    return false
  } finally {
    busy.value = null
  }
}

async function answer(q: Question) {
  const text = (drafts[q.id] ?? '').trim()
  if (!text) return
  if (await save(q, { answer: text })) {
    delete drafts[q.id]
    editing.value = null
  }
}

function startEdit(q: Question) {
  drafts[q.id] = q.answer
  editing.value = q.id
}

function askerLabel(q: Question) {
  return q.asked_by === 'specboard' ? 'pergunta inicial' : q.asked_by === 'user' ? 'você' : q.asked_by
}

onMounted(async () => {
  if (!props.highlight) return
  await nextTick()
  document.getElementById(`q-${props.highlight}`)?.scrollIntoView({ block: 'center' })
})
</script>

<template>
  <section class="questions">
    <p class="intro muted">
      Quanto mais você responde, menos a IA precisa supor. As respostas novas entram na spec ou nos cards na próxima
      conversa.
    </p>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="open.length" class="open">
      <form
        v-for="q in open"
        :id="`q-${q.id}`"
        :key="q.id"
        class="panel question"
        :class="{ highlight: q.id === highlight }"
        @submit.prevent="answer(q)"
      >
        <div class="q-head">
          <h3>{{ q.question }}</h3>
          <span class="chip" :class="{ ai: !['specboard', 'user'].includes(q.asked_by) }">{{ askerLabel(q) }}</span>
        </div>
        <p v-if="q.context || q.card_id" class="muted small">
          {{ q.context }}
          <button v-if="q.card_id" type="button" class="link" @click="emit('openCard', q.card_id)">
            card #{{ q.card_id }}
          </button>
        </p>
        <div v-if="q.options.length" class="options">
          <button
            v-for="o in q.options"
            :key="o"
            type="button"
            class="option"
            :class="{ picked: drafts[q.id] === o }"
            @click="drafts[q.id] = o"
          >
            {{ o }}
          </button>
        </div>
        <textarea
          v-model="drafts[q.id]"
          rows="2"
          :placeholder="q.options.length ? 'Escolha uma opção ou escreva a sua' : 'Sua resposta'"
          @keydown.ctrl.enter="answer(q)"
          @keydown.meta.enter="answer(q)"
        />
        <div class="actions">
          <button type="button" class="btn ghost small" :disabled="busy === q.id" @click="save(q, { status: 'dismissed' })">
            Dispensar
          </button>
          <button class="btn primary small" :disabled="busy === q.id || !(drafts[q.id] ?? '').trim()">Responder</button>
        </div>
      </form>
    </div>
    <div v-else class="panel empty">
      Nenhuma pergunta aberta. Quando faltar contexto, a IA pergunta aqui.
    </div>

    <template v-if="answered.length">
      <h2 class="section">Respondidas</h2>
      <ul class="panel answered">
        <li v-for="q in answered" :id="`q-${q.id}`" :key="q.id" :class="{ highlight: q.id === highlight }">
          <div class="a-head">
            <span class="a-question">{{ q.question }}</span>
            <span class="chip" :class="{ waiting: q.status === 'answered' }">
              {{ q.status === 'answered' ? 'a IA ainda vai usar' : 'incorporada' }}
            </span>
          </div>
          <form v-if="editing === q.id" class="edit" @submit.prevent="answer(q)">
            <textarea v-model="drafts[q.id]" rows="2" @keydown.ctrl.enter="answer(q)" @keydown.meta.enter="answer(q)" />
            <div class="actions">
              <button type="button" class="btn ghost small" @click="editing = null">Cancelar</button>
              <button class="btn primary small" :disabled="busy === q.id">Salvar</button>
            </div>
          </form>
          <p v-else class="a-answer">
            {{ q.answer }}
            <span class="muted small">· {{ q.answered_at ? timeAgo(q.answered_at) : '' }}</span>
            <button type="button" class="link" @click="startEdit(q)">editar</button>
          </p>
        </li>
      </ul>
    </template>

    <template v-if="dismissed.length">
      <button class="btn ghost small toggle" @click="showDismissed = !showDismissed">
        {{ showDismissed ? 'Esconder dispensadas' : `Ver dispensadas (${dismissed.length})` }}
      </button>
      <ul v-if="showDismissed" class="panel answered">
        <li v-for="q in dismissed" :key="q.id">
          <div class="a-head">
            <span class="a-question muted">{{ q.question }}</span>
            <button type="button" class="link" @click="save(q, { status: 'open' })">reabrir</button>
          </div>
        </li>
      </ul>
    </template>
  </section>
</template>

<style scoped>
.questions {
  display: grid;
  gap: 14px;
}

.intro {
  margin: 0;
  font-size: 14px;
}

.open {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 12px;
}

.question {
  display: grid;
  gap: 10px;
  align-content: start;
  padding: 16px;
}

.highlight {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.q-head,
.a-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.q-head h3 {
  font-size: 18px;
}

.question p {
  margin: 0;
}

.options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.option {
  padding: 4px 11px;
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  background: var(--surface);
  cursor: pointer;
  font-size: 13.5px;
  transition: background 0.15s ease-out;
}

.option:hover {
  background: var(--surface-2);
}

.option.picked {
  border-color: var(--text);
  background: var(--text);
  color: var(--bg);
}

textarea {
  font-family: var(--font-sans);
  font-size: 14.5px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.section {
  margin-top: 10px;
  font-size: 20px;
}

.answered {
  list-style: none;
  margin: 0;
  padding: 4px 16px;
}

.answered li {
  display: grid;
  gap: 4px;
  padding: 12px 0;
  border-top: 1px solid var(--border);
}

.answered li:first-child {
  border-top: 0;
}

.a-question {
  font-family: var(--font-serif);
  font-size: 16px;
}

.a-answer {
  margin: 0;
  white-space: pre-wrap;
}

.chip.waiting {
  border-color: #e3c98a;
  background: var(--warn-soft);
  color: var(--warn);
}

.edit {
  display: grid;
  gap: 6px;
}

.toggle {
  justify-self: start;
}

.link {
  border: 0;
  background: none;
  padding: 0;
  margin-left: 4px;
  color: var(--accent);
  cursor: pointer;
  font-size: 13px;
}

@media (max-width: 560px) {
  .open {
    grid-template-columns: 1fr;
  }
}
</style>
