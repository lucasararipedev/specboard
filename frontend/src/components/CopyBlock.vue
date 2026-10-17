<script setup lang="ts">
import { computed, ref } from 'vue'
import { copyText } from '../clipboard'

const props = defineProps<{ text: string; label?: string; placeholder?: string; tall?: boolean }>()

const state = ref<'idle' | 'ok' | 'fail'>('idle')
const pre = ref<HTMLElement>()

// O botão é só ícone; o rótulo vai para o title e para o leitor de tela.
const title = computed(() =>
  state.value === 'ok' ? 'Copiado' : state.value === 'fail' ? 'Selecionado: Ctrl+C' : props.label || 'Copiar',
)

async function copy() {
  state.value = (await copyText(props.text)) ? 'ok' : 'fail'
  if (state.value === 'fail') selectAll()
  setTimeout(() => (state.value = 'idle'), 1800)
}

/** Um clique no texto seleciona tudo, para quem prefere Ctrl+C. */
function selectAll() {
  if (!pre.value) return
  const range = document.createRange()
  range.selectNodeContents(pre.value)
  const sel = window.getSelection()
  sel?.removeAllRanges()
  sel?.addRange(range)
}
</script>

<template>
  <div class="copy-block" :class="{ tall }">
    <button
      type="button"
      class="btn primary copy"
      :class="{ ok: state === 'ok' }"
      :disabled="!text"
      :title="title"
      :aria-label="title"
      @click="copy"
    >
      <svg v-if="state === 'ok'" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 8.5l3.2 3L13 4.5" />
      </svg>
      <svg v-else viewBox="0 0 16 16" aria-hidden="true">
        <rect x="5.5" y="5.5" width="8" height="8" rx="1.5" />
        <path d="M10.5 3.5v-.5a1.5 1.5 0 0 0-1.5-1.5H4A1.5 1.5 0 0 0 2.5 3v5A1.5 1.5 0 0 0 4 9.5h.5" />
      </svg>
    </button>
    <pre ref="pre" @click="selectAll">{{ text || placeholder || 'Carregando…' }}</pre>
  </div>
</template>

<style scoped>
.copy-block {
  position: relative;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}

pre {
  margin: 0;
  /* Espaço só à direita, para o texto não passar por baixo do botão. */
  padding: 15px 58px 15px 18px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.6;
  cursor: text;
}

.tall pre {
  max-height: 340px;
  overflow: auto;
}

.copy {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
}

/* No bloco com rolagem, o botão fica fora da barra de rolagem. */
.tall .copy {
  right: 18px;
}

.copy.ok,
.copy.ok:hover {
  background: var(--ok);
  border-color: var(--ok);
}

svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}
</style>
