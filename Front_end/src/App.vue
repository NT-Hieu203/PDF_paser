<!-- App.vue -->
<template>
  <div id="app">
    <!-- Các thành phần layout chung như header, footer có thể đặt ở đây -->
    <router-view />
    <!-- router-view sẽ hiển thị component tương ứng với route hiện tại -->
  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style>
/* CSS toàn cục */
body {
  font-family: 'Inter', sans-serif; /* Đảm bảo bạn đã nhập font này hoặc thay đổi */
  margin: 0;
  padding: 0;
  background-color: #f4f7f6;
  color: #333;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

#app {
  width: 100%;
  box-sizing: border-box;
}
</style>