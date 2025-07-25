<template>
  <div class="video-container">
    <video
      ref="video"
      :src="videoUrl"
      controls
      width="640"
      height="360"
      @loadeddata="onLoaded"
      @error="onError"
    ></video>
    <p v-if="error" style="color: red">{{ error }}</p>
  </div>
</template>

<script>
export default {
  name: 'VideoPlayer',
  props: {
    videoPath: String // Например: "/uploads/abc123.mp4"
  },
  data() {
    return {
      error: null
    }
  },
  computed: {
    videoUrl() {
      if (!this.videoPath) return ''
      return `http://localhost:8000${this.videoPath}`
    }
  },
  methods: {
    onLoaded() {
      this.error = null
    },
    onError() {
      this.error = 'Ошибка загрузки видеопотока. Проверьте формат файла.'
    }
  }
}
</script>

<style scoped>
.video-player {
  position: relative;
}

.face-details {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 5px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}
</style>