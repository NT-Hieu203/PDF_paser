<template>
  <div class="upload-container">
    <!-- Header -->
    <div class="upload-header">
      <h2 class="upload-title">
        <i class="fas fa-file-pdf"></i>
        Xử lý tài liệu PDF
      </h2>
      <p class="upload-description">
        Upload file PDF để trích xuất và phân tích nội dung tự động
      </p>
    </div>

    <!-- Upload Area -->
    <div class="upload-content">
      <!-- Drag & Drop Area -->
      <div 
        class="upload-area"
        :class="{ 
          'drag-over': isDragOver,
          'uploading': isUploading,
          'has-file': selectedFile
        }"
        @dragover.prevent="handleDragOver"
        @dragleave.prevent="handleDragLeave"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          @change="handleFileSelect"
          class="file-input"
        />

        <!-- Upload States -->
        <div v-if="!selectedFile && !isUploading" class="upload-prompt">
          <div class="upload-icon">
            <i class="fas fa-cloud-upload-alt"></i>
          </div>
          <h3>Kéo thả file PDF vào đây</h3>
          <p>hoặc <span class="click-text">nhấp để chọn file</span></p>
          <div class="file-requirements">
            <small>
              <i class="fas fa-info-circle"></i>
              Hỗ trợ file PDF, tối đa 10MB
            </small>
          </div>
        </div>

        <!-- Selected File Info -->
        <div v-if="selectedFile && !isUploading" class="selected-file">
          <div class="file-icon">
            <i class="fas fa-file-pdf"></i>
          </div>
          <div class="file-info">
            <h4>{{ selectedFile.name }}</h4>
            <p>{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          <button 
            @click.stop="removeFile" 
            class="remove-file-btn"
            title="Xóa file"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>

        <!-- Upload Progress -->
        <div v-if="isUploading" class="upload-progress">
          <div class="progress-icon">
            <i class="fas fa-spinner fa-spin"></i>
          </div>
          <h4>Đang xử lý file...</h4>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: uploadProgress + '%' }"
            ></div>
          </div>
          <p>{{ uploadProgress }}% - {{ getUploadStatus() }}</p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="upload-actions" v-if="selectedFile && !isUploading">
        <button 
          @click="startUpload" 
          class="upload-btn primary"
          :disabled="!selectedFile"
        >
          <i class="fas fa-upload"></i>
          Bắt đầu xử lý
        </button>
        <button 
          @click="resetUpload" 
          class="upload-btn secondary"
        >
          <i class="fas fa-redo"></i>
          Chọn lại
        </button>
      </div>

      <!-- Error Display -->
      <div v-if="error" class="error-message">
        <i class="fas fa-exclamation-triangle"></i>
        <span>{{ error }}</span>
        <button @click="clearError" class="close-error">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
    
    <!-- Phần Result Component đã được chuyển sang một route riêng biệt (/result) -->
    <!-- Do đó, không cần hiển thị Result ở đây nữa -->
  </div>
</template>

<script>
import apiBackend from '../services/api_backend.js'
// Không cần import Result ở đây nữa vì nó đã được định nghĩa trong router
// import Result from '../components/Result.vue' 

export default {
  name: 'Upload',
  // Xóa Result khỏi components vì nó sẽ được render bởi router
  // components: {
  //   Result 
  // },
  data() {
    return {
      selectedFile: null,
      isUploading: false,
      uploadProgress: 0,
      isDragOver: false,
      error: null,
      // Xóa processedData khỏi data() vì nó sẽ được truyền qua route params
      // processedData: null, 
      uploadStage: 'preparing' // preparing, uploading, processing, completed
    }
  },
  methods: {
    // File selection methods
    triggerFileInput() {
      if (!this.isUploading) {
        this.$refs.fileInput.click()
      }
    },

    handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        this.selectFile(file)
      }
    },

    selectFile(file) {
      // Validate file
      const validation = apiBackend.validatePdfFile(file)
      if (!validation.valid) {
        this.showError(validation.error)
        return
      }

      this.selectedFile = file
      this.clearError()
      this.$emit('file-selected', file)
    },

    removeFile() {
      this.selectedFile = null
      this.$refs.fileInput.value = ''
      this.$emit('file-removed')
    },

    // Drag and drop methods
    handleDragOver(event) {
      event.preventDefault()
      this.isDragOver = true
    },

    handleDragLeave(event) {
      event.preventDefault()
      this.isDragOver = false
    },

    handleDrop(event) {
      event.preventDefault()
      this.isDragOver = false
      
      const files = event.dataTransfer.files
      if (files.length > 0) {
        this.selectFile(files[0])
      }
    },

    // Upload methods
    async startUpload() {
      if (!this.selectedFile) {
        this.showError('Vui lòng chọn file PDF')
        return
      }

      this.isUploading = true
      this.uploadProgress = 0
      this.uploadStage = 'uploading'
      this.clearError()

      try {
        // Emit upload started event
        this.$emit('upload-started', this.selectedFile)

        const result = await apiBackend.uploadPdf(
          this.selectedFile,
          this.handleUploadProgress
        )

        if (result.success) {
          this.$router.push({
            name: 'Result', // Đảm bảo tên route là 'Result' như đã định nghĩa trong router/index.js
            params: {
              // Quan trọng: Sử dụng JSON.stringify() để chuyển đối tượng thành chuỗi JSON
              processedDataString: JSON.stringify(result.data) 
            }
          });
        } else {
          throw new Error(result.error)
        }
      } catch (error) {
        console.error('Upload error:', error)
        this.showError(error.message || 'Có lỗi xảy ra khi xử lý file')
        this.$emit('upload-error', error)
      } finally {
        this.isUploading = false
        // Nếu upload thất bại, có thể reset lại trạng thái
        if (this.error) {
          this.resetUpload(); 
        }
      }
    },

    handleUploadProgress(progress) {
      this.uploadProgress = progress
      if (progress >= 100) {
        this.uploadStage = 'processing'
      }
      this.$emit('upload-progress', progress)
    },

    // Reset methods
    resetUpload() {
      this.selectedFile = null
      this.uploadProgress = 0
      this.uploadStage = 'preparing'
      this.$refs.fileInput.value = ''
      this.clearError()
    },

    // Error handling
    showError(message) {
      this.error = message
      setTimeout(() => {
        this.clearError()
      }, 5000) // Auto hide after 5 seconds
    },

    clearError() {
      this.error = null
    },

    // Utility methods
    formatFileSize(bytes) {
      return apiBackend.formatFileSize(bytes)
    },

    getUploadStatus() {
      switch (this.uploadStage) {
        case 'uploading':
          return 'Đang tải lên...'
        case 'processing':
          return 'Đang xử lý nội dung...'
        case 'completed': // Trạng thái này có thể không còn cần thiết nếu chuyển hướng ngay
          return 'Hoàn thành!'
        default:
          return 'Chuẩn bị...'
      }
    },
    
  },

  // Cleanup on component destroy
  beforeUnmount() {
    this.clearError()
  }
}
</script>

  
  <style scoped>
  .upload-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .upload-header {
    text-align: center;
    margin-bottom: 30px;
  }
  
  .upload-title {
    color: #2c3e50;
    font-size: 2rem;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
  
  .upload-title i {
    color: #e74c3c;
  }
  
  .upload-description {
    color: #7f8c8d;
    font-size: 1.1rem;
    margin: 0;
  }
  
  .upload-content {
    margin-bottom: 30px;
  }
  
  .upload-area {
    border: 3px dashed #bdc3c7;
    border-radius: 12px;
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #f8f9fa;
    position: relative;
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .upload-area:hover {
    border-color: #3498db;
    background: #e3f2fd;
  }
  
  .upload-area.drag-over {
    border-color: #2ecc71;
    background: #e8f5e8;
    transform: scale(1.02);
  }
  
  .upload-area.uploading {
    border-color: #f39c12;
    background: #fff3cd;
    cursor: not-allowed;
  }
  
  .upload-area.has-file {
    border-color: #27ae60;
    background: #d5f4e6;
  }
  
  .file-input {
    display: none;
  }
  
  .upload-prompt {
    color: #7f8c8d;
  }
  
  .upload-icon {
    font-size: 3rem;
    color: #3498db;
    margin-bottom: 20px;
  }
  
  .upload-prompt h3 {
    margin: 0 0 10px 0;
    color: #2c3e50;
    font-size: 1.3rem;
  }
  
  .upload-prompt p {
    margin: 0 0 15px 0;
    font-size: 1rem;
  }
  
  .click-text {
    color: #3498db;
    font-weight: 600;
    text-decoration: underline;
  }
  
  .file-requirements {
    background: #e3f2fd;
    padding: 8px 15px;
    border-radius: 20px;
    display: inline-block;
  }
  
  .file-requirements small {
    color: #1976d2;
    font-size: 0.9rem;
  }
  
  .selected-file {
    display: flex;
    align-items: center;
    gap: 15px;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  
  .file-icon {
    font-size: 2rem;
    color: #e74c3c;
  }
  
  .file-info {
    flex: 1;
    text-align: left;
  }
  
  .file-info h4 {
    margin: 0 0 5px 0;
    color: #2c3e50;
    font-size: 1.1rem;
  }
  
  .file-info p {
    margin: 0;
    color: #7f8c8d;
    font-size: 0.9rem;
  }
  
  .remove-file-btn {
    background: #e74c3c;
    color: white;
    border: none;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.3s ease;
  }
  
  .remove-file-btn:hover {
    background: #c0392b;
  }
  
  .upload-progress {
    color: #f39c12;
  }
  
  .progress-icon {
    font-size: 2rem;
    margin-bottom: 15px;
  }
  
  .upload-progress h4 {
    margin: 0 0 15px 0;
    color: #2c3e50;
  }
  
  .progress-bar {
    width: 100%;
    height: 8px;
    background: #ecf0f1;
    border-radius: 4px;
    overflow: hidden;
    margin: 15px 0;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #3498db, #2ecc71);
    transition: width 0.3s ease;
    border-radius: 4px;
  }
  
  .upload-progress p {
    margin: 0;
    color: #7f8c8d;
    font-size: 0.9rem;
  }
  
  .upload-actions {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin-top: 20px;
  }
  
  .upload-btn {
    padding: 12px 24px;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .upload-btn.primary {
    background: #3498db;
    color: white;
  }
  
  .upload-btn.primary:hover {
    background: #2980b9;
    transform: translateY(-2px);
  }
  
  .upload-btn.secondary {
    background: #95a5a6;
    color: white;
  }
  
  .upload-btn.secondary:hover {
    background: #7f8c8d;
  }
  
  .upload-btn:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
    transform: none;
  }
  
  .error-message {
    background: #f8d7da;
    color: #721c24;
    padding: 12px 16px;
    border-radius: 6px;
    margin-top: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
    border: 1px solid #f5c6cb;
  }
  
  .error-message i {
    color: #e74c3c;
  }
  
  .close-error {
    background: none;
    border: none;
    color: #721c24;
    cursor: pointer;
    margin-left: auto;
    padding: 0;
    font-size: 1.1rem;
  }
  
  .close-error:hover {
    color: #e74c3c;
  }
  
  .result-section {
    margin-top: 40px;
    padding-top: 30px;
    border-top: 2px solid #ecf0f1;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .upload-container {
      padding: 15px;
    }
    
    .upload-title {
      font-size: 1.5rem;
    }
    
    .upload-area {
      padding: 30px 15px;
    }
    
    .upload-actions {
      flex-direction: column;
    }
    
    .upload-btn {
      width: 100%;
      justify-content: center;
    }
  }
  
  /* Animation keyframes */
  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
  }
  
  .upload-area.uploading {
    animation: pulse 2s infinite;
  }
  </style>