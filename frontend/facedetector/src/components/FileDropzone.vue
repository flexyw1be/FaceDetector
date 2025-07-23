<template>
  <div class="dropzone" @dragover.prevent @drop.prevent="handleDrop">
    <input
      type="file"
      accept="video/mp4"
      @change="handleFileChange"
      style="display: none"
      ref="fileInput"
    />
    <p class="file-hint">mp4 (до 1 ГБ)</p>
    <button @click="openFileDialog" :disabled="uploading" class="select-button">📂 Выберите файл</button>
    <p class="or-text">или перетащите сюда</p>
    <UploadProgress v-if="uploading" :progress="progress" />
  </div>
</template>

<script>
import axios from 'axios'
import UploadProgress from './UploadProgress.vue'

export default {
  name: 'FileDropzone',
  components: { UploadProgress },
  data() {
    return {
      uploading: false,
      progress: 0
    }
  },
  methods: {
    openFileDialog() {
      this.$refs.fileInput.click()
    },
    async handleFileChange(event) {
      const file = event.target.files[0]
      if (!file || file.type !== 'video/mp4') {
        this.$toast?.error('Пожалуйста, выберите видео в формате MP4.')
        return
      }

      this.uploading = true
      const formData = new FormData()
      formData.append('video', file)

      try {
        await axios.post('/api/upload', formData, {
          onUploadProgress: (e) => {
            this.progress = Math.round((e.loaded * 100) / e.total)
          }
        })
        this.$emit('file-selected', file)
      } catch (err) {
        this.$router.push({ name: 'Error' })
      } finally {
        this.uploading = false
      }
    },
    handleDrop(event) {
      const file = event.dataTransfer.files[0]
      if (file && file.type === 'video/mp4') {
        this.$refs.fileInput.files = event.dataTransfer.files
        this.handleFileChange(event)
      }
    }
  }
}
</script>

<style scoped>
.dropzone {
  border: 2px dashed #c3c9f7;
  background-color: #4664e9;
  color: white;
  border-radius: 16px;
  padding: 60px 20px;
  max-width: 700px;
  margin: 0 auto;
  transition: background-color 0.3s ease;
}

.dropzone:hover {
  background-color: #3c59d1;
}

.file-hint {
  font-size: 14px;
  margin-bottom: 8px;
}

.select-button {
  background-color: white;
  color: #000;
  border: none;
  padding: 10px 16px;
  font-weight: 500;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.select-button:hover {
  background-color: #f0f0f0;
}

.or-text {
  font-size: 14px;
  color: #e3e6fb;
}
</style>
