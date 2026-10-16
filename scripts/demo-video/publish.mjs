// Copia o vídeo montado para o front: MP4 (H.264), WebM (VP9) e o poster.
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import ffmpeg from 'ffmpeg-static'

const pub = '../../frontend/public'
fs.copyFileSync('demo.mp4', `${pub}/demo.mp4`)
const run = (...args) => execFileSync(ffmpeg, ['-y', '-loglevel', 'error', ...args])
run('-i', 'demo.mp4', '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '38', '-row-mt', '1', '-an', `${pub}/demo.webm`)
run('-ss', '3.2', '-i', 'demo.mp4', '-frames:v', '1', '-q:v', '4', `${pub}/demo-poster.jpg`)
console.log('publicado em frontend/public')
