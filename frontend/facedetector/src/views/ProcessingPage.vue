<template>
  <div class="processing-page">
    <h2>Обработка видео...</h2>
    <p>Пожалуйста, подождите</p>
  </div>
</template>


<script>
export default {
  data() {
    return {
      videoPath: '',
      processing: false,
      streaming: false
    }
  },
  computed: {
    streamUrl() {
      return 'http://localhost:8000/process-video/';
    }
  },
  mounted() {
    this.videoPath = this.$route.params.videoPath;
  },
  methods: {
    startProcessing() {
      this.processing = true;
      this.streaming = true;
      // Обработка уже идет в /process-video/
      setTimeout(() => {
        this.$router.push({ name: 'Results' });
      }, 5000); // Имитация длительной обработки
    }
  }
}
</script>

<style scoped>
.video-container {
  margin: 20px auto;
  max-width: 640px;
}

.video-stream {
  max-width: 100%;
  border: 2px solid #ddd;
  border-radius: 8px;
}

.controls {
  margin: 20px 0;
}

.process-button {
  background-color: #2196F3;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

.process-button:hover:not(:disabled) {
  background-color: #1976D2;
}

.process-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>