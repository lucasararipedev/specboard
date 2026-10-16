// Popula a instância de demonstração (porta 8899) com projetos de exemplo, como se a IA tivesse feito.
const API = 'http://localhost:8899/api'
async function call(method, path, body, actor = 'claude') {
  const r = await fetch(API + path, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-Actor': actor },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${method} ${path}: ${r.status} ${await r.text()}`)
  return r.status === 204 ? null : r.json()
}

const spec = `# Agenda Barbearia

> Agenda online para barbearias pequenas. Spec mantida pela IA; decisões entram aqui antes de virar card.

## 1. Problema e público
Barbearias de 1 a 5 cadeiras marcam horário pelo WhatsApp e perdem cliente com conflito de horário e falta.

## 2. Escopo da v1
### 2.1 Cadastro
Barbearia, profissionais e serviços (duração e preço).
### 2.2 Agenda por profissional
Horários livres por profissional, sem conflito. Cliente marca sem criar conta.
### 2.3 Confirmação e lembrete
E-mail na hora de marcar e lembrete 1 h antes.
### 2.4 Pagamento
Sinal via Pix para reduzir falta.

## 3. Fora de escopo
App nativo, programa de fidelidade, várias unidades.

## 4. Decisões
- **Stripe** em vez de Pagar.me, pela API de assinaturas.
- Cliente não cria conta: nome e telefone bastam.

## 5. Perguntas em aberto
- Cobrança mensal ou anual no lançamento?
`

const p = await call('POST', '/projects', {
  name: 'Agenda Barbearia',
  summary: 'Agenda online para barbearias pequenas',
  repo: '~/code/agenda-barbearia',
  spec,
})
const slug = p.slug

// Perguntas iniciais: o usuário respondeu, a IA já usou.
const answers = [
  'Barbearias pequenas que marcam tudo pelo WhatsApp e perdem cliente com falta.',
  'Agenda por profissional, confirmação por e-mail e sinal via Pix.',
  'Nos próximos 3 meses',
  'App nativo e programa de fidelidade.',
  'De 5 a 15 h',
]
const starters = await call('GET', `/projects/${slug}/questions`)
for (const [i, q] of starters.entries()) {
  await call('PATCH', `/questions/${q.id}`, { answer: answers[i] }, 'user')
  await call('PATCH', `/questions/${q.id}`, { status: 'applied' })
}

const cards = {}
async function card(key, body) {
  cards[key] = await call('POST', `/projects/${slug}/cards`, body)
}
await card('cadastro', { title: 'Cadastro de barbearia e serviços', status: 'done', spec_ref: '2.1 Cadastro' })
await card('deploy', { title: 'Deploy no VPS com Docker', status: 'done', labels: ['infra'] })
await card('profs', { title: 'Cadastro de profissionais', status: 'done', spec_ref: '2.1 Cadastro' })
await card('agenda', {
  title: 'Agenda por profissional',
  status: 'doing',
  priority: 0,
  spec_ref: '2.2 Agenda',
  labels: ['back'],
  description: `Horários livres por profissional, sem conflito.

**Critérios de aceite**
- [x] grade de horários a partir da duração do serviço
- [x] bloqueio de horário já marcado
- [ ] folgas e feriados por profissional`,
})
await card('pix', {
  title: 'Sinal via Pix',
  status: 'blocked',
  priority: 1,
  spec_ref: '2.4 Pagamento',
  description: 'Esperando a aprovação da conta no Stripe.',
})
await card('login', { title: 'Login com Google quebrado', status: 'todo', priority: 1, labels: ['bug'] })
await card('email', { title: 'Confirmação de horário por e-mail', status: 'todo', spec_ref: '2.3 Confirmação' })
await card('precos', { title: 'Página de preços', status: 'todo', labels: ['front'] })
await card('fidel', { title: 'Programa de fidelidade', status: 'backlog', priority: 3 })
await card('relat', { title: 'Relatório mensal de faturamento', status: 'backlog' })
await card('multi', { title: 'Várias unidades na mesma conta', status: 'backlog', priority: 3 })

await call('POST', `/projects/${slug}/activity`, {
  message: 'Escolhemos Stripe em vez de Pagar.me pela API de assinaturas',
  kind: 'decision',
})
await call('POST', `/projects/${slug}/activity`, {
  message: 'Pix travado: conta no Stripe em análise, previsão de 2 dias',
  kind: 'note',
  card_id: cards.pix.id,
})
await call('POST', `/projects/${slug}/activity`, {
  message: 'Grade de horários e bloqueio de conflito prontos; faltam folgas',
  kind: 'note',
  card_id: cards.agenda.id,
})
await call('POST', `/projects/${slug}/questions`, {
  question: 'Cobrança mensal ou anual no lançamento?',
  context: 'Muda o card do sinal via Pix e a página de preços.',
  options: ['Só mensal', 'Mensal e anual', 'Só anual'],
  card_id: cards.precos.id,
})

// Outros projetos, para a lista não ficar vazia.
const blog = await call('POST', '/projects', {
  name: 'Blog pessoal',
  summary: 'Blog em Astro com newsletter',
  repo: '~/code/blog',
  starter_questions: false,
})
for (const [title, status] of [
  ['Tema escuro no código', 'doing'],
  ['Newsletter com Buttondown', 'todo'],
  ['Post: o que aprendi com SQLite', 'todo'],
  ['RSS', 'done'],
  ['Domínio próprio', 'done'],
]) await call('POST', `/projects/${blog.slug}/cards`, { title, status })

const api = await call('POST', '/projects', {
  name: 'API de pagamentos',
  summary: 'Freela: integração de cobrança recorrente',
  repo: '~/code/cliente-pagamentos',
  starter_questions: false,
})
for (const [title, status, priority] of [
  ['Webhook de pagamento recusado', 'doing', 1],
  ['Retry com backoff', 'todo', 2],
  ['Documentar endpoints', 'todo', 2],
  ['Ambiente de homologação', 'blocked', 1],
  ['Assinatura mensal', 'done', 2],
  ['Cupom de desconto', 'done', 2],
]) await call('POST', `/projects/${api.slug}/cards`, { title, status, priority })

console.log(JSON.stringify({ slug, cards: Object.fromEntries(Object.entries(cards).map(([k, c]) => [k, c.id])) }))
