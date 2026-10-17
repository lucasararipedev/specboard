<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{ name?: string; src?: string; size?: number }>(), {
  name: '',
  src: '',
  size: 28,
})

const initials = computed(
  () =>
    props.name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]!.toUpperCase())
      .join('') || '?',
)
</script>

<template>
  <span class="avatar" :style="{ width: `${size}px`, height: `${size}px`, fontSize: `${Math.round(size * 0.4)}px` }">
    <img v-if="src" :src="src" alt="" />
    <span v-else>{{ initials }}</span>
  </span>
</template>

<style scoped>
.avatar {
  display: inline-grid;
  place-items: center;
  flex: none;
  overflow: hidden;
  border-radius: 50%;
  background: var(--surface-2);
  border: 1px solid var(--border-strong);
  color: var(--text);
  font-family: var(--font-mono);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
