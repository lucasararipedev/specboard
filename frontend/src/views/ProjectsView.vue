<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { timeAgo } from '../format'
import type { Project } from '../types'

const router = useRouter()
const projects = ref<Project[]>([])
const loading = ref(true)
const error = ref('')
const showArchived = ref(false)

const creating = ref(false)
const form = ref({ name: '', summary: '', repo: '' })
const saving = ref(false)

async function load() {
  error.value = ''
  try {
    projects.value = await api.projects(showArchived.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

async function create() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    const project = await api.createProject(form.value)
    router.push(`/p/${project.slug}`)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}

onMounted(load)
watch(showArchived, load)
</script>

<template>
  <main class="page">
    <div class="head">
      <div>
        <h1>Projetos</h1>
        <p class="muted">Um kanban por projeto. Sua IA mantém os cards e a spec em dia; você acompanha aqui.</p>
      </div>
      <button class="btn primary" @click="creating = !creating">+ Novo projeto</button>
    </div>

    <form v-if="creating" class="panel new" @submit.prevent="create">
      <label>Nome <input v-model="form.name" required placeholder="Meu SaaS" autofocus /></label>
      <label>Resumo <input v-model="form.summary" placeholder="Uma linha: o que é o projeto" /></label>
      <label>
        Repositório <span class="muted">(opcional; ajuda a IA a achar o projeto certo)</span>
        <input v-model="form.repo" placeholder="~/code/meu-saas ou https://github.com/..." />
      </label>
      <div class="actions">
        <button type="button" class="btn ghost" @click="creating = false">Cancelar</button>
        <button class="btn primary" :disabled="saving">{{ saving ? 'Criando…' : 'Criar' }}</button>
      </div>
    </form>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="loading" class="grid">
      <div v-for="i in 3" :key="i" class="panel skeleton" />
    </div>

    <div v-else-if="!projects.length" class="panel empty">
      <h2>Nenhum projeto ainda</h2>
      <p>
        O jeito mais rápido é <RouterLink to="/conectar">copiar o prompt</RouterLink> para a sua IA e pedir:
        <em>"crie um projeto pro que estou fazendo e registre o que falta"</em>.
      </p>
    </div>

    <div v-else class="grid">
      <RouterLink v-for="p in projects" :key="p.id" :to="`/p/${p.slug}`" class="panel project">
        <div class="title">
          <h2>{{ p.name }}</h2>
          <span v-if="p.archived" class="chip">arquivado</span>
        </div>
        <p class="muted summary">{{ p.summary || 'Sem resumo' }}</p>
        <div class="counts small">
          <span><b>{{ p.counts.doing }}</b> fazendo</span>
          <span><b>{{ p.counts.todo }}</b> a fazer</span>
          <span v-if="p.counts.blocked" class="blocked"><b>{{ p.counts.blocked }}</b> travado</span>
          <span><b>{{ p.counts.done }}</b> feito</span>
        </div>
        <p class="muted small">Atualizado {{ timeAgo(p.updated_at) }}</p>
      </RouterLink>
    </div>

    <label class="archived small"><input v-model="showArchived" type="checkbox" /> Mostrar arquivados</label>
  </main>
</template>

<style scoped>
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.head p {
  margin: 6px 0 0;
}

.new {
  display: grid;
  gap: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.project {
  display: grid;
  gap: 8px;
  padding: 16px;
  color: inherit;
  text-decoration: none;
  transition: border-color 0.15s;
}

.project:hover {
  border-color: var(--accent);
}

.project p {
  margin: 0;
}

.title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title h2 {
  font-size: 17px;
}

.summary {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.counts {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
}

.blocked {
  color: var(--danger);
}

.skeleton {
  height: 130px;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  50% {
    opacity: 0.5;
  }
}

.archived {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  margin-top: 24px;
}

.archived input {
  width: auto;
}

@media (max-width: 560px) {
  .head {
    flex-direction: column;
  }
}
</style>
