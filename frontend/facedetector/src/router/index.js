import { createRouter, createWebHistory } from 'vue-router'

import UploadPage from '@/views/UploadPage.vue'
import ProcessingPage from '@/views/ProcessingPage.vue'
import ResultsPage from '@/views/ResultsPage.vue'

const routes = [
  { path: '/upload-video', name: 'UploadPage', component: UploadPage },
  { path: '/', redirect: '/upload-video' },
  { path: '/processing', name: 'Processing', component: ProcessingPage },
  { path: '/results', name: 'Results', component: ResultsPage }
]


const routes = [
  {
    path: '/upload-video',
    name: 'UploadPage',
    component: UploadPage
  },
  {
    path: '/',
    redirect: '/upload-video' // ← Главная страница перенаправляет на /upload-video
  },
  {
    path: '/processing',
    name: 'Processing',
    component: ProcessingPage
  },
  {
    path: '/results',
    name: 'Results',
    component: ResultsPage
  },
  {
    path: '/face/:faceId',
    name: 'FaceDetails',
    component: FaceDetailsPage,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router