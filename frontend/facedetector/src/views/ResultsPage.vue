<template>
  <div class="results-page">
    <div class="container">
      <div class="header">
        <h1>Результаты анализа видео</h1>
        <p class="subtitle">Обнаружено {{ persons.length }} {{ pluralizePerson(persons.length) }}</p>
      </div>

      <div class="persons-grid">
        <div v-for="(person, index) in persons" :key="person.id" class="person-card">
          <div class="person-gallery">
            <img
                v-for="(img, idx) in person.face_images"
                :key="idx"
                :src="img"
                :alt="`Человек ${index + 1}`"
                class="person-image"
                @click="openGallery(person.id, idx)"
            >
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
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно для просмотра изображений -->
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
      galleryOpen: false,
      currentGalleryImages: [],
      currentGalleryIndex: 0
    };
  },
  computed: {
    currentGalleryImage() {
      return this.currentGalleryImages[this.currentGalleryIndex];
    }
  },
  async created() {
    await this.loadResults();
  },
  methods: {
    async loadResults() {
      try {
        const response = await axios.get('http://localhost:8000/results/');
        this.persons = response.data.persons || [];
      } catch (error) {
        console.error('Error loading results:', error);
      }
    },

    openGallery(personId, startIndex = 0) {
      const person = this.persons.find(p => p.id === personId);
      if (person) {
        this.currentGalleryImages = person.face_images;
        this.currentGalleryIndex = startIndex;
        this.galleryOpen = true;
      }
    },

    pluralizePerson(count) {
      const lastDigit = count % 10;
      const lastTwoDigits = count % 100;

      if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
        return 'человек';
      }

      if (lastDigit === 1) {
        return 'человек';
      }

      if (lastDigit >= 2 && lastDigit <= 4) {
        return 'человека';
      }

      return 'человек';
    },

    pluralizeAppearance(count) {
      const lastDigit = count % 10;
      const lastTwoDigits = count % 100;

      if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
        return 'раз';
      }

      if (lastDigit === 1) {
        return 'раз';
      }

      if (lastDigit >= 2 && lastDigit <= 4) {
        return 'раза';
      }

      return 'раз';
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

      // Обработка возрастных групп в формате (25-32)
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

      // Проверяем, есть ли группа в карте
      if (ageMap.hasOwnProperty(ageGroup)) {
        return ageMap[ageGroup];
      }

      // Если это число (или строка, которую можно преобразовать в число)
      const ageNumber = parseFloat(ageGroup);
      if (!isNaN(ageNumber) && isFinite(ageNumber)) {
        return `${Math.round(ageNumber)} лет`; // Округляем на всякий случай
      }

      // Если ничего не подошло, возвращаем как есть или "Не определен"
      return ageGroup || 'Не определен';
    },
  }
};
</script>

<style scoped>
/* Ваши существующие стили остаются без изменений */
.results-page {
  padding: 2rem;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 2rem;
  text-align: center;
}

.header h1 {
  font-size: 2rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #64748b;
  font-size: 1.1rem;
}

.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.person-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.person-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.person-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8fafc;
}

.person-image {
  width: calc(33.333% - 0.5rem);
  height: 100px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s;
}

.person-image:hover {
  transform: scale(1.05);
}

.person-details {
  padding: 1rem;
}

.person-details h3 {
  margin: 0 0 1rem 0;
  color: #1e293b;
}

.person-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.stat-item {
  background: #f1f5f9;
  padding: 0.5rem;
  border-radius: 6px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  font-weight: 600;
  color: #1e293b;
}

/* Стили для модального окна галереи */
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
}

.gallery-thumbnails img {
  width: 80px;
  height: 60px;
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