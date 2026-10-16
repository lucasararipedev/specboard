<script setup lang="ts">
import { ref } from 'vue'
import { copyText } from '../clipboard'

const props = defineProps<{ text: string; label?: string; placeholder?: string; tall?: boolean }>()

const state = ref<'idle' | 'ok' | 'fail'>('idle')
const pre = ref<HTMLElement>()

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
    <button class="btn primary copy" :disabled="!text" @click="copy">
      {{ state === 'ok' ? 'Copiado' : state === 'fail' ? 'Selecionado: Ctrl+C' : label || 'Copiar' }}
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
  padding: 16px 18px;
  padding-top: 54px;
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
  top: 10px;
  right: 10px;
}
</style>
