export type Status = 'backlog' | 'todo' | 'doing' | 'blocked' | 'done'

export const STATUSES: Status[] = ['backlog', 'todo', 'doing', 'blocked', 'done']

export const STATUS_LABEL: Record<Status, string> = {
  backlog: 'Backlog',
  todo: 'A fazer',
  doing: 'Fazendo',
  blocked: 'Travado',
  done: 'Feito',
}

export const PRIORITY_LABEL: Record<number, string> = {
  0: 'P0 · urgente',
  1: 'P1 · alta',
  2: 'P2 · normal',
  3: 'P3 · algum dia',
}

export interface Project {
  id: number
  slug: string
  name: string
  summary: string
  repo: string
  archived: boolean
  url: string
  counts: Record<Status, number>
  open_questions: number
  created_at: string
  updated_at: string
}

export interface ProjectDetail extends Project {
  spec: string
  /** Etiquetas em uso no projeto, com quantos cards têm cada uma. */
  labels: Record<string, number>
}

export interface Card {
  id: number
  project: string
  title: string
  description: string
  status: Status
  priority: number
  position: number
  labels: string[]
  spec_ref: string
  due_date: string | null
  url: string
  created_at: string
  updated_at: string
  started_at: string | null
  done_at: string | null
}

export type QuestionStatus = 'open' | 'answered' | 'applied' | 'dismissed'

export interface Question {
  id: number
  project: string
  card_id: number | null
  question: string
  context: string
  options: string[]
  answer: string
  status: QuestionStatus
  asked_by: string
  url: string
  created_at: string
  answered_at: string | null
}

export interface Activity {
  id: number
  project: string
  card_id: number | null
  actor: string
  kind: string
  message: string
  created_at: string
}

export interface Profile {
  name: string
  avatar: string
  updated_at: string | null
}

/** Um chat ou agente ligado ao board (/board): aparece no painel Agora. */
export interface AgentSession {
  key: string
  actor: string
  client: string
  project: string | null
  project_url: string | null
  cwd: string
  doing: string
  card_id: number | null
  card_title: string | null
  card_url: string | null
  active: boolean
  idle: boolean
  started_at: string
  last_seen_at: string
  ended_at: string | null
}
