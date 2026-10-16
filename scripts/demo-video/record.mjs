// Grava o vídeo de demonstração do Specboard (veja README.md): navega na instância de demo (porta 8899)
// com cursor, zoom e legendas desenhados na página, capturando quadros via CDP screencast.
import { chromium } from 'playwright'
import fs from 'node:fs'

const BASE = 'http://localhost:8899'
const API = BASE + '/api'
const W = 1280
const H = 720
const OUT = 'frames'

fs.rmSync(OUT, { recursive: true, force: true })
fs.mkdirSync(OUT)

const overlay = () => {
  const css = `
    html, body { overflow: hidden !important; }
    #app { transform-origin: 0 0; transition: transform .85s cubic-bezier(.25,.8,.25,1); overflow: clip; }
    #demo-cursor { position: fixed; left: 0; top: 0; z-index: 99999; pointer-events: none;
      width: 30px; height: 30px; transform: translate(640px, 420px);
      transition: transform var(--move, .6s) cubic-bezier(.3,.7,.2,1); }
    #demo-cursor svg { display: block; filter: drop-shadow(0 2px 0 rgba(0,0,0,.25)); }
    #demo-ripple { position: fixed; z-index: 99998; pointer-events: none; width: 44px; height: 44px;
      margin: -22px 0 0 -22px; border-radius: 50%; border: 2.5px solid #c8462b; opacity: 0; }
    #demo-ripple.on { animation: demo-ripple .45s ease-out; }
    @keyframes demo-ripple { from { opacity: .9; transform: scale(.3); } to { opacity: 0; transform: scale(1.2); } }
    #demo-caption { position: fixed; left: 50%; bottom: 34px; z-index: 99997; pointer-events: none;
      display: flex; align-items: center; gap: 12px; padding: 13px 22px 13px 14px;
      background: #26221e; color: #f3eee4; border-radius: 10px; box-shadow: 0 3px 0 #000;
      font: 500 22px/1.3 'Instrument Sans Variable', system-ui, sans-serif;
      opacity: 0; transform: translate(-50%, 12px); transition: opacity .3s ease-out, transform .3s ease-out; }
    #demo-caption.on { opacity: 1; transform: translate(-50%, 0); }
    #demo-caption b { font: 500 13px/1 'JetBrains Mono Variable', monospace; padding: 6px 8px; border-radius: 5px;
      background: #c8462b; color: #fff; letter-spacing: .02em; }
    #demo-chat { position: fixed; right: 28px; top: 78px; z-index: 99997; pointer-events: none; width: 400px;
      padding: 14px 16px; background: #fbf9f4; border: 1px solid #c9bda6; border-radius: 10px;
      box-shadow: 0 3px 0 #c9bda6; font: 17px/1.45 'Instrument Sans Variable', system-ui, sans-serif; color: #26221e;
      opacity: 0; transform: translateY(-10px); transition: opacity .3s ease-out, transform .3s ease-out; }
    #demo-chat.on { opacity: 1; transform: none; }
    #demo-chat span { display: inline-block; margin-bottom: 6px; padding: 2px 7px; border-radius: 4px;
      background: #26221e; color: #f3eee4; font: 12px/1.5 'JetBrains Mono Variable', monospace; }
  `
  addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style')
    style.textContent = css
    document.head.appendChild(style)
    document.body.insertAdjacentHTML(
      'beforeend',
      `<div id="demo-cursor"><svg width="30" height="30" viewBox="0 0 24 24"><path d="M4 2.5 L4 19.5 L8.6 15.4 L11.6 22 L14.6 20.6 L11.7 14.2 L18 14.2 Z" fill="#26221e" stroke="#fbf9f4" stroke-width="1.6" stroke-linejoin="round"/></svg></div>
       <div id="demo-ripple"></div><div id="demo-caption"></div><div id="demo-chat"></div>`,
    )
  })
}

const browser = await chromium.launch()
const context = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1.5 })
await context.addInitScript(overlay)
const page = await context.newPage()
const cdp = await context.newCDPSession(page)

const frames = []
cdp.on('Page.screencastFrame', async ({ data, metadata, sessionId }) => {
  const file = `${OUT}/${String(frames.length).padStart(5, '0')}.jpg`
  fs.writeFileSync(file, Buffer.from(data, 'base64'))
  frames.push({ file, t: metadata.timestamp })
  await cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => {})
})

const cuts = [] // trechos de espera (polling) que viram quase nada na edição
const now = () => Date.now() / 1000
const wait = (ms) => page.waitForTimeout(ms)
let cursor = { x: 640, y: 420 }

async function api(method, path, body) {
  const r = await fetch(API + path, {
    method,
    headers: { 'Content-Type': 'application/json', 'X-Actor': 'claude' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`${method} ${path}: ${r.status}`)
  return r.json()
}

async function move(x, y, ms = 650) {
  const dist = Math.hypot(x - cursor.x, y - cursor.y)
  ms = Math.max(280, Math.min(ms, 260 + dist * 0.9))
  await page.evaluate(
    ([x, y, ms]) => {
      const c = document.getElementById('demo-cursor')
      c.style.setProperty('--move', ms + 'ms')
      c.style.transform = `translate(${x - 4}px, ${y - 3}px)`
    },
    [x, y, ms],
  )
  await page.mouse.move(x, y, { steps: 12 })
  cursor = { x, y }
  await wait(ms + 40)
}

async function ripple() {
  await page.evaluate(([x, y]) => {
    const r = document.getElementById('demo-ripple')
    r.style.left = x + 'px'
    r.style.top = y + 'px'
    r.classList.remove('on')
    void r.offsetWidth
    r.classList.add('on')
  }, [cursor.x, cursor.y])
}

async function centerOf(locator) {
  const b = await locator.boundingBox()
  return { x: b.x + b.width / 2, y: b.y + b.height / 2 }
}

async function click(locator, { pause = 250 } = {}) {
  const { x, y } = await centerOf(locator)
  await move(x, y)
  await wait(120)
  await ripple()
  await page.mouse.down()
  await page.mouse.up()
  await wait(pause)
}

async function caption(text, tag = '') {
  await page.evaluate(
    ([text, tag]) => {
      const c = document.getElementById('demo-caption')
      c.classList.remove('on')
      setTimeout(() => {
        c.innerHTML = (tag ? `<b>${tag}</b>` : '') + text
        if (text) c.classList.add('on')
      }, text && c.innerHTML ? 220 : 0)
    },
    [text, tag],
  )
}

async function chat(text) {
  await page.evaluate((text) => {
    const c = document.getElementById('demo-chat')
    if (!text) return c.classList.remove('on')
    c.innerHTML = `<span>claude</span><br>${text}`
    c.classList.add('on')
  }, text)
}

/** Zoom de câmera: leva o ponto (x, y) da tela para o centro, sem mostrar borda vazia. */
async function zoom(s, x = W / 2, y = H / 2) {
  const t = await page.evaluate(
    ([s, x, y, W, H]) => {
      const app = document.getElementById('app')
      const sy = scrollY
      const docH = app.scrollHeight
      let tx = W / 2 - x * s
      let ty = sy + H / 2 - (y + sy) * s
      tx = Math.min(0, Math.max(W - W * s, tx))
      ty = Math.min(sy - sy * s, Math.max(sy + H - Math.max(docH, sy + H) * s, ty))
      if (s === 1) tx = ty = 0
      app.style.transform = s === 1 ? '' : `translate(${tx}px, ${ty}px) scale(${s})`
      return { tx, ty: ty - sy + sy * s }
    },
    [s, x, y, W, H],
  )
  await wait(950)
  return t
}

/** Onde um ponto da página aparece com o zoom aplicado (para o cursor apontar). */
function zoomed(p, s, t) {
  return { x: p.x * s + t.tx, y: p.y * s + t.ty }
}

async function waitForAi(selector) {
  const start = now()
  await page.waitForSelector(selector, { timeout: 8000 })
  cuts.push([start, now()])
  await wait(150)
}

// ─── Roteiro ────────────────────────────────────────────────────────────────

await page.goto(BASE + '/projetos', { waitUntil: 'networkidle' })
await wait(400)
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 90, maxWidth: W * 1.5, maxHeight: H * 1.5 })
const t0 = now()
await wait(500)

// 1. Lista de projetos
await caption('Seus projetos num lugar só')
await move(520, 300, 600)
await wait(350)
const agenda = page.locator('.project', { hasText: 'Agenda Barbearia' })
await click(agenda, { pause: 500 })
await page.waitForSelector('.columns')
await wait(500)

// 2. Board
await caption('Um kanban por projeto, com a spec por trás')
await wait(500)
const doingCard = page.locator('.card', { hasText: 'Agenda por profissional' })
let p = await centerOf(doingCard)
await move(p.x + 40, p.y + 30)
let t = await zoom(1.9, p.x, p.y + 10)
await move(...Object.values(zoomed({ x: p.x + 50, y: p.y + 40 }, 1.9, t)))
await wait(1000)
await zoom(1)
await move(p.x + 50, p.y + 60, 300)

// 3. A IA trabalha
await caption('Enquanto você conversa com ela, a IA atualiza o board', 'IA')
await chat('Corrigi o login com Google e criei o card do lembrete por WhatsApp.')
await api('PATCH', '/cards/6', { status: 'done' })
await api('POST', '/projects/agenda-barbearia/cards', {
  title: 'Lembrete por WhatsApp 1 h antes',
  status: 'todo',
  priority: 1,
  spec_ref: '2.3 Confirmação',
  labels: ['back'],
})
await waitForAi('.card:has-text("Lembrete por WhatsApp")')
await wait(400)
const newCard = page.locator('.card', { hasText: 'Lembrete por WhatsApp' })
p = await centerOf(newCard)
t = await zoom(1.7, p.x + 120, p.y)
await move(...Object.values(zoomed({ x: p.x + 30, y: p.y + 20 }, 1.7, t)))
await wait(1100)
const loginDone = page.locator('.card', { hasText: 'Login com Google' })
const q = await centerOf(loginDone)
t = await zoom(1.7, q.x - 100, q.y)
await move(...Object.values(zoomed({ x: q.x + 30, y: q.y + 20 }, 1.7, t)))
await wait(1100)
await chat('')
await zoom(1)

// 4. Arrastar
await caption('Você também mexe: é só arrastar')
const precos = page.locator('.card', { hasText: 'Página de preços' })
p = await centerOf(precos)
await move(p.x, p.y)
await wait(150)
await page.mouse.down()
const doingCol = page.locator('.column').nth(2)
const box = await doingCol.boundingBox()
const dest = { x: box.x + box.width / 2, y: (await doingCard.boundingBox()).y + 110 }
await page.evaluate(([x, y]) => {
  const c = document.getElementById('demo-cursor')
  c.style.setProperty('--move', '900ms')
  c.style.transform = `translate(${x - 4}px, ${y - 3}px)`
}, [dest.x, dest.y])
await page.mouse.move(dest.x, dest.y, { steps: 30 })
cursor = dest
await wait(300)
await page.mouse.up()
await wait(900)

// 5. Card aberto
await caption('Cada card guarda contexto e histórico')
await click(doingCard, { pause: 700 })
const modal = page.locator('.modal')
await modal.waitFor()
const desc = page.locator('.modal .preview')
p = await centerOf(desc)
await move(p.x + 80, p.y + 10)
t = await zoom(1.6, p.x + 60, p.y + 60)
await wait(1300)
await zoom(1)
await page.evaluate(() => document.querySelector('.modal .history')?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
await wait(1200)
await click(page.getByRole('button', { name: 'Fechar' }), { pause: 500 })

// 6. Spec
await caption('A spec é a fonte da verdade: decisões entram nela primeiro')
await click(page.locator('.tabs button', { hasText: 'Spec' }), { pause: 600 })
await page.evaluate(() => scrollTo({ top: 420, behavior: 'smooth' }))
await wait(1200)
const decisoes = page.locator('.markdown h2', { hasText: 'Decisões' })
p = await centerOf(decisoes)
const md = await page.locator('.markdown').boundingBox()
t = await zoom(1.7, md.x + 330, p.y + 40)
await move(...Object.values(zoomed({ x: md.x + 360, y: p.y + 48 }, 1.7, t)))
await wait(1300)
await zoom(1)
await page.evaluate(() => scrollTo({ top: 0, behavior: 'smooth' }))
await wait(700)

// 7. Perguntas
await caption('A IA pergunta em vez de supor. Você responde num clique')
await click(page.locator('.tabs button', { hasText: 'Perguntas' }), { pause: 700 })
const question = page.locator('.question').first()
p = await centerOf(question)
t = await zoom(1.5, p.x, p.y)
await wait(1100)
await zoom(1)
await click(page.locator('.option', { hasText: 'Mensal e anual' }), { pause: 400 })
await click(page.getByRole('button', { name: 'Responder' }), { pause: 1000 })

// 8. Atividade
await caption('Tudo registrado: quem fez o quê, e quando')
await click(page.locator('.tabs button', { hasText: 'Atividade' }), { pause: 700 })
const list = page.locator('.activity ul')
p = await centerOf(list)
const lb = await list.boundingBox()
await move(lb.x + 300, lb.y + 70)
await zoom(1.5, lb.x + 420, lb.y + 120)
await wait(1400)
await zoom(1)

// 9. Fim
await click(page.locator('.tabs button', { hasText: 'Board' }), { pause: 500 })
await caption('Specboard · open source · roda na sua máquina')
await move(W - 200, H - 160, 800)
await wait(1800)

await cdp.send('Page.stopScreencast')
const tEnd = now()
fs.writeFileSync('timeline.json', JSON.stringify({ frames, cuts, t0, tEnd }))
console.log('frames', frames.length, 'cuts', cuts.map(([a, b]) => (b - a).toFixed(1)), 'dur', (tEnd - t0).toFixed(1))
await browser.close()
