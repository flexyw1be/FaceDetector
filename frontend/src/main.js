import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/main.css'

// Создаем Vue приложение
const app = createApp(App)

// Используем роутер
app.use(router)

// Монтируем приложение
app.mount('#app')

// Глобальная обработка ошибок
app.config.errorHandler = (err, vm, info) => {
    console.error('Ошибка Vue:', err, info)
    // Здесь можно добавить отправку ошибок в систему мониторинга
}

// Глобальные свойства (по желанию)
app.config.globalProperties.$filters = {
    formatDate(value) {
        if (!value) return ''
        return new Date(value).toLocaleString()
    }
}