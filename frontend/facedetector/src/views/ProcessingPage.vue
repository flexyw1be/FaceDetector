<template>
  <div class="processing-page">
    <h1>Обработка видео</h1>

    <!-- Статус моделей -->
    <div class="models-status" v-if="modelsStatus">
      <h3>Статус моделей:</h3>
      <div class="status-grid">
        <div class="status-item" :class="{ 'loaded': modelsStatus.face_detection }">
          Детекция лиц: {{ modelsStatus.face_detection ? '✓ Загружена' : '✗ Не загружена' }}
        </div>
        <div class="status-item" :class="{ 'loaded': modelsStatus.gender_detection }">
          Определение пола: {{ modelsStatus.gender_detection ? '✓ Загружена' : '✗ Не загружена' }}
        </div>
        <div class="status-item" :class="{ 'loaded': modelsStatus.age_detection }">
          Определение возраста: {{ modelsStatus.age_detection ? '✓ Загружена' : '✗ Не загружена' }}
        </div>
      </div>
    </div>

    <!-- Тестовая кнопка -->
    <div class="test-section">
      <button @click="testFrame" class="test-button">
        Тест детекции
      </button>
      <div v-if="testResult" class="test-result">
        <p>Тестовый кадр: {{ testResult.detected_faces }} лиц найдено</p>
        <p v-if="testResult.face_boxes.length > 0">
          Координаты: {{ testResult.face_boxes }}
        </p>
      </div>
    </div>

    <div class="video-container">
      <img
        :src="videoStreamUrl"
        alt="Video Stream"
        class="video-stream"
        @error="handleStreamError"
        v-if="streamLoaded"
      />
      <div v-else class="loading-stream">
        <p>Загрузка видеопотока...</p>
        <div class="spinner"></div>
      </div>
    </div>

    <div class="controls">
      <button @click="processVideo" :disabled="processing" class="process-button">
        {{ processing ? 'Анализ...' : 'Анализировать видео' }}
      </button>
      <button @click="checkResults" class="results-button">
        Проверить результаты
      </button>
    </div>

    <!-- Результаты обработки -->
    <div v-if="processingResult" class="processing-result">
      <h3>Результаты обработки:</h3>
      <p>Обработано кадров: {{ processingResult.total_frames }}</p>
      <p>Найдено лиц: {{ processingResult.detections_count }}</p>
      <div v-if="processingResult.results && processingResult.results.length > 0">
        <h4>Примеры детекций:</h4>
        <div v-for="(result, index) in processingResult.results" :key="index" class="detection-preview">
          <p>Кадр {{ result.frame_time }}с: {{ result.gender }}, {{ result.age }}</p>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'ProcessingPage',
  data() {
    return {
      videoStreamUrl: 'http://localhost:8000/video-stream/',
      streamLoaded: false,
      processing: false,
      processingResult: null,
      error: '',
      modelsStatus: null,
      testResult: null
    }
  },
  async mounted() {
    await this.checkModelsStatus()
    this.streamLoaded = true
  },
  methods: {
    handleStreamError() {
      this.error = 'Ошибка загрузки видеопотока'
      this.streamLoaded = false
    },
    async checkModelsStatus() {
      try {
        const response = await axios.get('http://localhost:8000/models-status/')
        this.modelsStatus = response.data
        console.log('Models status:', response.data)
      } catch (error) {
        console.error('Error checking models status:', error)
      }
    },
    async testFrame() {
      try {
        this.testResult = null
        const response = await axios.get('http://localhost:8000/test-frame/')
        this.testResult = response.data
        console.log('Test frame result:', response.data)
      } catch (error) {
        console.error('Test frame error:', error)
        this.error = 'Ошибка теста детекции'
      }
    },
    async processVideo() {
      this.processing = true
      this.processingResult = null
      this.error = ''

      try {
        const response = await axios.get('http://localhost:8000/process-video/')
        this.processingResult = response.data
        console.log('Processing result:', response.data)
      } catch (error) {
        console.error('Processing error:', error)
        this.error = error.response?.data?.detail || 'Ошибка обработки видео'
      } finally {
        this.processing = false
      }
    },
    async checkResults() {
      this.$router.push('/results')
    }
  }
}
</script>

<style scoped>
.processing-page {
  padding: 20px;
  text-align: center;
}

.models-status {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  text-align: left;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.status-item {
  padding: 10px;
  border-radius: 4px;
  background-color: #fff3cd;
  border: 1px solid #ffeaa7;
}

.status-item.loaded {
  background-color: #d4edda;
  border-color: #c3e6cb;
}

.test-section {
  margin: 20px 0;
}

.test-button {
  background-color: #6c757d;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.test-button:hover {
  background-color: #5a6268;
}

.test-result {
  margin-top: 10px;
  padding: 10px;
  background-color: #e9ecef;
  border-radius: 4px;
}

.video-container {
  margin: 20px auto;
  max-width: 800px;
}

.video-stream {
  max-width: 100%;
  border: 2px solid #ddd;
  border-radius: 8px;
}

.loading-stream {
  padding: 50px;
  text-align: center;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 20px auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.controls {
  margin-top: 20px;
}

.process-button, .results-button {
  background-color: #2196F3;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin: 10px;
}

.process-button:hover:not(:disabled), .results-button:hover {
  background-color: #1976D2;
}

.process-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.processing-result {
  background-color: #e8f5e8;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
  text-align: left;
}

.detection-preview {
  background-color: white;
  padding: 10px;
  margin: 5px 0;
  border-radius: 4px;
  border-left: 3px solid #2196F3;
}

.error-message {
  color: #f44336;
  background-color: #ffebee;
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
}
</style>