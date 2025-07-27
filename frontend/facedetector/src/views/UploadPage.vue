<template>
  <div class="upload-page">
    <div class="container">
      <div class="header">
        <h1>Распознавание лиц на видео</h1>
        <p class="subtitle">Загрузите видео для анализа лиц, пола, возраста и времени появления</p>
      </div>

      <div
          class="drop-zone"
          :class="{ 'drag-over': dragOver, 'has-file': selectedFile }"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
      >
        <input
            ref="fileInput"
            type="file"
            @change="handleFileSelect"
            accept="video/*"
            class="file-input"
        />

        <transition name="fade" mode="out-in">
          <div v-if="!selectedFile" class="drop-content">
            <div class="upload-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15V19C21 20.1046 20.1046 21 19 21H5C3.89543 21 3 20.1046 3 19V15" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M17 8L12 3L7 8" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M12 3V15" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <p class="file-format">Поддерживаемые форматы: MP4, AVI, MOV (до 1 ГБ)</p>
            <button class="choose-file-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M19 10H5C3.89543 10 3 10.8954 3 12V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V12C21 10.8954 20.1046 10 19 10Z" stroke="#4F46E5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Выберите файл
            </button>
            <p class="hint">или перетащите видео сюда</p>
          </div>

          <div v-else class="file-info">
            <div class="file-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M14 2V8H20" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 13H8" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 17H8" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M10 9H9H8" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div class="file-details">
              <h3>{{ selectedFile.name }}</h3>
              <p class="size">{{ formatSize(selectedFile.size) }}</p>
            </div>
            <button @click.stop="clearFile" class="clear-btn">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18M6 6L18 18" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </transition>
      </div>

      <!-- Прогресс загрузки -->
      <div v-if="uploadProgress > 0" class="progress-section">
        <div class="progress-header">
          <span>Загрузка...</span>
          <span>{{ uploadProgress }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
      </div>

      <!-- Кнопка "Анализировать видео" -->
      <button
          v-if="selectedFile && !uploading"
          @click="uploadFile"
          class="upload-btn"
          :disabled="uploading"
      >
        <span v-if="!uploading">Анализировать видео</span>
        <span v-else class="loading-text">Обработка...</span>
      </button>

      <!-- Ошибка -->
      <div v-if="error" class="error-box">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 9V11M12 15H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'UploadPage',
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
    handleDragOver(event) {
      event.preventDefault();
      this.dragOver = true;
    },
    handleDragLeave(event) {
      event.preventDefault();
      this.dragOver = false;
    },
    handleDrop(event) {
      event.preventDefault();
      const file = event.dataTransfer.files[0];
      if (file) this.validateAndSetFile(file);
      this.dragOver = false;
    },
    validateAndSetFile(file) {
      const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/quicktime'];
      const maxSize = 1 * 1024 * 1024 * 1024; // 1 GB

      if (!validTypes.includes(file.type)) {
        this.error = 'Поддерживаются только видео (MP4, AVI, MOV)';
        return;
      }

      if (file.size > maxSize) {
        this.error = 'Файл слишком большой. Максимум 1 ГБ.';
        return;
      }

      this.selectedFile = file;
      this.error = '';
    },
    clearFile() {
      this.selectedFile = null;
      this.uploadProgress = 0;
      this.error = '';
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

        const videoPath = response.data.path;
        this.$router.push(`/process-video/${encodeURIComponent(videoPath)}`);
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка загрузки видео';
      } finally {
        this.uploading = false;
      }
    }
  }
};
</script>

<style scoped>
.upload-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f8ff 0%, #e6f0ff 100%);
  padding: 2rem;
}

.container {
  max-width: 800px;
  width: 100%;
  background-color: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  padding: 2.5rem;
  text-align: center;
  transition: all 0.3s ease;
}

.header {
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2.2rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.header .subtitle {
  color: #64748b;
  font-size: 1.1rem;
  line-height: 1.6;
  max-width: 80%;
  margin: 0 auto;
}

.drop-zone {
  border: 2px dashed #4F46E5;
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: rgba(79, 70, 229, 0.05);
  margin-bottom: 1.5rem;
  position: relative;
  overflow: hidden;
}

.drop-zone:before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(79, 70, 229, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.drop-zone.drag-over {
  background-color: rgba(79, 70, 229, 0.1);
  border-color: #4F46E5;
}

.drop-zone.drag-over:before {
  opacity: 1;
}

.drop-zone.has-file {
  background-color: #4F46E5;
  border-color: #4F46E5;
}

.file-input {
  display: none;
}

.drop-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon {
  margin-bottom: 1rem;
}

.upload-icon svg {
  stroke-width: 1.5;
}

.file-format {
  font-size: 0.9rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.choose-file-btn {
  background-color: #4F46E5;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(79, 70, 229, 0.1);
}

.choose-file-btn:hover {
  background-color: #4338ca;
  transform: translateY(-1px);
  box-shadow: 0 6px 8px rgba(79, 70, 229, 0.15);
}

.choose-file-btn:active {
  transform: translateY(0);
}

.choose-file-btn svg {
  stroke-width: 2;
}

.hint {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  width: 100%;
  padding: 1rem;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.file-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.75rem;
}

.file-details {
  flex-grow: 1;
  text-align: left;
  overflow: hidden;
}

.file-details h3 {
  font-size: 1rem;
  font-weight: 600;
  color: white;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.size {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 0.25rem;
}

.clear-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.3s ease;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.clear-btn svg {
  stroke-width: 2;
}

.progress-section {
  width: 100%;
  margin-bottom: 1.5rem;
  animation: fadeIn 0.3s ease;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: #64748b;
}

.progress-bar {
  height: 8px;
  background-color: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2);
  position: relative;
  overflow: hidden;
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(79, 70, 229, 0.3);
}

.upload-btn:active {
  transform: translateY(0);
}

.upload-btn:disabled {
  background: linear-gradient(135deg, #a5b4fc 0%, #c4b5fd 100%);
  cursor: not-allowed;
}

.upload-btn:disabled:hover {
  transform: none;
  box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2);
}

.loading-text {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.error-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background-color: #fee2e2;
  color: #dc2626;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  margin-top: 1.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  animation: fadeIn 0.3s ease;
}

.error-box svg {
  flex-shrink: 0;
}

/* Animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .container {
    padding: 1.5rem;
  }

  .header h1 {
    font-size: 1.8rem;
  }

  .header .subtitle {
    max-width: 100%;
  }

  .drop-zone {
    padding: 2rem 1rem;
  }

  .file-info {
    gap: 1rem;
    padding: 0.75rem;
  }
}
</style>