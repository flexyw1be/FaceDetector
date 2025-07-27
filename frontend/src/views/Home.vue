<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <!-- Hero Section -->
      <div class="text-center mb-16">
        <h1 class="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
          Face Detection System
        </h1>
        <p class="mt-5 max-w-xl mx-auto text-xl text-gray-500">
          Advanced face detection with gender and age estimation using OpenCV and AI
        </p>
      </div>

      <!-- Features Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
        <div class="bg-white p-6 rounded-lg shadow-md">
          <div class="text-blue-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">Real-time Detection</h3>
          <p class="text-gray-500">
            Detect faces in real-time from your webcam with bounding boxes and analysis.
          </p>
          <router-link
            to="/detection"
            class="mt-4 inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            Try it now
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>

        <div class="bg-white p-6 rounded-lg shadow-md">
          <div class="text-blue-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">Gender & Age Analysis</h3>
          <p class="text-gray-500">
            Our AI models estimate gender and age range for each detected face.
          </p>
        </div>

        <div class="bg-white p-6 rounded-lg shadow-md">
          <div class="text-blue-500 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 class="text-lg font-medium text-gray-900 mb-2">Face Database</h3>
          <p class="text-gray-500">
            All detected faces are stored in a searchable database with timestamps.
          </p>
          <router-link
            to="/faces"
            class="mt-4 inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            View database
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </router-link>
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="bg-white p-6 rounded-lg shadow-md mb-16">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">System Statistics</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-blue-50 p-4 rounded-lg">
            <p class="text-sm font-medium text-gray-500">Total Faces Detected</p>
            <p class="text-2xl font-semibold text-blue-600">{{ stats.totalFaces || 'Loading...' }}</p>
          </div>
          <div class="bg-green-50 p-4 rounded-lg">
            <p class="text-sm font-medium text-gray-500">Male/Female Ratio</p>
            <p class="text-2xl font-semibold text-green-600">
              {{ stats.maleCount || 0 }} / {{ stats.femaleCount || 0 }}
            </p>
          </div>
          <div class="bg-purple-50 p-4 rounded-lg">
            <p class="text-sm font-medium text-gray-500">Most Common Age</p>
            <p class="text-2xl font-semibold text-purple-600">{{ stats.commonAge || 'N/A' }}</p>
          </div>
          <div class="bg-yellow-50 p-4 rounded-lg">
            <p class="text-sm font-medium text-gray-500">Last Detection</p>
            <p class="text-2xl font-semibold text-yellow-600">
              {{ stats.lastDetection ? formatTimeAgo(stats.lastDetection) : 'Never' }}
            </p>
          </div>
        </div>
      </div>

      <!-- How It Works -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold text-gray-900 mb-6">How It Works</h2>
        <div class="space-y-6">
          <div class="flex items-start">
            <div class="flex-shrink-0 bg-blue-100 rounded-full p-2 mr-4">
              <span class="text-blue-600 font-bold">1</span>
            </div>
            <div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">Face Detection</h3>
              <p class="text-gray-500">
                Our system uses OpenCV with DNN module to detect faces in images or video streams.
                The model can detect multiple faces simultaneously with high accuracy.
              </p>
            </div>
          </div>

          <div class="flex items-start">
            <div class="flex-shrink-0 bg-blue-100 rounded-full p-2 mr-4">
              <span class="text-blue-600 font-bold">2</span>
            </div>
            <div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">Gender & Age Estimation</h3>
              <p class="text-gray-500">
                For each detected face, we use pre-trained Caffe models to estimate gender (Male/Female)
                and age range (8 categories from 0-2 to 60-100 years).
              </p>
            </div>
          </div>

          <div class="flex items-start">
            <div class="flex-shrink-0 bg-blue-100 rounded-full p-2 mr-4">
              <span class="text-blue-600 font-bold">3</span>
            </div>
            <div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">Data Storage</h3>
              <p class="text-gray-500">
                All detected faces are stored in a SQLite database with timestamps, gender and age information.
                You can search, filter and analyze the collected data.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      stats: {
        totalFaces: 0,
        maleCount: 0,
        femaleCount: 0,
        commonAge: '',
        lastDetection: null
      },
      loading: true
    }
  },
  async mounted() {
    await this.fetchStats()
  },
  methods: {
    async fetchStats() {
      try {
        // Здесь должен быть запрос к вашему API для получения статистики
        // Это примерная реализация - вам нужно адаптировать её под ваш бэкенд
        const response = await fetch('http://localhost:8000/stats/')
        if (response.ok) {
          this.stats = await response.json()
        }
      } catch (error) {
        console.error('Error fetching stats:', error)
      } finally {
        this.loading = false
      }
    },
    formatTimeAgo(timestamp) {
      const now = new Date()
      const detectionTime = new Date(timestamp)
      const diffInSeconds = Math.floor((now - detectionTime) / 1000)

      if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`
      if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
      if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
      return `${Math.floor(diffInSeconds / 86400)} days ago`
    }
  }
}
</script>

<style scoped>
/* Дополнительные стили при необходимости */
</style>