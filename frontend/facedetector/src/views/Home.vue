<template>
  <div class="home-page">
    <div class="hero">
      <h1>Детекция лиц на видео</h1>
      <p>Загрузите видео, и мы автоматически найдём и проанализируем лица: пол, возраст и время появления.</p>
    </div>

    <div class="upload-section">
      <div
          class="drop-zone"
          :class="{ 'drag-over': dragOver }"
          @dragover.prevent="dragOver = true"
          @dragleave.prevent="dragOver = false"
          @drop.prevent="handleDrop"
      >
        <input
            type="file"
            ref="fileInput"
            @change="handleFileSelect"
            accept="video/*"
            class="file-input"
        />

        <div class="drop-content" @click="triggerFileInput">
          <div v-if="!selectedFile">
            <i class="upload-icon">📁</i>
            <p><strong>Перетащите видео сюда</strong></p>
            <p>или нажмите для выбора файла</p>
            <p class="file-info">
              Поддерживаемые форматы: MP4, AVI, MOV<br />
              Макс. размер: 100 МБ
            </p>
          </div>

          <div v-else>
            <i class="file-icon">🎥</i>
            <p><strong>{{ selectedFile.name }}</strong></p>
            <p class="file-size">{{ formatSize(selectedFile.size) }}</p>
            <button @click.stop="clearFile" class="clear-btn">Удалить</button>
          </div>
        </div>
      </div>

      <!-- Кнопки управления -->
      <div v-if="selectedFile && !uploading" class="actions">
        <button @click="uploadFile" class="upload-btn">
          Загрузить видео
        </button>
      </div>

      <!-- Прогресс загрузки -->
      <div v-if="uploading" class="progress-section">
        <p>Загрузка: {{ uploadProgress }}%</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
      </div>

      <!-- Ошибка -->
      <div v-if="error" class="error-box">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Home',
  data() {
    return {
      selectedFile: null,
      uploading: false,
      uploadProgress: 0,
      error: '',
      dragOver: false
    };
  },
  methods: {
    triggerFileInput() {
      if (!this.uploading) {
        this.$refs.fileInput.click();
      }
    },
    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) this.validateAndSetFile(file);
    },
    handleDrop(event) {
      const file = event.dataTransfer.files[0];
      if (file) this.validateAndSetFile(file);
      this.dragOver = false;
    },
    validateAndSetFile(file) {
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime'];
      const maxSize = 100 * 1024 * 1024; // 100 MB

      if (!validTypes.includes(file.type)) {
        this.error = 'Поддерживаются только видео (MP4, AVI, MOV)';
        return;
      }

      if (file.size > maxSize) {
        this.error = 'Файл слишком большой. Максимум 100 МБ.';
        return;
      }

      this.selectedFile = file;
      this.error = '';
    },
    clearFile() {
      this.selectedFile = null;
      this.$refs.fileInput.value = '';
    },
    formatSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    async uploadFile() {
      if (!this.selectedFile || this.uploading) return;

      this.uploading = true;
      this.uploadProgress = 0;
      this.error = '';

      const formData = new FormData();
      formData.append('file', this.selectedFile);

      try {
        const response = await axios.post('http://localhost:8000/upload-video/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              this.uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            }
          }
        });

        // Сохраняем путь к видео
        const videoPath = response.data.path;

        // Переход на страницу обработки
        this.$router.push({
          name: 'Processing',
          params: { videoPath }
        });
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка загрузки видео';
        this.uploading = false;
      }
    }
  }
};
</script>

<style scoped>
.home-page {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
  text-align: center;
}

.hero h1 {
  font-size: 2.2em;
  color: #333;
  margin-bottom: 10px;
}

.hero p {
  color: #666;
  font-size: 1.1em;
  margin-bottom: 30px;
}

.drop-zone {
  border: 3px dashed #ccc;
  border-radius: 12px;
  padding: 50px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
  margin-bottom: 20px;
}

.drop-zone.drag-over {
  border-color: #4CAF50;
  background-color: #e8f5e8;
  transform: scale(1.02);
}

.drop-content {
  padding: 10px;
}

.upload-icon, .file-icon {
  font-size: 48px;
  margin-bottom: 15px;
  display: block;
}

.file-input {
  display: none;
}

.file-info {
  color: #777;
  font-size: 14px;
  margin-top: 10px;
}

.file-size {
  color: #555;
  font-size: 14px;
  margin: 5px 0 10px;
}

.clear-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 5px;
}

.clear-btn:hover {
  background-color: #da190b;
}

.actions {
  margin: 20px 0;
}

.upload-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 12px 30px;
  font-size: 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.upload-btn:hover:not(:disabled) {
  background-color: #45a049;
}

.upload-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.progress-section {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 18px;
  background-color: #e0e0e0;
  border-radius: 9px;
  overflow: hidden;
  margin: 10px 0;
}

.progress-fill {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

.error-box {
  color: #d32f2f;
  background-color: #ffebee;
  padding: 12px;
  border-radius: 6px;
  margin-top: 15px;
  font-size: 14px;
  text-align: left;
}
</style>