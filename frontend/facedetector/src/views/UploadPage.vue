<template>
  <div class="upload-page">
    <h1 class="page-title">Распознавание лиц на видео</h1>
    <p class="page-subtitle">Загрузите видео в формате MP4 (до 1 ГБ)</p>
    
    <!-- 👇 Твой компонент FileDropzone подключен -->
    <FileDropzone @file-selected="handleFileSelected" />
  </div>
</template>

<script>
import FileDropzone from '../components/FileDropzone.vue'

export default {
  name: 'UploadPage',
  components: { FileDropzone },
  methods: {
    handleFileSelected(file) {
      console.log('Файл получен:', file.name)
      // 🚧 Здесь нельзя передавать file в router params напрямую!
      // Вариант на будущее: сохранить файл во Vuex или Pinia
      this.$router.push({ name: 'Processing' })
    }
  }
}
</script>

<style scoped>
.upload-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 40px 20px;
  text-align: center;
}

.page-title {
  font-size: 24px;
  margin-bottom: 12px;
}

.page-subtitle {
  font-size: 14px;
  color: #5a5a5a;
  margin-bottom: 30px;
}
</style>
