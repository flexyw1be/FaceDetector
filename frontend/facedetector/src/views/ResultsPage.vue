<template>
  <div class="results-page">
    <h2>Найденные лица: {{ persons.length }}</h2>
    <div v-for="(person, index) in persons" :key="index" class="person-card">
      <h3>Лицо {{ index + 1 }}: {{ person.person.gender }}, {{ person.person.age_group }}</h3>
      <p>Всего появилось: {{ person.detections.length }} раз</p>
      <div class="face-images">
        <img
            v-for="(img, i) in person.person.face_images"
            :key="i"
            :src="`http://localhost:8000${img}`"
            alt="Face"
            class="face-thumb"
            @click="showFullFace(img)"
        />
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      persons: []
    }
  },
  async mounted() {
    try {
      const response = await axios.get('http://localhost:8000/results/');
      this.persons = response.data.persons;
    } catch (err) {
      console.error('Error loading results:', err);
    }
  },
  methods: {
    showFullFace(img) {
      window.open(`http://localhost:8000${img}`, '_blank');
    }
  }
}
</script>

<style scoped>
.person-card {
  border: 1px solid #ddd;
  padding: 15px;
  margin: 15px 0;
  border-radius: 8px;
  text-align: left;
}

.face-images {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.face-thumb {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}

.face-thumb:hover {
  border-color: #007bff;
}
</style>