<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{ source: string }>()

// A spec e as descrições podem vir da IA (que lê a web), então o HTML é sempre sanitizado.
const html = computed(() => DOMPurify.sanitize(marked.parse(props.source, { async: false, gfm: true })))
</script>

<template>
  <div class="markdown" v-html="html" />
</template>
