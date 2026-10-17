<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '../api'
import { timeAgo } from '../format'
import type { AgentSession } from '../types'

// project: só as sessões dele (faixa no board). Sem project: todas, com o nome do projeto (página Projetos).
const props = defineProps<{ project?: string }>()
const emit = defineEmits<{ openCard: [id: number] }>()

const POLL_MS = 5000
const sessions = ref<AgentSession[]>([])
const loaded = ref(false)

async function load() {
  if (document.hidden) return
  try {
    sessions.value = await api.sessions(props.project)
  } catch {
    // erro passageiro: tenta no próximo ciclo
  } finally {
    loaded.value = true
  }
}

let timer: number | undefined
onMounted(() => {
  load()
  timer = window.setInterval(load, POLL_MS)
})
onUnmounted(() => window.clearInterval(timer))
</script>

<template>
  <section v-if="!project || sessions.length" class="now" :class="{ compact: !!project }">
    <h2 class="now-title">Agora</h2>
    <ul v-if="sessions.length">
      <li v-for="s in sessions" :key="s.key" :class="{ idle: s.idle }">
        <span class="chip ai">{{ s.actor }}</span>
        <RouterLink v-if="!project && s.project_url" :to="`/p/${s.project}`" class="project mono">{{ s.project }}</RouterLink>
        <span class="doing">{{ s.doing || 'sem status' }}</span>
        <template v-if="s.card_id">
          <button v-if="project" class="link" @click="emit('openCard', s.card_id)">#{{ s.card_id }}</button>
          <RouterLink v-else :to="`/p/${s.project}?card=${s.card_id}`" class="link">#{{ s.card_id }}</RouterLink>
        </template>
        <span v-if="s.idle" class="chip">parado</span>
        <span class="muted small when">{{ timeAgo(s.last_seen_at) }}</span>
      </li>
    </ul>
    <p v-else-if="loaded" class="muted small empty-now">
      Nenhum chat ligado. No Claude Code, instale o plugin e rode <code>/board</code>; em outras IAs, peça para
      "ligar este chat ao Specboard".
    </p>
  </section>
</template>

<style scoped>
.now {
  margin-bottom: 20px;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}

.now.compact {
  margin: 0 0 12px;
  padding: 8px 12px;
}

.now-title {
  margin-bottom: 6px;
  font-size: 17px;
}

.compact .now-title {
  display: none;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}

li {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 8px;
}

li.idle {
  opacity: 0.6;
}

.project {
  font-size: 12.5px;
  color: var(--text);
}

.doing {
  flex: 1;
  min-width: 160px;
  overflow-wrap: anywhere;
}

.link {
  border: 0;
  background: none;
  color: var(--accent);
  cursor: pointer;
  padding: 0;
  font: 12.5px var(--font-mono);
}

.empty-now {
  margin: 0;
}

@media (prefers-reduced-motion: no-preference) {
  li {
    transition: opacity 0.15s ease-out;
  }
}
</style>
