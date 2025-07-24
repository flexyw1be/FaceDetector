<template>
  <div class="results-page">
    <h1>Результаты анализа</h1>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Загрузка результатов...</p>
    </div>

    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else class="results-container">
      <div class="summary">
        <h2>Статистика видео</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <h3>{{ results.total_persons }}</h3>
            <p>Уникальных людей</p>
          </div>
          <div class="stat-card">
            <h3>{{ results.total_detections }}</h3>
            <p>Всего детекций</p>
          </div>
          <div class="stat-card">
            <h3>{{ results.persons.length }}</h3>
            <p>Персоны с детекциями</p>
          </div>
        </div>
      </div>

      <div v-if="results.persons && results.persons.length > 0" class="persons-section">
        <h2>Найденные персоны</h2>
        <div class="persons-grid">
          <div
            v-for="personData in results.persons"
            :key="personData.person.id"
            class="person-card"
          >
            <div class="person-header">
              <h3>Персона #{{ personData.person.id }}</h3>
              <div class="person-stats">
                <span class="stat-item">
                  <strong>Пол:</strong> {{ personData.person.gender }}
                </span>
                <span class="stat-item">
                  <strong>Возраст:</strong> {{ personData.person.age_group }}
                </span>
                <span class="stat-item">
                  <strong>Появлений:</strong> {{ personData.person.appearance_count }}
                </span>
              </div>
            </div>

            <div class="detections-section">
              <h4>Детекции ({{ personData.detections.length }})</h4>
              <div class="detections-grid">
                <div
                  v-for="detection in personData.detections"
                  :key="detection.id"
                  class="detection-card"
                >
                  <div class="face-image-container">
                    <img
                      :src="detection.face_image"
                      :alt="`Лицо персоны ${personData.person.id}`"
                      class="face-image"
                      @error="handleImageError"
                    />
                  </div>
                  <div class="detection-info">
                    <p><strong>Время:</strong> {{ detection.frame_time.toFixed(2) }} сек</p>
                    <p><strong>Пол:</strong> {{ detection.gender }}</p>
                    <p><strong>Возраст:</strong> {{ detection.age_group }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="no-results">
        <h3>Лица не найдены</h3>
        <p>Попробуйте загрузить другое видео или настроить параметры детекции.</p>
      </div>
    </div>

    <div class="back-button">
      <button @click="$router.push('/')">Загрузить другое видео</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ResultsPage',
  data() {
    return {
      results: {
        persons: [],
        total_persons: 0,
        total_detections: 0
      },
      loading: true,
      error: ''
    }
  },
  async mounted() {
    await this.loadResults()
  },
  methods: {
    async loadResults() {
      try {
        this.loading = true
        this.error = ''

        const response = await axios.get('http://localhost:8000/results/')
        this.results = response.data
        console.log('Results:', response.data)
      } catch (error) {
        console.error('Error loading results:', error)
        this.error = error.response?.data?.detail || 'Ошибка загрузки результатов'
      } finally {
        this.loading = false
      }
    },
    handleImageError(event) {
      event.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2NjYyIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1zaXplPSIxMiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzk5OSI+Tm8gSW1hZ2U8L3RleHQ+PC9zdmc+'
    }
  }
}
</script>

<style scoped>
.results-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.loading {
  text-align: center;
  padding: 50px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #f5c6cb;
  margin: 20px 0;
}

.summary {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.summary h2 {
  margin-top: 0;
  color: #495057;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 15px;
}

.stat-card {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-card h3 {
  margin: 0 0 10px 0;
  font-size: 2em;
  color: #007bff;
}

.stat-card p {
  margin: 0;
  color: #6c757d;
}

.persons-section h2 {
  color: #495057;
  margin-bottom: 20px;
}

.persons-grid {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.person-card {
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.person-header {
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 15px;
  margin-bottom: 20px;
}

.person-header h3 {
  margin: 0 0 15px 0;
  color: #495057;
}

.person-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.stat-item {
  background-color: #e9ecef;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 14px;
}

.detections-section h4 {
  margin: 0 0 15px 0;
  color: #6c757d;
}

.detections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.detection-card {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  overflow: hidden;
  transition: transform 0.2s;
}

.detection-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.face-image-container {
  width: 100%;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f0f0;
  overflow: hidden;
}

.face-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-bottom: 2px solid #dee2e6;
}

.detection-info {
  padding: 15px;
}

.detection-info p {
  margin: 5px 0;
  font-size: 13px;
  color: #495057;
}

.no-results {
  text-align: center;
  padding: 50px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.no-results h3 {
  color: #6c757d;
  margin-bottom: 10px;
}

.back-button {
  margin-top: 30px;
  text-align: center;
}

.back-button button {
  background-color: #6c757d;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.back-button button:hover {
  background-color: #5a6268;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .person-stats {
    flex-direction: column;
    gap: 10px;
  }

  .detections-grid {
    grid-template-columns: 1fr;
  }
}
</style>