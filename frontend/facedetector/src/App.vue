<template>
  <div id="app">
    <header>
      <h1>Face Detector</h1>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  text-align: center;
  color: #2c3e50;
  margin-top: 20px;
}
header {
  padding: 10px;
  background: #f0f0f0;
  border-bottom: 1px solid #ddd;
}
main {
  padding: 20px;
}
</style>