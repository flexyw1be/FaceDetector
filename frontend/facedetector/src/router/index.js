import { createRouter, createWebHistory } from 'vue-router'
import UploadPage from '../views/UploadPage.vue'
import ProcessingPage from '../views/ProcessingPage.vue'
import ResultsPage from '../views/ResultsPage.vue'
import FaceDetailsPage from '../views/FaceDetailsPage.vue'
import ErrorPage from '../views/ErrorPage.vue'

const routes = [
  { path: '/', name: 'Upload', component: UploadPage },
  { path: '/processing', name: 'Processing', component: ProcessingPage, props: true },
  { path: '/results', name: 'Results', component: ResultsPage },
  { path: '/face/:faceId', name: 'FaceDetails', component: FaceDetailsPage },
  { path: '/error', name: 'Error', component: ErrorPage }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
