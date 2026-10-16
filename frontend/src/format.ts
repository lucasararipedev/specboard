const rtf = new Intl.RelativeTimeFormat('pt-BR', { numeric: 'auto' })

/** "há 5 min", "ontem", "há 3 dias". */
export function timeAgo(iso: string): string {
  const seconds = (new Date(iso).getTime() - Date.now()) / 1000
  const steps: [Intl.RelativeTimeFormatUnit, number][] = [
    ['second', 60],
    ['minute', 60],
    ['hour', 24],
    ['day', 30],
    ['month', 12],
  ]
  let value = seconds
  for (const [unit, size] of steps) {
    if (Math.abs(Math.round(value)) < size) return rtf.format(Math.round(value), unit)
    value /= size
  }
  return rtf.format(Math.round(value), 'year')
}

export function formatDate(isoDate: string): string {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

export function isOverdue(isoDate: string | null): boolean {
  if (!isoDate) return false
  const today = new Date()
  const local = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  return isoDate < local
}
