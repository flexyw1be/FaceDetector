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

      <div class="persons-grid">
        <div v-for="(person, index) in persons" :key="person.id || index" class="person-card">
          <div class="person-gallery">
            <div class="main-image-container">
              <img
                  :src="getFirstImage(person)"
                  :alt="`Человек ${index + 1}`"
                  class="person-main-image"
                  @click="openGallery(person.id || index, 0)"
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
          </div>
        </div>
      </div>
    </div>

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
      currentGalleryIndex: 0,
      expandedPersons: new Set(),
      loading: false,
      error: null
    };
  },
  computed: {
    currentGalleryImage() {
      return this.currentGalleryImages[this.currentGalleryIndex] || '';
    }
  },
  async created() {
    await this.loadResults();
  },
  methods: {
    async loadResults() {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.get('http://localhost:8000/results/');
        this.persons = response.data.persons.map((person, index) => ({
          ...person,
          // Добавляем id если его нет
          id: person.id || `person-${index}`,
          face_images: person.face_images || []
        }));
      } catch (error) {
        console.error('Error loading results:', error);
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

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
  padding: 2rem;
  min-height: 100vh;
  background-color: #f8fafc;
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
  padding: 1rem;
  background: #f8fafc;
}

.main-image-container {
  margin-bottom: 1rem;
}

.person-main-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.person-main-image:hover {
  transform: scale(1.03);
}

.additional-images {
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  color: #3b82f6;
  font-weight: 500;
  cursor: pointer;
  padding: 0.5rem;
  margin: 0 auto;
  transition: color 0.2s;
}

.toggle-btn:hover {
  color: #2563eb;
}

.toggle-btn svg {
  transition: transform 0.3s ease;
}

.thumbnails-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
  margin-top: 1rem;
  max-height: 300px;
  overflow-y: auto;
  padding: 5px;
}

.person-thumbnail {
  width: 100%;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s;
}

.person-thumbnail:hover {
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