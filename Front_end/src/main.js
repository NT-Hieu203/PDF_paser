// main.js (hoặc main.ts)
import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // Import router của bạn


const app = createApp(App);

// Sử dụng router trong ứng dụng Vue của bạn
app.use(router); 

// Gắn ứng dụng vào phần tử DOM có id="app"
app.mount('#app');