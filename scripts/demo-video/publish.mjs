// Copia o vídeo montado para o front (MP4 H.264, WebM VP9, poster) e gera o GIF do README.
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import ffmpeg from 'ffmpeg-static'

const pub = '../../frontend/public'
fs.copyFileSync('demo.mp4', `${pub}/demo.mp4`)
const run = (...args) => execFileSync(ffmpeg, ['-y', '-loglevel', 'error', ...args])
run('-i', 'demo.mp4', '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '38', '-row-mt', '1', '-an', `${pub}/demo.webm`)
run('-ss', '3.2', '-i', 'demo.mp4', '-frames:v', '1', '-q:v', '4', `${pub}/demo-poster.jpg`)
// GIF do README: 1,5× mais rápido, 800 px, 10 fps, paleta só com as cores que mudam (fica abaixo de 10 MB).
run('-i', 'demo.mp4', '-filter_complex',
  'setpts=PTS/1.5,fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];' +
  '[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle',
  '../../docs/demo.gif')
console.log('publicado em frontend/public e docs/demo.gif')
