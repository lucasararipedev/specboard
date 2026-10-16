import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomeView from './views/HomeView.vue'
import ProjectsView from './views/ProjectsView.vue'
import BoardView from './views/BoardView.vue'
import './styles.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/projetos', component: ProjectsView },
    // Links que a IA manda: /p/<slug> e /p/<slug>?card=<id>
    { path: '/p/:slug', component: BoardView, props: true },
    // A antiga página "Conectar IA" virou a seção do prompt na página inicial.
    { path: '/conectar', redirect: { path: '/', hash: '#prompt' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(to, from, saved) {
    if (to.hash) return { el: to.hash, top: 72 }
    if (saved) return saved
    // Trocar de aba ou abrir card no board só muda a query: mantém a rolagem.
    return to.path === from.path ? false : { top: 0 }
  },
})

createApp(App).use(router).mount('#app')
