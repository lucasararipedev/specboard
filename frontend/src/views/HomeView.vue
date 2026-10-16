<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '../api'
import { copyText } from '../clipboard'
import CopyBlock from '../components/CopyBlock.vue'

const REPO = 'https://github.com/lucasararipedev/specboard'
const origin = location.origin

const install = `git clone ${REPO}
cd specboard
docker compose up -d`

const firstAsk = 'Crie um projeto no Specboard pro que estou fazendo, escreva uma spec curta e registre os próximos passos.'

const prompt = ref('')
const promptError = ref('')
const online = ref<boolean | null>(null)
const heroCopied = ref(false)

const video = ref<HTMLVideoElement>()
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches

function fullscreen() {
  const v = video.value
  if (!v) return
  v.controls = true
  v.play().catch(() => {})
  v.requestFullscreen?.().catch(() => {})
}

function onFullscreenChange() {
  if (!document.fullscreenElement && video.value) video.value.controls = reducedMotion
}

async function copyPromptFromHero() {
  if (!prompt.value) return
  heroCopied.value = await copyText(prompt.value)
  if (!heroCopied.value) document.getElementById('prompt')?.scrollIntoView()
  setTimeout(() => (heroCopied.value = false), 2400)
}

const benefits = [
  {
    tag: 'memória',
    title: 'Memória de longo prazo',
    text: 'A conversa acaba, o board fica. Na sessão seguinte a IA lê o briefing e continua de onde parou.',
  },
  {
    tag: 'projetos',
    title: 'Vários projetos, um lugar',
    text: 'Um kanban por projeto. A IA acha o certo pelo repositório e não mistura as coisas.',
  },
  {
    tag: 'spec',
    title: 'Spec first, resposta melhor',
    text: 'A IA lê a spec antes de planejar. Decisão escrita é escopo que ela não inventa.',
  },
  {
    tag: 'perguntas',
    title: 'Pergunta em vez de supor',
    text: 'Faltou contexto? Ela deixa a pergunta no board, com opções. Você responde num clique.',
  },
  {
    tag: 'lembretes',
    title: 'Lembra do que importa',
    text: 'Card parado há dias, P0 esquecido no backlog, prazo vencido. Ela puxa o assunto.',
  },
  {
    tag: 'qualquer ia',
    title: 'Troque de IA sem perder nada',
    text: 'Claude hoje, ChatGPT amanhã, Cursor no outro dia. O board é o mesmo.',
  },
]

const faq = [
  {
    q: 'Funciona com qual IA?',
    a: 'Qualquer uma que faça requisições HTTP: Claude Code, Cursor, Codex, Gemini CLI, Windsurf, Copilot, Aider… O prompt é o mesmo para todas.',
  },
  {
    q: 'E o ChatGPT ou o Claude no navegador?',
    a: 'Eles rodam na nuvem e não enxergam o seu localhost. Cole o prompt mesmo assim: a IA te passa os comandos curl prontos para você rodar. Ou exponha com um túnel e defina SPECBOARD_TOKEN (está no README).',
  },
  {
    q: 'Preciso colar o prompt toda vez?',
    a: 'Não. O prompt pede para a IA salvar as regras na memória ou no arquivo de instruções dela. Se a sua IA não tiver memória, cole no começo da conversa.',
  },
  {
    q: 'Onde ficam meus dados?',
    a: 'Num arquivo SQLite na sua máquina. Sem conta, sem nuvem, sem chave de IA. Backup com make backup (exporta tudo em JSON).',
  },
  {
    q: 'Quanto custa?',
    a: 'Nada. É open source, licença MIT. Use, mude e distribua.',
  },
]

onMounted(async () => {
  document.addEventListener('fullscreenchange', onFullscreenChange)
  // Autoplay só funciona mudo; quem pede menos movimento dá o play quando quiser.
  if (video.value && !reducedMotion) {
    video.value.muted = true
    video.value.play().catch(() => {})
  }
  fetch('/api/health')
    .then((r) => (online.value = r.ok))
    .catch(() => (online.value = false))
  try {
    prompt.value = await api.prompt()
  } catch (e) {
    promptError.value = (e as Error).message
  }
})
onBeforeUnmount(() => document.removeEventListener('fullscreenchange', onFullscreenChange))
</script>

<template>
  <main class="home">
    <!-- Hero -->
    <section class="hero">
      <div class="hero-text">
        <p class="kicker mono">open source · roda na sua máquina · sem conta</p>
        <h1>Sua IA esquece.<br />O <span class="ink-mark">board</span>, não.</h1>
        <p class="lead">
          Um kanban <b>spec-first</b> que a sua própria IA mantém em dia. Ela registra as tarefas, move os cards,
          guarda as decisões na spec e, no começo de cada sessão, te lembra do que importa.
        </p>
        <div class="cta">
          <button class="btn primary big" :disabled="!prompt" @click="copyPromptFromHero">
            {{ heroCopied ? 'Copiado. Agora cole na sua IA' : 'Copiar o prompt' }}
          </button>
          <a href="#como-funciona" class="btn big">Como funciona</a>
        </div>
        <p class="muted small">
          Funciona com Claude, ChatGPT, Gemini, Cursor, Codex e o que mais você usar.
          É open source: <a :href="REPO" target="_blank" rel="noopener">deixe uma estrela no GitHub</a>.
        </p>
      </div>

      <!-- O produto em uso: a IA mantém, você acompanha -->
      <figure class="screen">
        <div class="screen-bar">
          <span class="url mono">localhost:8787/p/agenda-barbearia</span>
          <button class="btn ghost small" type="button" @click="fullscreen">Tela cheia</button>
        </div>
        <video
          ref="video"
          poster="/demo-poster.jpg"
          muted
          loop
          playsinline
          preload="auto"
          :controls="reducedMotion"
          @click="fullscreen"
          aria-label="Demonstração: navegando no board, a IA criando cards, a spec, as perguntas e a atividade"
        >
          <!-- H.264 para Safari e Chrome; VP9 para navegadores sem o codec proprietário. -->
          <source src="/demo.mp4" type='video/mp4; codecs="avc1.640028"' />
          <source src="/demo.webm" type="video/webm" />
        </video>
      </figure>
    </section>

    <!-- Passos -->
    <section id="como-funciona" class="section">
      <p class="eyebrow mono">como funciona</p>
      <h2>Três passos e a sua IA cuida do resto</h2>

      <ol class="steps">
        <li class="step">
          <div class="step-num mono">1</div>
          <div class="step-body">
            <h3>Suba o Specboard</h3>
            <p class="muted">Precisa só de Docker. Um comando e ele fica rodando em <code>localhost:8787</code>.</p>
            <CopyBlock :text="install" label="Copiar" />
            <p v-if="online !== null" class="status small" :class="{ off: !online }">
              <span class="dot" />
              <template v-if="online">Já está rodando aqui: <span class="mono">{{ origin }}</span></template>
              <template v-else>A API não respondeu. Rode <code>docker compose up -d</code> na pasta do projeto.</template>
            </p>
          </div>
        </li>

        <li id="prompt" class="step">
          <div class="step-num mono">2</div>
          <div class="step-body">
            <h3>Copie o prompt e cole na sua IA</h3>
            <p class="muted">
              Clique em <b>Copiar prompt</b> (ou selecione o texto e copie) e cole na sua IA. É o mesmo texto para
              qualquer uma. Ela lê o manual, salva as regras na memória e começa a cuidar do board.
            </p>
            <p v-if="promptError" class="error">Não deu para carregar o prompt: {{ promptError }}</p>
            <CopyBlock v-else :text="prompt" label="Copiar prompt" tall />
          </div>
        </li>

        <li class="step">
          <div class="step-num mono">3</div>
          <div class="step-body">
            <h3>Acompanhe pelos seus projetos</h3>
            <p class="muted">
              A IA cria os projetos, move os cards e anota as decisões. A tela se atualiza sozinha. Para começar,
              peça algo como:
            </p>
            <blockquote class="ask">“{{ firstAsk }}”</blockquote>
            <RouterLink to="/projetos" class="btn primary big">Abrir meus projetos</RouterLink>
          </div>
        </li>
      </ol>
    </section>

    <!-- Por que -->
    <section class="section">
      <p class="eyebrow mono">por que usar</p>
      <h2>Melhora o que a sua IA entrega</h2>
      <p class="muted intro">
        IA boa com contexto ruim entrega resultado ruim. O Specboard é o contexto que fica entre uma conversa e outra.
      </p>
      <div class="benefits">
        <article v-for="b in benefits" :key="b.tag" class="benefit">
          <span class="chip">{{ b.tag }}</span>
          <h3>{{ b.title }}</h3>
          <p>{{ b.text }}</p>
        </article>
      </div>
    </section>

    <!-- Na prática -->
    <section class="section">
      <p class="eyebrow mono">na prática</p>
      <h2>Duas conversas, dois dias</h2>
      <div class="days">
        <div class="day">
          <p class="day-date mono">segunda, 9h</p>
          <p><span class="who mono">você</span>Quero fazer um app de agenda pra barbearias. Organiza isso pra mim.</p>
          <p class="ia">
            <span class="who mono">ia</span>Criei o projeto <b>Agenda Barbearia</b> e deixei 5 perguntas no board:
            público, o que entra na v1, prazo… Responde lá que eu monto a spec.
          </p>
          <p><span class="who mono">você</span>Respondi.</p>
          <p class="ia">
            <span class="who mono">ia</span>Spec escrita e 8 cards criados. O primeiro é <i>Agenda por profissional</i>,
            já movi para Fazendo.
          </p>
        </div>
        <div class="day">
          <p class="day-date mono">quarta, 14h · conversa nova</p>
          <p><span class="who mono">você</span>Bora trabalhar.</p>
          <p class="ia">
            <span class="who mono">ia</span>Pelo briefing: <i>Agenda por profissional</i> está em andamento há 2 dias e
            o bug do login com Google é P1. Você decidiu Stripe na segunda. Fecho a agenda primeiro?
          </p>
          <p class="note small muted">
            Ela não lembrava de nada. Leu o board. É isso que vira memória de longo prazo, entre sessões e entre
            projetos.
          </p>
        </div>
      </div>
    </section>

    <!-- Dúvidas -->
    <section class="section narrow">
      <p class="eyebrow mono">dúvidas</p>
      <h2>Perguntas frequentes</h2>
      <div class="faq">
        <details v-for="item in faq" :key="item.q">
          <summary>{{ item.q }}</summary>
          <p>{{ item.a }}</p>
        </details>
      </div>
    </section>

    <!-- Estrela no GitHub -->
    <section class="star-band">
      <div>
        <h2>Gostou? Deixe uma estrela</h2>
        <p class="muted">
          O Specboard é open source e gratuito. Uma estrela no GitHub ajuda outros devs a encontrarem o projeto e
          mostra que vale continuar.
        </p>
      </div>
      <div class="star-actions">
        <a :href="REPO" target="_blank" rel="noopener" class="btn primary big">
          <svg class="star" width="16" height="16" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z" /></svg>
          Dar uma estrela no GitHub
        </a>
        <a :href="`${REPO}/issues`" target="_blank" rel="noopener" class="small">Sugerir uma melhoria</a>
      </div>
    </section>

    <footer class="foot">
      <p>
        <img src="/favicon.svg" alt="" width="22" height="22" />
        <b>Specboard</b> <span class="muted">· open source, licença MIT</span>
      </p>
      <nav class="small">
        <a :href="REPO" target="_blank" rel="noopener">Estrela no GitHub</a>
        <a href="/llms.txt" target="_blank">Manual da IA</a>
        <a href="/docs" target="_blank">API</a>
        <RouterLink to="/projetos">Projetos</RouterLink>
      </nav>
    </footer>
  </main>
</template>

<style scoped>
/* Largura total com conteúdo centralizado: a pauta do hero vai de ponta a ponta sem criar rolagem lateral. */
.home {
  padding: 0 max(16px, (100% - 1068px) / 2) 40px;
  overflow-x: clip;
}

.mono {
  font-family: var(--font-mono);
}

/* Hero */
.hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 0.85fr) minmax(0, 1.15fr);
  gap: 44px;
  align-items: center;
  padding: 64px 0 72px;
}

/* Pauta de caderno atrás do hero. */
.hero::before {
  content: '';
  position: absolute;
  inset: 0 -100vw;
  z-index: -1;
  background: repeating-linear-gradient(to bottom, transparent 0 31px, var(--border) 31px 32px);
  opacity: 0.45;
  mask-image: linear-gradient(to bottom, transparent, #000 15%, #000 75%, transparent);
}

.kicker,
.eyebrow {
  margin: 0 0 14px;
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
}

.hero h1 {
  font-size: clamp(40px, 5.4vw, 62px);
  line-height: 1.02;
  letter-spacing: -0.025em;
}

/* Sublinhado de marca-texto vermelhão, como caneta no caderno. */
.ink-mark {
  font-style: italic;
  background: linear-gradient(transparent 62%, var(--accent-soft) 62% 92%, transparent 92%);
  color: var(--accent);
}

.lead {
  max-width: 34em;
  margin: 22px 0 26px;
  font-size: 18px;
  line-height: 1.6;
}

.cta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 16px;
}

.btn.big {
  padding: 11px 20px;
  font-size: 16px;
}

.who {
  display: inline-block;
  padding: 0 6px;
  border-radius: 4px;
  font-size: 11px;
  line-height: 1.7;
  background: var(--surface-2);
  color: var(--muted);
  vertical-align: 1px;
}

.day .who {
  margin-right: 8px;
}

.ia > .who {
  background: var(--text);
  color: var(--bg);
}

/* Vídeo do produto no hero */
.screen {
  margin: 0;
  overflow: hidden;
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  background: var(--surface);
  box-shadow: var(--shadow-lift);
}

.screen-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 8px 6px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
}

.url {
  overflow: hidden;
  padding: 3px 10px;
  border-radius: 5px;
  background: var(--surface);
  font-size: 12px;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

video {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: var(--bg);
  cursor: zoom-in;
}

/* Seções */
.section {
  padding: 56px 0;
  border-top: 1px dashed var(--border-strong);
}

.section > h2 {
  font-size: clamp(28px, 3.6vw, 38px);
  letter-spacing: -0.02em;
}

.intro {
  max-width: 40em;
  margin: 12px 0 0;
  font-size: 17px;
}

.narrow > * {
  max-width: 760px;
}

/* Passos */
.steps {
  display: grid;
  gap: 36px;
  margin: 32px 0 0;
  padding: 0;
  list-style: none;
}

.step {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  gap: 18px;
  scroll-margin-top: 80px;
}

.step-num {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 1.5px solid var(--text);
  border-radius: 50%;
  font-size: 18px;
  background: var(--surface);
}

.step-body {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.step-body h3 {
  font-size: 23px;
}

.step-body p {
  margin: 0;
}

.step-body > .btn {
  justify-self: start;
}

.status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ok);
}

.status.off {
  color: var(--danger);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 0 3px var(--ok-soft);
}

.status.off .dot {
  box-shadow: 0 0 0 3px var(--danger-soft);
}

.ask {
  margin: 0;
  padding: 4px 16px;
  border-left: 2px solid var(--accent);
  font: italic 18px/1.5 var(--font-serif);
}

/* Benefícios */
.benefits {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 28px;
}

.benefit {
  display: grid;
  align-content: start;
  justify-items: start;
  gap: 8px;
  padding: 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
  transition:
    transform 0.15s ease-out,
    box-shadow 0.15s ease-out;
}

.benefit:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lift);
}

.benefit h3 {
  font-size: 20px;
}

.benefit p {
  margin: 0;
  color: var(--muted);
}

/* Na prática */
.days {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 28px;
}

.day {
  display: grid;
  align-content: start;
  gap: 10px;
  padding: 18px 20px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}

.day p {
  margin: 0;
}

.day-date {
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.note {
  padding-top: 8px;
  border-top: 1px dashed var(--border-strong);
}

/* FAQ */
.faq {
  margin-top: 24px;
  border-top: 1px solid var(--border);
}

details {
  border-bottom: 1px solid var(--border);
}

summary {
  padding: 14px 0;
  cursor: pointer;
  font: 500 18px var(--font-serif);
  list-style: none;
}

summary::-webkit-details-marker {
  display: none;
}

summary::before {
  content: '+';
  display: inline-block;
  width: 22px;
  font-family: var(--font-mono);
  color: var(--accent);
}

details[open] summary::before {
  content: '–';
}

details p {
  margin: 0 0 16px 22px;
  color: var(--muted);
}

/* Pedido de estrela */
.star-band {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 20px 32px;
  margin: 8px 0 48px;
  padding: 28px 30px;
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  background: var(--surface);
  box-shadow: var(--shadow-lift);
}

.star-band > div:first-child {
  max-width: 34em;
}

.star-band h2 {
  font-size: clamp(24px, 3vw, 30px);
}

.star-band p {
  margin: 8px 0 0;
}

.star-actions {
  display: grid;
  justify-items: center;
  gap: 10px;
}

.star {
  fill: var(--accent);
}

/* Rodapé */
.foot {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 28px 0 0;
  border-top: 1px dashed var(--border-strong);
}

.foot p {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.foot nav {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

@media (max-width: 860px) {
  .hero {
    grid-template-columns: minmax(0, 1fr);
    gap: 36px;
    padding: 40px 0 48px;
  }

  .benefits {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .days {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 560px) {
  .lead {
    font-size: 16px;
  }

  .benefits {
    grid-template-columns: minmax(0, 1fr);
  }

  .step {
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
  }

  .cta .btn {
    flex: 1;
    justify-content: center;
  }

  .star-band {
    padding: 22px 18px;
  }

  .star-actions,
  .star-actions .btn {
    width: 100%;
    justify-content: center;
  }

}
</style>
