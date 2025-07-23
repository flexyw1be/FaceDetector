<template>
<UploadPage/> 
<RouterView/>
</template>

<script>
import { RouterView } from 'vue-router';
import UploadPage from './views/UploadPage.vue';
</script>

<style>
body {
  margin: 0;
  padding: 0;
  background-color: #f3f6fd;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  text-align: center;
  color: #2c3e50;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

header {
  display: flex;
  align-items: center;
  padding: 20px;
  background-color: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

header img {
  height: 28px;
  margin-right: 10px;
}

.logo-text {
  font-weight: bold;
  font-size: 16px;
}

main {
  flex: 1;
  padding: 40px 20px;
}

.main-title {
  font-size: 24px;
  margin-bottom: 30px;
}
</style>
