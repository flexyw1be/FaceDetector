<template>
  <div class="upload-page">
    <h1>Загрузка видео</h1>
    <div class="upload-container">
      <div
        class="drop-zone"
        @drop.prevent="handleDrop"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        :class="{ 'drag-over': dragOver }"
      >
        <input
          type="file"
          @change="handleFileUpload"
          accept="video/*"
          ref="fileInput"
          class="file-input"
        />
        <div class="drop-zone-content" @click="triggerFileInput">
          <div v-if="!selectedFile">
            <i class="upload-icon">📁</i>
            <p>Перетащите видео сюда или нажмите для выбора</p>
            <p class="file-types">Поддерживаемые форматы: MP4, AVI, MOV, MKV</p>
          </div>
          <div v-else>
            <i class="file-icon">🎥</i>
            <p><strong>{{ selectedFile.name }}</strong></p>
            <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
          </div>
        </div>
      </div>

      <div v-if="uploadProgress > 0" class="progress-container">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: uploadProgress + '%' }"
          ></div>
        </div>
        <p class="progress-text">{{ uploadProgress }}% загружено</p>
      </div>

      <div v-if="selectedFile" class="upload-controls">
        <button
          @click="uploadFile"
          :disabled="uploading || uploadProgress > 0"
          class="upload-button"
        >
          {{ uploading ? 'Загрузка...' : 'Загрузить видео' }}
        </button>
        <button @click="clearFile" class="clear-button">
          Очистить
        </button>
      </div>

      <div v-if="uploadError" class="error-message">
        {{ uploadError }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UploadPage',
  data() {
    return {
      selectedFile: null,
      uploading: false,
      uploadProgress: 0,
      uploadError: '',
      dragOver: false
    }
  },
  methods: {
    triggerFileInput() {
      if (!this.uploading) {
        this.$refs.fileInput.click()
      }
    },
    handleFileUpload(event) {
      const file = event.target.files[0]
      if (file) {
        this.validateAndSetFile(file)
      }
      this.dragOver = false
    },
    handleDrop(event) {
      const file = event.dataTransfer.files[0]
      if (file) {
        this.validateAndSetFile(file)
      }
      this.dragOver = false
    },
    validateAndSetFile(file) {
      // Проверяем тип файла
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime', 'video/x-matroska']
      const maxSize = 100 * 1024 * 1024; // 100MB

      if (!file.type.startsWith('video/')) {
        this.uploadError = 'Пожалуйста, выберите видео файл'
        return
      }

      if (file.size > maxSize) {
        this.uploadError = 'Файл слишком большой. Максимальный размер: 100MB'
        return
      }

      this.selectedFile = file
      this.uploadError = ''
    },
    async uploadFile() {
      if (!this.selectedFile) return

      this.uploading = true
      this.uploadProgress = 0
      this.uploadError = ''

      const formData = new FormData()
      formData.append('file', this.selectedFile)

      try {
        const response = await axios.post('http://localhost:8000/upload-video/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              this.uploadProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            }
          }
        })

        console.log('Upload response:', response.data)

        // Переход к странице обработки
        this.$router.push({
          name: 'Processing',
          params: { filename: response.data.filename }
        })
      } catch (error) {
        console.error('Upload error:', error)
        this.uploadError = error.response?.data?.detail || 'Ошибка загрузки файла'
      } finally {
        this.uploading = false
      }
    },
    clearFile() {
      this.selectedFile = null
      this.uploadProgress = 0
      this.uploadError = ''
      this.$refs.fileInput.value = ''
    },
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
  }
}
</script>

<style scoped>
.upload-page {
  padding: 20px;
  text-align: center;
  max-width: 800px;
  margin: 0 auto;
}

.drop-zone {
  border: 2px dashed #ccc;
  border-radius: 10px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #fafafa;
  margin-bottom: 20px;
}

.drop-zone.drag-over {
  border-color: #4CAF50;
  background-color: #e8f5e8;
}

.drop-zone-content {
  padding: 20px;
}

.upload-icon, .file-icon {
  font-size: 48px;
  margin-bottom: 15px;
  display: block;
}

.file-input {
  display: none;
}

.file-types {
  color: #666;
  font-size: 14px;
  margin-top: 10px;
}

.file-size {
  color: #666;
  font-size: 14px;
}

.progress-container {
  margin: 20px 0;
}

.progress-bar {
  width: 100%;
  height: 20px;
  background-color: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background-color: #4CAF50;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  color: #666;
}

.upload-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.upload-button, .clear-button {
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin: 5px;
}

.upload-button {
  background-color: #4CAF50;
  color: white;
}

.upload-button:hover:not(:disabled) {
  background-color: #45a049;
}

.upload-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.clear-button {
  background-color: #f44336;
  color: white;
}

.clear-button:hover {
  background-color: #da190b;
}

.error-message {
  color: #f44336;
  background-color: #ffebee;
  padding: 10px;
  border-radius: 4px;
  margin-top: 15px;
}
</style>