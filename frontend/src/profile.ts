import { ref } from 'vue'
import { api } from './api'
import type { Profile } from './types'

/** Perfil do usuário, carregado uma vez e compartilhado pelo topo, histórico e página de perfil. */
export const profile = ref<Profile>({ name: '', avatar: '', updated_at: null })

export async function loadProfile(): Promise<void> {
  try {
    profile.value = await api.profile()
  } catch {
    // sem perfil (ou sem token ainda): fica o padrão
  }
}

/** Nome para mostrar no histórico: a interface grava "user"; as IAs, o próprio nome. */
export function actorName(actor: string): string {
  return actor === 'user' ? profile.value.name || 'você' : actor
}
