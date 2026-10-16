<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'

const prompt = ref('')
const error = ref('')
const copied = ref('')

const origin = location.origin
const claudeMd = `## Specboard (organização dos meus projetos)

- Kanban local em ${origin}. Manual da API: ${origin}/llms.txt (leia se ainda não leu nesta sessão).
- No início de cada sessão de trabalho, rode \`curl -s ${origin}/api/briefing\` e me lembre das prioridades.
- Tarefas, ideias, bugs e planos que eu mencionar viram cards; mova o status conforme o trabalho anda e registre atividades curtas.
- Decisões e mudanças de escopo vão para a spec do projeto antes de virar card.
- Mande \`X-Actor: claude\` nas requisições e me passe o link do card ou do board quando mudar algo.`

async function copy(text: string, which: string) {
  await navigator.clipboard.writeText(text)
  copied.value = which
  setTimeout(() => (copied.value = ''), 1500)
}

onMounted(async () => {
  try {
    prompt.value = await api.prompt()
  } catch (e) {
    error.value = (e as Error).message
  }
})
</script>

<template>
  <main class="page narrow">
    <h1>Conectar sua IA</h1>
    <p class="muted">
      O Specboard não tem IA dentro: quem mantém o board é a IA que você já usa (Claude, ChatGPT, Gemini, Cursor…).
      Ela lê o manual em <a href="/llms.txt" target="_blank">/llms.txt</a>, registra tarefas, move status e te lembra
      das prioridades. Você acompanha por aqui.
    </p>

    <section class="panel step">
      <div class="step-head">
        <h2>1. Cole este prompt na sua IA</h2>
        <button class="btn primary" :disabled="!prompt" @click="copy(prompt, 'prompt')">
          {{ copied === 'prompt' ? 'Copiado' : 'Copiar prompt' }}
        </button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <pre v-else>{{ prompt || 'Carregando…' }}</pre>
    </section>

    <section class="panel step">
      <div class="step-head">
        <h2>2. Claude Code: deixe fixo no CLAUDE.md</h2>
        <button class="btn" @click="copy(claudeMd, 'claude')">{{ copied === 'claude' ? 'Copiado' : 'Copiar' }}</button>
      </div>
      <p class="muted small">
        Cole no fim de <code>~/.claude/CLAUDE.md</code> (vale para todos os repositórios) ou no <code>CLAUDE.md</code>
        de um projeto. Assim o Claude lembra do board em toda sessão nova, sem você colar o prompt de novo.
      </p>
      <pre>{{ claudeMd }}</pre>
    </section>

    <section class="panel step">
      <h2>3. Outras IAs</h2>
      <ul class="small">
        <li><b>Cursor / Windsurf / Copilot</b>: cole o texto do passo 2 nas Rules do projeto ou em <code>AGENTS.md</code>.</li>
        <li><b>Codex CLI, Gemini CLI, Aider</b>: <code>AGENTS.md</code> ou <code>GEMINI.md</code> na raiz do repo.</li>
        <li>
          <b>ChatGPT, Gemini e Claude no navegador</b>: não alcançam <code>localhost</code>. Eles te passam os comandos
          <code>curl</code> prontos e você roda, ou exponha o Specboard com um túnel e defina
          <code>SPECBOARD_TOKEN</code> (veja o README).
        </li>
      </ul>
      <p class="muted small">Referência completa da API: <a href="/docs" target="_blank">/docs</a> (OpenAPI).</p>
    </section>
  </main>
</template>

<style scoped>
.narrow {
  max-width: 820px;
}

h1 {
  margin-bottom: 8px;
}

.step {
  display: grid;
  gap: 10px;
  padding: 18px;
  margin-top: 18px;
}

.step h2 {
  font-size: 16px;
}

.step-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.step p,
.step ul {
  margin: 0;
}

.step li + li {
  margin-top: 6px;
}

pre {
  margin: 0;
  padding: 14px;
  border-radius: 8px;
  background: var(--surface-2);
  white-space: pre-wrap;
  font-size: 13px;
  max-height: 420px;
  overflow: auto;
}

@media (max-width: 560px) {
  .step-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
