import { createRouter, createWebHistory } from 'vue-router'
import UploadPage from '@/views/UploadPage.vue'
import ProcessingPage from '@/views/ProcessingPage.vue'
import ResultsPage from '@/views/ResultsPage.vue'

// Only ONE routes declaration
const routes = [
    {
        path: '/',
        name: 'Upload',
        component: UploadPage
    },
    {
        path: '/processing/:videoId',
        name: 'Processing',
        component: ProcessingPage,
        props: true
    },
    {
        path: '/results/:videoId',
        name: 'Results',
        component: ResultsPage,
        props: true
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes // Use the single routes array
})

export default router