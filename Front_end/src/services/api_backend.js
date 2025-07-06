// api_backend.js - API service cho Vue.js frontend
import axios from 'axios'

// Cấu hình base URL cho API backend
const API_BASE_URL = 'http://localhost:5000'

// Tạo axios instance với cấu hình mặc định
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 phút timeout cho việc xử lý PDF có thể mất thời gian
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

// Interceptor để xử lý response và error
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    if (error.response) {
      // Server responded with error status
      console.error('Error Status:', error.response.status)
      console.error('Error Data:', error.response.data)
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received:', error.request)
    } else {
      // Something else happened
      console.error('Error Message:', error.message)
    }
    return Promise.reject(error)
  }
)

/**
 * Class chứa các phương thức để tương tác với API backend
 */
class ApiBackend {
  /**
   * Upload file PDF và xử lý
   * @param {File} pdfFile - File PDF cần upload
   * @param {Function} onUploadProgress - Callback function để theo dõi tiến trình upload
   * @returns {Promise} Promise chứa kết quả xử lý
   */
  async uploadPdf(pdfFile, onUploadProgress = null) {
    try {
      const formData = new FormData()
      formData.append('pdfFile', pdfFile)

      const config = {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }

      // Thêm callback cho tiến trình upload nếu có
      if (onUploadProgress) {
        config.onUploadProgress = (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          )
          onUploadProgress(percentCompleted)
        }
      }

      const response = await apiClient.post('/api/upload_pdf', formData, config)
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Lỗi khi upload file PDF',
        details: error
      }
    }
  }

  /**
   * Lấy danh sách ảnh các trang của file đã xử lý
   * @param {string} fileId - ID của file đã được xử lý
   * @returns {Promise} Promise chứa danh sách ảnh các trang
   */
  async getPageImages(fileId) {
    try {
      const response = await apiClient.get(`/api/get_page_images/${fileId}`)
      return {
        success: true,
        data: response.data
      }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Lỗi khi lấy danh sách ảnh trang',
        details: error
      }
    }
  }

  /**
   * Tạo URL để truy cập file PDF đã upload
   * @param {string} filename - Tên file PDF
   * @returns {string} URL đầy đủ để truy cập file
   */
  getPdfUrl(filename) {
    return `${API_BASE_URL}/uploads/${filename}`
  }

  /**
   * Tạo URL để truy cập ảnh trang cụ thể
   * @param {string} fileId - ID của file
   * @param {string} pageName - Tên ảnh trang (vd: page_1.png)
   * @returns {string} URL đầy đủ để truy cập ảnh trang
   */
  getPageImageUrl(fileId, pageName) {
    return `${API_BASE_URL}/page_images/${fileId}/${pageName}`
  }

  /**
   * Kiểm tra kết nối với server
   * @returns {Promise} Promise kiểm tra kết nối
   */
  async checkConnection() {
    try {
      const response = await fetch(`${API_BASE_URL}/`, { method: 'HEAD' })
      return {
        success: response.ok,
        status: response.status
      }
    } catch (error) {
      return {
        success: false,
        error: 'Không thể kết nối đến server',
        details: error
      }
    }
  }

  /**
   * Validate file PDF trước khi upload
   * @param {File} file - File cần validate
   * @returns {Object} Kết quả validation
   */
  validatePdfFile(file) {
    const maxSize = 5 * 1024 * 1024 // 5MB
    const allowedTypes = ['application/pdf']

    if (!file) {
      return {
        valid: false,
        error: 'Vui lòng chọn file'
      }
    }

    if (!allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'Chỉ chấp nhận file PDF'
      }
    }

    if (file.size > maxSize) {
      return {
        valid: false,
        error: 'File quá lớn. Kích thước tối đa là 5MB'
      }
    }

    return {
      valid: true
    }
  }

  /**
   * Định dạng kích thước file
   * @param {number} bytes - Kích thước file theo bytes
   * @returns {string} Chuỗi định dạng kích thước
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
}

// Tạo instance duy nhất
const apiBackend = new ApiBackend()

// Export default instance
export default apiBackend

// Export class để có thể tạo instance mới nếu cần
export { ApiBackend }

// Export các constants nếu cần sử dụng ở nơi khác
export const API_CONFIG = {
  BASE_URL: API_BASE_URL,
  TIMEOUT: 300000,
  MAX_FILE_SIZE: 5 * 1024 * 1024 // 5MB
}