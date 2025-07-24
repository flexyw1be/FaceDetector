<template>
  <div class="face-details-page">
    <h1>Детали человека #{{ personId }}</h1>
    <div v-if="loading" class="loading">
      Загрузка данных...
    </div>
    <div v-else-if="personData" class="details-container">
      <div class="person-summary">
        <h2>Информация о человеке</h2>
        <div class="person-info">
          <p><strong>ID:</strong> {{ personData.person.id }}</p>
          <p><strong>Пол:</strong> {{ personData.person.gender }}</p>
          <p><strong>Возрастная группа:</strong> {{ personData.person.age_group }}</p>
          <p><strong>Количество появлений:</strong> {{ personData.person.appearance_count }}</p>
          <p><strong>Первое появление:</strong> {{ formatDate(personData.person.first_seen) }}</p>
          <p><strong>Последнее появление:</strong> {{ formatDate(personData.person.last_seen) }}</p>
        </div>
      </div>

      <div class="detections-section">
        <h2>Детекции ({{ personData.detections.length }})</h2>
        <div class="detections-list">
          <div
            v-for="detection in personData.detections"
            :key="detection.id"
            class="detection-item"
          >
            <div class="detection-info">
              <p><strong>Время в видео:</strong> {{ detection.frame_time.toFixed(2) }} сек</p>
              <p><strong>Пол:</strong> {{ detection.gender }}</p>
              <p><strong>Возраст:</strong> {{ detection.age_group }}</p>
              <p><strong>Дата обнаружения:</strong> {{ formatDate(detection.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="back-button">
      <button @click="$router.push('/results')">Назад к результатам</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'FaceDetailsPage',
  props: ['faceId'],
  data() {
    return {
      personId: this.faceId,
      personData: null,
      loading: true
    }
  },
  async mounted() {
    await this.loadPersonDetails()
  },
  methods: {
    async loadPersonDetails() {
      try {
        const response = await axios.get(`http://localhost:8000/persons/${this.personId}`)
        this.personData = response.data
        this.loading = false
      } catch (error) {
        console.error('Error loading person details:', error)
        this.loading = false
      }
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString('ru-RU')
    }
  }
}
</script>

<style scoped>
.face-details-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading {
  text-align: center;
  font-size: 18px;
  margin: 50px;
}

.details-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 30px;
}

.person-summary {
  background-color: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.person-summary h2 {
  margin-top: 0;
  color: #495057;
}

.person-info p {
  margin: 10px 0;
  font-size: 16px;
}

.detections-section h2 {
  color: #495057;
  border-bottom: 2px solid #dee2e6;
  padding-bottom: 10px;
}

.detections-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.detection-item {
  background-color: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.detection-info p {
  margin: 8px 0;
  font-size: 14px;
}

.back-button {
  margin-top: 30px;
  text-align: center;
}

.back-button button {
  background-color: #6c757d;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.back-button button:hover {
  background-color: #5a6268;
}
</style>