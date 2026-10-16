import { ref } from 'vue'
import type { Activity, Card, Project, ProjectDetail, Question } from './types'

const TOKEN_KEY = 'specboard-token'

/** Vira true quando a API responde 401: o App mostra o campo de token. */
export const needsToken = ref(false)

let memoryToken = ''

export function getToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) || ''
  } catch {
    return ''
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Sem storage (aba anônima): o token vale só até recarregar.
  }
  memoryToken = token
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  // A interface se identifica como "user"; as IAs mandam o próprio nome.
  const headers: Record<string, string> = { 'X-Actor': 'user' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = getToken() || memoryToken
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  if (res.status === 401) needsToken.value = true
  if (!res.ok) {
    let message = `Erro ${res.status}`
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      // resposta sem JSON
    }
    throw new ApiError(res.status, message)
  }
  if (res.status === 204) return undefined as T
  const type = res.headers.get('content-type') || ''
  return (type.includes('json') ? res.json() : res.text()) as Promise<T>
}

export const api = {
  projects: (includeArchived = false) =>
    request<Project[]>('GET', `/api/projects${includeArchived ? '?include_archived=true' : ''}`),
  createProject: (body: { name: string; summary?: string; repo?: string }) =>
    request<ProjectDetail>('POST', '/api/projects', body),
  project: (slug: string) => request<ProjectDetail>('GET', `/api/projects/${slug}`),
  updateProject: (slug: string, patch: Partial<ProjectDetail>) =>
    request<ProjectDetail>('PATCH', `/api/projects/${slug}`, patch),

  cards: (slug: string) => request<Card[]>('GET', `/api/projects/${slug}/cards`),
  createCard: (slug: string, body: Partial<Card> & { title: string }) =>
    request<Card>('POST', `/api/projects/${slug}/cards`, body),
  updateCard: (id: number, patch: Partial<Card>) => request<Card>('PATCH', `/api/cards/${id}`, patch),
  deleteCard: (id: number) => request<void>('DELETE', `/api/cards/${id}`),

  questions: (slug: string) => request<Question[]>('GET', `/api/projects/${slug}/questions`),
  updateQuestion: (id: number, patch: Partial<Pick<Question, 'answer' | 'status'>>) =>
    request<Question>('PATCH', `/api/questions/${id}`, patch),

  activity: (slug: string, opts: { limit?: number; cardId?: number } = {}) => {
    const params = new URLSearchParams({ limit: String(opts.limit ?? 100) })
    if (opts.cardId) params.set('card_id', String(opts.cardId))
    return request<Activity[]>('GET', `/api/projects/${slug}/activity?${params}`)
  },
  logActivity: (slug: string, body: { message: string; kind?: 'note' | 'decision'; card_id?: number }) =>
    request<Activity>('POST', `/api/projects/${slug}/activity`, body),

  prompt: () => request<string>('GET', '/api/agent/prompt'),
}
