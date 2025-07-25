<!-- src/views/UploadPage.vue -->
<template>
  <div class="upload-page">
    <div class="container">
      <h1>Загрузите видео для анализа лиц</h1>
      <p>Поддерживаемые форматы: MP4, AVI, MOV. Макс. размер: 100 МБ.</p>

      <div
          class="drop-zone"
          :class="{ 'drag-over': dragOver }"
          @dragover.prevent="dragOver = true"
          @dragleave.prevent="dragOver = false"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
      >
        <input ref="fileInput" type="file" @change="handleFileSelect" accept="video/*" class="file-input" />
        <div v-if="!selectedFile" class="drop-content">
          <i class="upload-icon">📁</i>
          <p><strong>Перетащите видео сюда</strong></p>
          <p>или нажмите, чтобы выбрать файл</p>
        </div>
        <div v-else class="file-info">
          <i class="file-icon">🎥</i>
          <p><strong>{{ selectedFile.name }}</strong></p>
          <p class="size">{{ formatSize(selectedFile.size) }}</p>
          <button @click.stop="clearFile" class="clear-btn">Удалить</button>
        </div>
      </div>

      <div v-if="uploadProgress > 0" class="progress-section">
        <p>Загрузка: {{ uploadProgress }}%</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
      </div>

      <div v-if="selectedFile && !uploading" class="actions">
        <button @click="uploadFile" class="upload-btn">Загрузить видео</button>
      </div>

      <div v-if="error" class="error-box">{{ error }}</div>
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
    triggerFileInput() { if (!this.uploading) this.$refs.fileInput.click(); },
    handleFileSelect(e) { const file = e.target.files[0]; if (file) this.validateAndSetFile(file); },
    handleDrop(e) { const file = e.dataTransfer.files[0]; if (file) this.validateAndSetFile(file); this.dragOver = false; },
    validateAndSetFile(file) {
      const validTypes = ['video/mp4', 'video/avi', 'video/mov'];
      const maxSize = 100 * 1024 * 1024;
      if (!validTypes.includes(file.type)) { this.error = 'Только MP4, AVI, MOV'; return; }
      if (file.size > maxSize) { this.error = 'Файл > 100 МБ'; return; }
      this.selectedFile = file;
      this.error = '';
    },
    formatSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    clearFile() {
      this.selectedFile = null;
      this.uploadProgress = 0;
      this.error = '';
      this.$refs.fileInput.value = '';
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
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => { this.uploadProgress = Math.round((e.loaded * 100) / e.total); }
        });
        this.$router.push({ name: 'Processing', params: { videoPath: response.data.path } });
      } catch (err) {
        this.error = err.response?.data?.detail || 'Ошибка загрузки';
      } finally {
        this.uploading = false;
      }
    }
  }
};
</script>