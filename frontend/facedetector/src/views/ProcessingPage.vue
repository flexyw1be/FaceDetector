<template>
  <div class="processing-page">
    <div class="container">
      <h1>Face Detector</h1>

      <div class="file-info">
        <div class="file-format">mp4</div>
        <div class="file-name">{{ fileName }}</div>
        <div class="file-size">{{ fileSize }}</div>
      </div>

      <!-- Отображение сообщения от сервера -->
      <div class="message-section" v-if="serverMessage">
        <p>{{ serverMessage }}</p>
      </div>

      <div class="processing-section">
        <div class="spinner"></div>
        <p class="processing-text">Обработка...</p>
      </div>

      <div class="progress-section" v-if="progress > 0 || progress === 0">
        <div class="progress-bar">
          <div class="progress" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-text">{{ progress }}%</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProcessingPage',
  data() {
    return {
      fileName: 'Загруженное видео',
      fileSize: 'Размер файла',
      progress: 0,
      serverMessage: '',
      statusInterval: null
    }
  },
  async mounted() {
    // Получаем данные о файле из параметров маршрута
    if (this.$route.query.fileName) {
      this.fileName = this.$route.query.fileName;
    }
    if (this.$route.query.fileSize) {
      this.fileSize = this.formatFileSize(this.$route.query.fileSize);
    }

    await this.startProcessing();
    this.pollProcessingStatus();
  },
  methods: {
    // Метод для форматирования размера файла
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    async startProcessing() {
      try {
        // Предполагаем, что video_id уже известен или был загружен ранее
        // Если нужно, можно передавать его в теле запроса
        const response = await fetch('http://localhost:8000/process-video/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
          // body: JSON.stringify({ video_id: this.videoId }) // если требуется
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Ошибка запуска обработки');
        }

        const data = await response.json();
        console.log("Обработка начата:", data.message);
        this.serverMessage = data.message;

      } catch (error) {
        console.error('Ошибка при запуске обработки:', error);
        this.serverMessage = `Ошибка: ${error.message}`;
        // Опционально: остановить опрос или показать ошибку пользователю
      }
    },

    pollProcessingStatus() {
      this.statusInterval = setInterval(async () => {
        try {
          const res = await fetch('http://localhost:8000/process-video/status');

          if (!res.ok) {
              // Обработка ошибок статуса (например, 500)
              const errorText = await res.text();
              console.error("Ошибка получения статуса:", res.status, errorText);
              this.serverMessage = `Ошибка получения статуса: ${res.status}`;
              return;
          }

          const data = await res.json();

          this.progress = data.progress;
          this.serverMessage = data.message;

          // Проверяем, завершена ли обработка
          if (!data.is_processing && data.progress >= 100) {
            clearInterval(this.statusInterval);
            this.serverMessage = "Обработка завершена! Переход к результатам...";
            // Небольшая задержка перед переходом
            setTimeout(() => {
              // Передаем video_id в результаты, если необходимо
              this.$router.push({ name: 'Results', query: { video_id: data.video_id } });
            }, 1500);
          } else if (!data.is_processing && data.progress < 100) {
             // Обработка остановлена или произошла ошибка
             clearInterval(this.statusInterval);
             this.serverMessage = data.message || "Обработка остановлена или произошла ошибка.";
          }


        } catch (error) {
          console.error("Ошибка получения статуса обработки:", error);
           this.serverMessage = `Ошибка соединения: ${error.message}`;
          // Опционально: остановить опрос при сетевой ошибке
          // clearInterval(this.statusInterval);
        }
      }, 1000); // Опрашиваем каждую секунду
    }
  }
}
</script>

<style scoped>
.processing-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8fafc;
  padding: 20px;
}

.container {
  width: 100%;
  max-width: 500px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 40px;
  text-align: center;
}

h1 {
  font-size: 24px;
  color: #2d3748;
  margin-bottom: 30px;
  font-weight: 600;
}

.file-info {
  margin-bottom: 30px;
}

.file-format {
  font-size: 14px;
  color: #718096;
  margin-bottom: 4px;
}

.file-name {
  font-size: 16px;
  color: #2d3748;
  font-weight: 500;
  margin-bottom: 4px;
}

.file-size {
  font-size: 14px;
  color: #718096;
}

.processing-section {
  margin: 30px 0;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(79, 70, 229, 0.1);
  border-radius: 50%;
  border-top-color: #4f46e5;
  margin: 0 auto 15px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.processing-text {
  font-size: 16px;
  color: #4f46e5;
  margin: 0;
}

.progress-section {
  margin-top: 30px;
}

.progress-bar {
  height: 6px;
  background-color: #e2e8f0;
  border-radius: 3px;
  margin-bottom: 8px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background-color: #4f46e5;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #64748b;
}
</style>