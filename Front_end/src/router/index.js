// router/index.js
import { createRouter, createWebHistory } from 'vue-router';

// Nhập các component mà bạn muốn sử dụng làm trang
import Upload from '../components/upload.vue';
import Result from '../components/Result.vue';

/**
 * Định nghĩa các tuyến đường (routes) cho ứng dụng Vue của bạn.
 * Mỗi đối tượng tuyến đường bao gồm:
 * - path: Đường dẫn URL.
 * - name: Tên định danh cho tuyến đường (để điều hướng bằng tên).
 * - component: Component sẽ được render khi tuyến đường này được kích hoạt.
 * - props: Nếu là 'true', tất cả các route params sẽ được truyền làm props cho component.
 * - redirect: Chuyển hướng đến một tuyến đường khác.
 */
const routes = [
  {
    path: '/',
    name: 'Home',
    // Trang chủ '/' sẽ tự động chuyển hướng đến trang tải lên '/upload'.
    // Nếu bạn muốn một trang chủ riêng, hãy thay đổi component ở đây.
    redirect: '/upload' 
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload,
    // Bạn có thể thêm meta fields nếu cần, ví dụ: meta: { requiresAuth: true }
  },
  {
    path: '/result',
    name: 'Result',
    component: Result,
    // Quan trọng: 'props: true' cho phép truyền các tham số (params) từ route
    // như là các props cho component Result.vue.
    // Điều này sẽ giúp bạn truyền 'processedData' từ Upload.vue sang Result.vue.
    props: true 
  }
];

/**
 * Tạo một đối tượng router mới.
 * - history: Sử dụng createWebHistory để tạo ra các URL sạch (ví dụ: /upload thay vì /#upload).
 * Sử dụng import.meta.env.BASE_URL để xử lý base URL trong các dự án Vite/Vue CLI.
 * - routes: Mảng các tuyến đường đã định nghĩa.
 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
