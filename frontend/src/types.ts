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
  created_at: string
  updated_at: string
}

export interface ProjectDetail extends Project {
  spec: string
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

export interface Activity {
  id: number
  project: string
  card_id: number | null
  actor: string
  kind: string
  message: string
  created_at: string
}
