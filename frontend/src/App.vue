<script setup lang="ts">
import { ref } from 'vue'
import { needsToken, setToken } from './api'

const token = ref('')

function saveToken() {
  setToken(token.value.trim())
  location.reload()
}
</script>

<template>
  <header class="topbar">
    <RouterLink to="/" class="brand">
      <img src="/favicon.svg" alt="" width="22" height="22" />
      Specboard
    </RouterLink>
    <nav>
      <RouterLink to="/" class="btn ghost">Projetos</RouterLink>
      <RouterLink to="/conectar" class="btn ghost">Conectar IA</RouterLink>
    </nav>
  </header>

  <form v-if="needsToken" class="token-bar" @submit.prevent="saveToken">
    <span>Esta instância exige token (<code>SPECBOARD_TOKEN</code> no <code>.env</code>).</span>
    <input v-model="token" type="password" placeholder="Cole o token" autocomplete="off" />
    <button class="btn primary">Salvar</button>
  </form>

  <RouterView />
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 650;
  color: var(--text);
  text-decoration: none;
}

nav {
  display: flex;
  gap: 4px;
}

nav .router-link-exact-active {
  background: var(--surface-2);
}

.token-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--warn-soft);
  color: var(--warn);
}

.token-bar input {
  width: auto;
  flex: 1;
  min-width: 180px;
}
</style>
