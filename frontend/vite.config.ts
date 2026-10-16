import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Em dev o Vite (5173) repassa a API para o FastAPI. No Docker de dev o alvo é o serviço "api".
const target = process.env.VITE_API_TARGET || 'http://localhost:8787'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': target,
      '/llms.txt': target,
      '/docs': target,
      '/openapi.json': target,
    },
  },
})
