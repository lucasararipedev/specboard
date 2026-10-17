<script setup lang="ts">
import { ref, watch } from 'vue'
import { api } from '../api'
import { profile } from '../profile'
import UserAvatar from '../components/UserAvatar.vue'

// A foto é reduzida no navegador antes de salvar: fica pequena no banco e no backup.
const AVATAR_PX = 160

const name = ref(profile.value.name)
const avatar = ref(profile.value.avatar)
const saving = ref(false)
const saved = ref(false)
const error = ref('')

// O perfil pode chegar depois desta tela abrir (carregado pelo App).
watch(profile, (p) => {
  name.value = p.name
  avatar.value = p.avatar
})

function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Não consegui ler essa imagem'))
    img.src = URL.createObjectURL(file)
  })
}

async function pickPhoto(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  error.value = ''
  try {
    const img = await loadImage(file)
    // Recorte quadrado do centro, reduzido para AVATAR_PX.
    const side = Math.min(img.naturalWidth, img.naturalHeight)
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = AVATAR_PX
    canvas.getContext('2d')!.drawImage(
      img,
      (img.naturalWidth - side) / 2,
      (img.naturalHeight - side) / 2,
      side,
      side,
      0,
      0,
      AVATAR_PX,
      AVATAR_PX,
    )
    URL.revokeObjectURL(img.src)
    const webp = canvas.toDataURL('image/webp', 0.85)
    avatar.value = webp.startsWith('data:image/webp') ? webp : canvas.toDataURL('image/jpeg', 0.85)
  } catch (err) {
    error.value = (err as Error).message
  }
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    profile.value = await api.saveProfile({ name: name.value.trim(), avatar: avatar.value })
    saved.value = true
    setTimeout(() => (saved.value = false), 1500)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <main class="page profile-page">
    <h1>Perfil</h1>
    <p class="muted">Aparece no histórico e no topo, e a IA passa a te chamar pelo nome. Fica só na sua máquina.</p>

    <form class="panel form" @submit.prevent="save">
      <div class="photo">
        <UserAvatar :name="name" :src="avatar" :size="72" />
        <div class="photo-actions">
          <label class="btn small upload">
            Escolher foto
            <input type="file" accept="image/png,image/jpeg,image/webp" @change="pickPhoto" />
          </label>
          <button v-if="avatar" type="button" class="btn ghost small" @click="avatar = ''">Remover</button>
        </div>
      </div>

      <label>Nome <input v-model="name" maxlength="100" placeholder="Como você quer ser chamado" /></label>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="actions">
        <button class="btn primary" :disabled="saving">{{ saved ? 'Salvo' : saving ? 'Salvando…' : 'Salvar' }}</button>
      </div>
    </form>
  </main>
</template>

<style scoped>
.profile-page {
  max-width: 560px;
}

.profile-page > p {
  margin: 6px 0 20px;
}

.form {
  display: grid;
  gap: 16px;
  padding: 18px;
}

.photo {
  display: flex;
  align-items: center;
  gap: 16px;
}

.photo-actions {
  display: flex;
  gap: 6px;
}

.upload {
  position: relative;
  overflow: hidden;
}

.upload input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.actions {
  display: flex;
  justify-content: flex-end;
}
</style>
