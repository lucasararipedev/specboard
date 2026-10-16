import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import ProjectsView from './views/ProjectsView.vue'
import BoardView from './views/BoardView.vue'
import ConnectView from './views/ConnectView.vue'
import './styles.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: ProjectsView },
    // Links que a IA manda: /p/<slug> e /p/<slug>?card=<id>
    { path: '/p/:slug', component: BoardView, props: true },
    { path: '/conectar', component: ConnectView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

createApp(App).use(router).mount('#app')
