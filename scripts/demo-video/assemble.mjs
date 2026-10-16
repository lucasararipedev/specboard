// Junta os quadros do screencast num MP4: respeita o tempo real entre quadros, encolhe as esperas do
// polling e acelera tudo um pouco.
import fs from 'node:fs'
import { execFileSync } from 'node:child_process'
import ffmpeg from 'ffmpeg-static'

const SPEED = Number(process.env.SPEED || 1.3)
const { frames, cuts, tEnd } = JSON.parse(fs.readFileSync('timeline.json'))
const inCut = (t) => cuts.find(([a, b]) => t >= a && t < b)
let list = ''
let total = 0
frames.forEach((f, i) => {
  const next = i + 1 < frames.length ? frames[i + 1].t : tEnd
  let d = Math.max(0, next - f.t)
  const cut = inCut(f.t)
  if (cut) d *= 0.35 / (cut[1] - cut[0])
  d /= SPEED
  total += d
  list += `file '${f.file}'\nduration ${d.toFixed(4)}\n`
})
list += `file '${frames.at(-1).file}'\n`
fs.writeFileSync('frames.txt', list)
const out = process.env.OUT || 'demo.mp4'
execFileSync(ffmpeg, [
  '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'frames.txt',
  '-vf', 'fps=30,scale=1600:900:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24',
  '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', out,
])
console.log(out, total.toFixed(1) + 's', (fs.statSync(out).size / 1e6).toFixed(2) + ' MB')
