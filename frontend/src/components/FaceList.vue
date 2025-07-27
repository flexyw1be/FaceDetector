<template>
  <div class="p-4">
    <h2 class="text-2xl font-bold mb-4">Detected Faces</h2>

    <div v-if="loading" class="text-center py-8">
      <p>Loading...</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="face in faces" :key="face.id" class="border rounded p-4">
        <img :src="`/static/${face.face_image_path.split('static/')[1]}`" alt="Detected face" class="w-full h-48 object-cover mb-2">
        <div class="text-sm">
          <p><span class="font-semibold">Gender:</span> {{ face.gender }}</p>
          <p><span class="font-semibold">Age:</span> {{ face.age_group }}</p>
          <p><span class="font-semibold">Detected:</span> {{ new Date(face.detection_time).toLocaleString() }}</p>
          <p><span class="font-semibold">Source:</span> {{ face.video_source }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      faces: [],
      loading: true
    }
  },
  async mounted() {
    try {
      const response = await fetch('http://localhost:8000/faces/')
      this.faces = await response.json()
    } catch (err) {
      console.error("Error fetching faces:", err)
    } finally {
      this.loading = false
    }
  }
}
</script>