<template>
  <div class="results-page">
    <div class="container">
      <div class="header">
        <h1>Результаты анализа видео</h1>
        <p class="subtitle">Обнаружено {{ persons.length }} {{ pluralizePerson(persons.length) }}</p>
      </div>

      <div v-if="error" class="error-message">
        Ошибка загрузки данных: {{ error }}
      </div>

      <div v-if="loading" class="loading-message">
        Загрузка данных...
      </div>

      <!-- Видео плеер с детекцией -->
      <div class="video-player-container">
        <video
            ref="videoPlayer"
            :src="videoUrl"
            controls
            @play="startFaceDetection"
            @pause="stopFaceDetection"
            @seeked="handleSeek"
            class="video-player"
        ></video>
        <canvas ref="detectionCanvas" class="detection-canvas"></canvas>

        <div class="video-controls">
          <button @click="toggleDetection" class="control-btn">
            {{ showDetection ? 'Скрыть детекцию' : 'Показать детекцию' }}
          </button>
          <button @click="togglePlayback" class="control-btn">
            {{ isPlaying ? 'Пауза' : 'Воспроизвести' }}
          </button>
        </div>
      </div>

      <!-- Список обнаруженных лиц -->
      <div class="persons-grid">
        <div v-for="(person, index) in persons" :key="person.id || index" class="person-card">
          <div class="person-gallery">
            <div class="main-image-container">
              <img
                  :src="getFirstImage(person)"
                  :alt="`Человек ${index + 1}`"
                  class="person-main-image"
                  @click="openGallery(person.id || index, 0)"
                  @mouseenter="highlightPerson(person.id)"
                  @mouseleave="unhighlightPerson()"
              >
            </div>

            <div v-if="person.face_images && person.face_images.length > 1" class="additional-images">
              <button class="toggle-btn" @click="toggleGallery(person.id || index)">
                <span>
                  {{ isExpanded(person.id || index) ? 'Скрыть фото' : `Показать все фото (${person.face_images.length})` }}
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"
                       :style="{ transform: isExpanded(person.id || index) ? 'rotate(180deg)' : 'none' }">
                    <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
              </button>

              <div v-show="isExpanded(person.id || index)" class="thumbnails-container">
                <img
                    v-for="(img, idx) in person.face_images.slice(1)"
                    :key="idx"
                    :src="img"
                    :alt="`Человек ${index + 1} фото ${idx + 2}`"
                    class="person-thumbnail"
                    @click="openGallery(person.id || index, idx + 1)"
                    @mouseenter="highlightPerson(person.id)"
                    @mouseleave="unhighlightPerson()"
                >
              </div>
            </div>
          </div>

          <div class="person-details">
            <h3>Человек {{ index + 1 }}</h3>
            <div class="person-stats">
              <div class="stat-item">
                <span class="stat-label">Пол</span>
                <span class="stat-value">{{ formatGender(person.gender) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Возраст</span>
                <span class="stat-value">{{ formatAge(person.age_group) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Появления</span>
                <span class="stat-value">{{ person.appearance_count }} {{ pluralizeAppearance(person.appearance_count) }}</span>
              </div>
            </div>
            <button
                @click="jumpToPerson(person.id)"
                class="jump-btn"
            >
              Показать в видео
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Галерея изображений -->
    <div v-if="galleryOpen" class="image-gallery-modal">
      <button class="close-btn" @click="galleryOpen = false">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <div class="gallery-content">
        <img :src="currentGalleryImage" class="gallery-main-image">
        <div class="gallery-thumbnails">
          <img
              v-for="(img, idx) in currentGalleryImages"
              :key="idx"
              :src="img"
              @click="currentGalleryIndex = idx"
              :class="{active: currentGalleryIndex === idx}"
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ResultsPage',
  data() {
    return {
      persons: [],
      detections: [], // Все обнаружения лиц
      videoUrl: '',
      currentVideoId: '',

      // Видео и детекция
      showDetection: true,
      isPlaying: false,
      detectionInterval: null,
      currentTime: 0,
      highlightedPerson: null,

      // Галерея
      galleryOpen: false,
      currentGalleryImages: [],
      currentGalleryIndex: 0,
      expandedPersons: new Set(),

      // Состояние
      loading: false,
      error: null
    };
  },
  computed: {
    currentGalleryImage() {
      return this.currentGalleryImages[this.currentGalleryIndex] || '';
    },

    // Фильтруем обнаружения для текущего времени
    currentDetections() {
      if (!this.detections.length) return [];

      const video = this.$refs.videoPlayer;
      if (!video) return [];

      // Ищем обнаружения в пределах ±0.5 секунды от текущего времени
      const time = video.currentTime;
      return this.detections.filter(d =>
          Math.abs(this.getTimeInSeconds(d.frame_time) - time) <= 0.5
      );
    },

    // Группируем обнаружения по person_id
    groupedDetections() {
      const groups = {};
      this.currentDetections.forEach(detection => {
        if (!groups[detection.person_id]) {
          groups[detection.person_id] = [];
        }
        groups[detection.person_id].push(detection);
      });
      return groups;
    }
  },
  async created() {
    await this.loadResults();
  },
  beforeDestroy() {
    this.stopFaceDetection();
  },
  methods: {
    async loadResults() {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('http://localhost:8000/results/');
        this.persons = response.data.persons.map((person, index) => ({
          ...person,
          id: person.id || `person-${index}`,
          face_images: person.face_images || []
        }));

        // Загружаем все обнаружения
        const detectionsResponse = await axios.get('http://localhost:8000/detections/');
        this.detections = detectionsResponse.data.detections;

        // Получаем URL видео
        this.currentVideoId = response.data.video_id;
        this.videoUrl = `http://localhost:8000/uploads/${this.currentVideoId}.mp4`;
      } catch (error) {
        console.error('Error loading results:', error);
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    // Преобразуем время в секунды
    getTimeInSeconds(timeStr) {
      const time = new Date(timeStr);
      return time.getHours() * 3600 + time.getMinutes() * 60 + time.getSeconds() + time.getMilliseconds() / 1000;
    },

    // Воспроизведение/пауза
    togglePlayback() {
      const video = this.$refs.videoPlayer;
      if (!video) return;

      if (video.paused) {
        video.play();
        this.isPlaying = true;
      } else {
        video.pause();
        this.isPlaying = false;
      }
    },

    // Переключение отображения детекции
    toggleDetection() {
      this.showDetection = !this.showDetection;
      if (this.showDetection && this.isPlaying) {
        this.drawDetections();
      } else {
        this.clearCanvas();
      }
    },

    // Начать детекцию при воспроизведении
    startFaceDetection() {
      this.isPlaying = true;
      if (this.showDetection) {
        this.detectionInterval = setInterval(this.drawDetections, 100);
      }
    },

    // Остановить детекцию при паузе
    stopFaceDetection() {
      this.isPlaying = false;
      if (this.detectionInterval) {
        clearInterval(this.detectionInterval);
        this.detectionInterval = null;
      }
      this.clearCanvas();
    },

    // Обработка перемотки
    handleSeek() {
      if (!this.isPlaying && this.showDetection) {
        this.drawDetections();
      }
    },

    // Отрисовка обнаруженных лиц
    drawDetections() {
      const video = this.$refs.videoPlayer;
      const canvas = this.$refs.detectionCanvas;

      if (!video || !canvas || !this.showDetection) return;

      // Синхронизируем размеры canvas с видео
      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }

      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Отрисовываем все обнаружения для текущего времени
      this.currentDetections.forEach(detection => {
        const box = JSON.parse(detection.bounding_box);
        if (!box || box.length !== 4) return;

        // Координаты могут быть в нормализованном формате
        const isNormalized = box.some(coord => coord < 1 && coord > 0);

        let x1, y1, x2, y2;
        if (isNormalized) {
          // Преобразуем нормализованные координаты в абсолютные
          x1 = box[0] * video.videoWidth;
          y1 = box[1] * video.videoHeight;
          x2 = box[2] * video.videoWidth;
          y2 = box[3] * video.videoHeight;
        } else {
          // Абсолютные координаты
          [x1, y1, x2, y2] = box;
        }

        // Определяем цвет рамки
        let color = '#3b82f6'; // Синий по умолчанию
        let lineWidth = 2;

        // Если это выделенный человек
        if (this.highlightedPerson === detection.person_id) {
          color = '#ef4444'; // Красный для выделенного
          lineWidth = 4;
        }

        // Рисуем рамку
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

        // Подпись с информацией
        const label = `${this.formatGender(detection.gender)}, ${this.formatAge(detection.age_group)}`;
        const labelWidth = ctx.measureText(label).width;

        // Фон для подписи
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.fillRect(x1, y1 - 20, labelWidth + 10, 20);

        // Текст подписи
        ctx.fillStyle = 'white';
        ctx.font = '12px Arial';
        ctx.fillText(label, x1 + 5, y1 - 5);
      });
    },

    // Очистка canvas
    clearCanvas() {
      const canvas = this.$refs.detectionCanvas;
      if (!canvas) return;

      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    },

    // Подсветка человека при наведении
    highlightPerson(personId) {
      this.highlightedPerson = personId;
      if (this.showDetection) {
        this.drawDetections();
      }
    },

    // Снятие подсветки
    unhighlightPerson() {
      this.highlightedPerson = null;
      if (this.showDetection) {
        this.drawDetections();
      }
    },

    // Переход к моменту появления человека в видео
    jumpToPerson(personId) {
      const video = this.$refs.videoPlayer;
      if (!video) return;

      // Находим первое обнаружение этого человека
      const firstDetection = this.detections.find(d => d.person_id === personId);
      if (!firstDetection) return;

      // Перематываем видео
      const time = this.getTimeInSeconds(firstDetection.frame_time);
      video.currentTime = time;

      // Подсвечиваем этого человека
      this.highlightPerson(personId);

      // Если видео на паузе, обновляем детекцию
      if (video.paused) {
        this.drawDetections();
      }
    },

    // Остальные методы остаются без изменений
    getFirstImage(person) {
      return person.face_images?.[0] || '';
    },
    isExpanded(personId) {
      return this.expandedPersons.has(personId);
    },
    toggleGallery(personId) {
      if (this.expandedPersons.has(personId)) {
        this.expandedPersons.delete(personId);
      } else {
        this.expandedPersons.add(personId);
      }
    },
    openGallery(personId, startIndex = 0) {
      const person = this.persons.find(p => p.id === personId);
      if (person?.face_images?.length) {
        this.currentGalleryImages = person.face_images;
        this.currentGalleryIndex = Math.min(startIndex, person.face_images.length - 1);
        this.galleryOpen = true;
      }
    },
    pluralizePerson(count) {
      if (count % 100 >= 11 && count % 100 <= 19) return 'человек';
      switch(count % 10) {
        case 1: return 'человек';
        case 2:
        case 3:
        case 4: return 'человека';
        default: return 'человек';
      }
    },
    pluralizeAppearance(count) {
      if (count % 100 >= 11 && count % 100 <= 19) return 'раз';
      switch(count % 10) {
        case 1: return 'раз';
        case 2:
        case 3:
        case 4: return 'раза';
        default: return 'раз';
      }
    },
    formatGender(gender) {
      if (!gender) return 'Не определен';
      const genderMap = {
        'Male': 'Мужской',
        'Female': 'Женский',
        'Man': 'Мужской',
        'Woman': 'Женский',
        'male': 'Мужской',
        'female': 'Женский'
      };
      return genderMap[gender] || gender;
    },
    formatAge(ageGroup) {
      if (!ageGroup) return 'Не определен';
      if (!isNaN(ageGroup)) return `${ageGroup} лет`;

      const ageMap = {
        '(0-2)': '0-2 года',
        '(4-6)': '4-6 лет',
        '(8-12)': '8-12 лет',
        '(15-20)': '15-20 лет',
        '(25-32)': '25-32 года',
        '(38-43)': '38-43 года',
        '(48-53)': '48-53 года',
        '(60-100)': '60+ лет'
      };
      return ageMap[ageGroup] || ageGroup;
    }
  }
};
</script>

<style scoped>
.results-page {
  padding: 1.5rem;
  min-height: 100vh;
  background-color: #f8fafc;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 1.5rem;
  text-align: center;
}

.header h1 {
  font-size: 1.8rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
  font-size: 1rem;
}

.error-message {
  color: #ef4444;
  background: #fee2e2;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
}

.loading-message {
  color: #3b82f6;
  text-align: center;
  padding: 2rem;
}

/* Видео плеер */
.video-player-container {
  position: relative;
  margin: 0 auto 1.5rem;
  max-width: 700px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.video-player {
  width: 100%;
  display: block;
  background: #000;
}

.detection-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.video-controls {
  display: flex;
  justify-content: center;
  gap: 1rem;
  padding: 0.8rem;
  background: #f1f5f9;
}

.control-btn {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.9rem;
}

.control-btn:hover {
  background: #2563eb;
}

/* Карточки людей */
.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.2rem;
}

.person-card {
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.person-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.person-gallery {
  padding: 0.8rem;
  background: #f8fafc;
}

.main-image-container {
  margin-bottom: 0.8rem;
}

.person-main-image {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s;
}

.person-main-image:hover {
  transform: scale(1.02);
}

.additional-images {
  border-top: 1px solid #e2e8f0;
  padding-top: 0.8rem;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: none;
  border: none;
  color: #3b82f6;
  font-weight: 500;
  cursor: pointer;
  padding: 0.4rem;
  margin: 0 auto;
  transition: color 0.2s;
  font-size: 0.85rem;
}

.toggle-btn:hover {
  color: #2563eb;
}

.toggle-btn svg {
  transition: transform 0.3s ease;
}

.thumbnails-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(70px, 1fr));
  gap: 6px;
  margin-top: 0.8rem;
  max-height: 220px;
  overflow-y: auto;
  padding: 4px;
}

.person-thumbnail {
  width: 100%;
  height: 70px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s;
}

.person-thumbnail:hover {
  transform: scale(1.05);
}

.person-details {
  padding: 0.8rem;
}

.person-details h3 {
  margin: 0 0 0.8rem 0;
  color: #1e293b;
  font-size: 1.1rem;
}

.person-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.4rem;
  margin-bottom: 0.8rem;
}

.stat-item {
  background: #f1f5f9;
  padding: 0.5rem;
  border-radius: 6px;
  text-align: center;
  font-size: 0.85rem;
}

.stat-label {
  display: block;
  color: #64748b;
  margin-bottom: 0.2rem;
  font-size: 0.75rem;
}

.stat-value {
  display: block;
  font-weight: 600;
  color: #1e293b;
}

.jump-btn {
  width: 100%;
  padding: 0.5rem;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.9rem;
}

.jump-btn:hover {
  background: #059669;
}

/* Галерея изображений */
.image-gallery-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.gallery-content {
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gallery-main-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  margin-bottom: 1rem;
}

.gallery-thumbnails {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding: 0.5rem;
  max-width: 100%;
}

.gallery-thumbnails img {
  width: 70px;
  height: 50px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.gallery-thumbnails img:hover {
  opacity: 1;
}

.gallery-thumbnails img.active {
  opacity: 1;
  border: 2px solid white;
}
</style>