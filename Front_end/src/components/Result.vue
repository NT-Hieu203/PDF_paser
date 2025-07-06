<template>
  <div class="result-container">
    <!-- Header -->
    <div class="result-header">
      <div class="result-title">
        <h2>
          <i class="fas fa-file-alt"></i>
          Kết quả phân tích tài liệu
        </h2>
        <!-- Sử dụng parsedData thay vì data trực tiếp -->
        <div class="result-stats" v-if="parsedData">
          <span class="stat-item">
            <i class="fas fa-file-pdf"></i>
            {{ parsedData.total_pages }} trang
          </span>
          <span class="stat-item">
            <i class="fas fa-paragraph"></i>
            {{ parsedData.total_paragraphs }} đoạn văn
          </span>
        </div>
      </div>
      
      <div class="result-actions">

        <button @click="resetResult" class="action-btn reset">
          <i class="fas fa-redo"></i>
          Xử lý file khác
        </button>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="result-content">
      <!-- Left Panel - PDF Viewer -->
      <div class="pdf-panel">
        <div class="panel-header">
          <h3>
            <i class="fas fa-eye"></i>
            Xem tài liệu
          </h3>
          <div class="pdf-controls">
            <!-- Thêm nút điều hướng trang -->
            <button @click="prevPage" :disabled="selectedPageIndex === 0" class="page-nav-btn">
              <i class="fas fa-chevron-left"></i>
            </button>
            <select v-model="selectedPageIndex" @change="scrollToPageAndRedraw" class="page-selector" v-if="pageImages.length > 0">
              <option v-for="(page, index) in pageImages" :key="index" :value="index">
                Trang {{ page.page_number }}
              </option>
            </select>
            <button @click="nextPage" :disabled="selectedPageIndex === pageImages.length - 1" class="page-nav-btn">
              <i class="fas fa-chevron-right"></i>
            </button>
          </div>
        </div>
        
        <div class="pdf-viewer" ref="pdfViewer">
          <div v-if="isLoadingImages" class="loading-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Đang tải ảnh trang...</p>
          </div>
          
          <div v-else-if="pageImages.length > 0" class="pages-container">
            <!-- Chỉ hiển thị canvas của trang đang chọn -->
            <div 
              v-for="(page, index) in pageImages" 
              :key="page.page_number"
              v-show="index === selectedPageIndex"
              class="page-wrapper"
              :class="{ 'active-page': index === selectedPageIndex }"
            >
              <div class="page-number">Trang {{ page.page_number }}</div>
              <canvas
                :ref="`pageCanvas-${index}`"
                class="page-canvas"
                @click="handleCanvasClick($event, index)"
              ></canvas>
            </div>
          </div>
          
          <div v-else class="error-state">
            <i class="fas fa-exclamation-triangle"></i>
            <p>Không thể tải ảnh trang</p>
          </div>
        </div>
      </div>

      <!-- Right Panel - Text Analysis / Selected Paragraph Details -->
      <div class="text-panel">
        <div class="panel-header">
          <h3>
            <i class="fas fa-list-alt"></i>
            Nội dung phân tích
          </h3>
          <div class="text-controls" v-if="!selectedParagraphDetails">
            <!-- Filter Controls -->
            <div class="filter-group">
              <select v-model="filterType" @change="applyFilters" class="filter-select">
                <option value="">Tất cả loại</option>
                <option value="title">Tiêu đề</option>
                <option value="text">Văn bản</option>
                <option value="table">Bảng</option>
                <option value="figure">Hình ảnh</option>
                <option value="list">Danh sách</option>
              </select>
              
              <!-- FilterPage giờ đây sẽ được cập nhật tự động theo selectedPageIndex -->
              <!-- Vẫn giữ option "Tất cả trang" nếu muốn cho phép người dùng xem tất cả đoạn văn -->
              <select v-model="filterPage" @change="applyFilters" class="filter-select">
                <option value="">Tất cả trang</option>
                <option v-for="page in uniquePages" :key="page" :value="page">
                  Trang {{ page + 1 }}
                </option>
              </select>
            </div>
            
            <!-- Search -->
            <div class="search-group">
              <input 
                v-model="searchQuery" 
                @input="applyFilters"
                placeholder="Tìm kiếm nội dung..."
                class="search-input"
              />
              <div class="action-search-btn reset" >
                <i class="fas fa-search search-icon"></i>
              </div>
              
            </div>
          </div>
          <button v-if="selectedParagraphDetails" @click="clearSelectedParagraph" class="action-btn back-to-list">
            <i class="fas fa-arrow-left"></i> Quay lại danh sách
          </button>
        </div>

        <div class="text-content" ref="textContent">
          <div v-if="internalError" class="error-message">
            <i class="fas fa-exclamation-triangle"></i>
            <span>{{ internalError }}</span>
            <button @click="internalError = null" class="close-error">
              <i class="fas fa-times"></i>
            </button>
          </div>

          <!-- Display Selected Paragraph Details -->
          <div v-if="selectedParagraphDetails" class="selected-paragraph-details">
            <h4>Chi tiết đoạn văn</h4>
            <div class="detail-item">
              <strong>Loại:</strong> <span class="paragraph-type-badge" :class="`type-${selectedParagraphDetails.type}`">{{ getTypeLabel(selectedParagraphDetails.type) }}</span>
            </div>
            <div class="detail-item">
              <strong>Trang:</strong> {{ selectedParagraphDetails.page_index + 1 }}
            </div>
            <div class="detail-item">
              <strong>Thứ tự đọc:</strong> #{{ selectedParagraphDetails.reading_order }}
            </div>
            <div class="detail-item" v-if="selectedParagraphDetails.column !== 'unknown'">
              <strong>Cột:</strong> {{ getColumnLabel(selectedParagraphDetails.column) }}
            </div>
            <div class="detail-item" v-if="selectedParagraphDetails.is_title">
              <strong>Là tiêu đề:</strong> Có
            </div>
            <div class="detail-item">
              <strong>Index:</strong> {{ selectedParagraphDetails.index }}
            </div> 
            <div class="detail-item">
              <strong>Parent Index:</strong> {{ selectedParagraphDetails.parent_index }}
            </div>
             <div class="detail-item full-text-detail">
              <strong>Nội dung: </strong>
              <div class="full-text-content">
                {{ selectedParagraphDetails.full_text }}
              </div>
            </div>
             <div class="detail-item bbox-detail" v-if="selectedParagraphDetails.bbox && selectedParagraphDetails.bbox.length === 4">
              <strong>Bbox:</strong> [{{ selectedParagraphDetails.bbox.map(coord => coord.toFixed(2)).join(', ') }}]
            </div>
          </div>
          
          <!-- Display Filtered Paragraphs List -->
          <div v-else-if="filteredParagraphs.length === 0" class="empty-state">
            <i class="fas fa-search"></i>
            <p>Không tìm thấy nội dung phù hợp</p>
          </div>
          
          <div v-else class="paragraphs-list">
            <div 
              v-for="(paragraph, index) in filteredParagraphs" 
              :key="paragraph.index"
              class="paragraph-item"
              :class="[
                `type-${paragraph.type}`,
                { 
                  'is-title': paragraph.is_title,
                  'is-full-width': paragraph.is_full_width,
                  'selected': selectedParagraph === paragraph.index
                }
              ]"
              @click="selectParagraph(paragraph)"
            >
              <!-- Paragraph Header -->
              <div class="paragraph-header">
                <div class="paragraph-meta">
                  <span class="paragraph-type" :class="`type-${paragraph.type}`">
                    <i :class="getTypeIcon(paragraph.type)"></i>
                    {{ getTypeLabel(paragraph.type) }}
                  </span>
                  
                  <span class="paragraph-page">
                    Trang {{ paragraph.page_index + 1 }}
                  </span>
                  
                  <span class="paragraph-order">
                    #{{ paragraph.reading_order }}
                  </span>
                  
                  <span v-if="paragraph.column !== 'unknown'" class="paragraph-column">
                    {{ getColumnLabel(paragraph.column) }}
                  </span>
                </div>
                
                <button 
                  @click.stop="goToPage(paragraph.page_index)"
                  class="goto-page-btn"
                  title="Chuyển đến trang"
                >
                  <i class="fas fa-external-link-alt"></i>
                </button>
              </div>

              <!-- Paragraph Content -->
              <div class="paragraph-content">
                <div 
                  class="paragraph-text"
                  :class="{ 'expanded': expandedParagraphs.includes(paragraph.index) }"
                >
                  {{ paragraph.full_text }}
                </div>
                
                <button 
                  v-if="paragraph.full_text.length > 200"
                  @click.stop="toggleExpanded(paragraph.index)"
                  class="expand-btn"
                >
                  {{ expandedParagraphs.includes(paragraph.index) ? 'Thu gọn' : 'Xem thêm' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import apiBackend from '../services/api_backend.js'

export default {
  name: 'Result',
  props: {
    // Thay đổi prop 'data' thành 'processedDataString' và kiểu String
    processedDataString: {
      type: String,
      required: false, // Không yêu cầu nếu bạn muốn Result có thể tải trực tiếp
      default: '{}' // Mặc định là một chuỗi JSON rỗng để tránh lỗi parse
    }
  },
  data() {
    return {
      // pageImages sẽ lưu trữ thông tin ảnh và đối tượng Image đã tải
      pageImages: [], 
      // pageCanvases sẽ lưu trữ các context 2D của từng canvas
      pageCanvases: {},
      isLoadingImages: true,
      selectedPageIndex: 0,
      selectedParagraph: null, // index của đoạn văn được chọn
      selectedParagraphDetails: null, // Chi tiết đầy đủ của đoạn văn được chọn
      expandedParagraphs: [],
      
      // Filtering and searching
      filterType: '',
      filterPage: '', // Giá trị này sẽ được đồng bộ với selectedPageIndex
      searchQuery: '',
      filteredParagraphs: [],
      
      // UI state
      internalError: null, 
    }
  },
  computed: {
    // Tạo một computed property để parse chuỗi JSON thành đối tượng
    parsedData() {
      try {
        if (this.processedDataString && this.processedDataString !== '{}') {
          return JSON.parse(this.processedDataString);
        }
        return null;
      } catch (e) {
        console.error("Lỗi khi parse processedDataString:", e);
        this.showError("Dữ liệu kết quả không hợp lệ.");
        return null;
      }
    },
    uniquePages() {
      if (!this.parsedData || !this.parsedData.info_all_paragraphs) return [];
      const pages = [...new Set(this.parsedData.info_all_paragraphs.map(p => p.page_index))]
      return pages.sort((a, b) => a - b)
    }
  },
  async mounted() {
    // Chỉ tải ảnh nếu có dữ liệu và file_id
    if (this.parsedData && this.parsedData.file_id) {
      await this.loadPageImages();
    } else {
      this.isLoadingImages = false;
    }
    // Initialize filters only if paragraphs data exists
    if (this.parsedData && this.parsedData.info_all_paragraphs) {
      this.initializeFilters();
      // Sau khi tải ảnh và khởi tạo filter, vẽ nội dung trang hiện tại
      this.$nextTick(() => {
        if (this.pageImages.length > 0) {
          this.drawPageContent(this.selectedPageIndex);
        }
      });
    } else if (!this.parsedData) {
      this.showError('Không có dữ liệu phân tích nào được truyền vào.');
    }
  },
  methods: {
    // Load page images onto canvas
    async loadPageImages() {
      this.isLoadingImages = true;
      this.pageImages = []; // Reset
      this.pageCanvases = {}; // Reset

      if (!this.parsedData || !this.parsedData.file_id || !this.parsedData.page_images_url) {
        this.showError('Không tìm thấy file_id hoặc URL ảnh trang để tải.');
        this.isLoadingImages = false;
        return;
      }

      try {
        const result = await apiBackend.getPageImages(this.parsedData.file_id);
        
        if (result.success && result.data && result.data.page_images) {
          const loadedImages = await Promise.all(
            result.data.page_images.map(p => {
              return new Promise((resolve, reject) => {
                const img = new Image();
                img.src = p.image_url;
                img.onload = () => resolve({ page_number: p.page_number, image_url: p.image_url, img_obj: img });
                img.onerror = () => {
                  console.error(`Failed to load image for page ${p.page_number}: ${p.image_url}`);
                  resolve({ page_number: p.page_number, image_url: p.image_url, img_obj: null, error: true }); // Trả về lỗi để xử lý sau
                };
              });
            })
          );
          this.pageImages = loadedImages.filter(img => img.img_obj); // Chỉ giữ lại ảnh tải thành công
          if (this.pageImages.length === 0) {
            this.showError('Không có ảnh trang nào được tải thành công.');
          }
        } else {
          this.showError('Không thể tải ảnh trang: ' + (result.error || 'Dữ liệu ảnh trang không hợp lệ.'));
        }
      } catch (error) {
        console.error('Error loading page images:', error);
        this.showError(error.message || 'Lỗi khi tải ảnh trang từ API.');
      } finally {
        this.isLoadingImages = false;
        // Sau khi tất cả ảnh đã được tải (hoặc thất bại), tiến hành vẽ trang hiện tại
        this.$nextTick(() => {
          if (this.pageImages.length > 0) {
            this.drawPageContent(this.selectedPageIndex);
          }
        });
      }
    },

    /**
     * Draws the image and all bounding boxes for a specific page.
     * @param {number} pageIndex - The 0-based index of the page to draw.
     */
    drawPageContent(pageIndex) {
      if (!this.pageImages || this.pageImages.length === 0) return;

      const pageData = this.pageImages[pageIndex];
      if (!pageData || !pageData.img_obj) {
        console.warn(`Không có dữ liệu ảnh hoặc đối tượng ảnh cho trang ${pageIndex + 1}`);
        return;
      }

      // Lấy tham chiếu đến canvas của trang hiện tại
      const canvasRefName = `pageCanvas-${pageIndex}`;
      const canvas = this.$refs[canvasRefName]?.[0];

      if (!canvas) {
        console.warn(`Không tìm thấy canvas cho trang ${pageIndex + 1}`);
        return;
      }

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error("Không thể lấy context 2D của canvas.");
        return;
      }

      const img = pageData.img_obj;

      // Đặt kích thước canvas bằng với kích thước ảnh để vẽ 1:1, sau đó CSS sẽ scale
      // Hoặc đặt kích thước canvas dựa trên kích thước container và tính scale factor
      const parentWidth = this.$refs.pdfViewer ? this.$refs.pdfViewer.clientWidth - 30 : img.width; // Giảm padding
      const scale = parentWidth / img.width;

      canvas.width = img.width;
      canvas.height = img.height;

      // Cập nhật CSS để canvas tự động co giãn trong container
      canvas.style.width = '100%';
      canvas.style.height = 'auto';

      ctx.clearRect(0, 0, canvas.width, canvas.height); // Xóa canvas cũ
      ctx.drawImage(img, 0, 0, img.width, img.height); // Vẽ ảnh

      // Lọc các đoạn văn bản thuộc trang hiện tại
      const paragraphsOnPage = this.parsedData.info_all_paragraphs.filter(
        p => p.page_index === pageIndex
      );

      paragraphsOnPage.forEach(paragraph => {
        // 'bbox' là bbox, có dạng [x1, y1, x2, y2]
        if (paragraph.bbox && paragraph.bbox.length === 4) {
          const isSelected = (this.selectedParagraph === paragraph.index);
          this.drawBbox(ctx, paragraph.bbox, 1, 1, isSelected); // Scale 1:1 vì canvas đã có kích thước gốc của ảnh
        }
      });
    },

    /**
     * Helper to draw a single bounding box on the canvas.
     * @param {CanvasRenderingContext2D} ctx - The 2D rendering context of the canvas.
     * @param {Array<number>} bbox - Bounding box coordinates [x1, y1, x2, y2].
     * @param {number} scaleX - X-axis scaling factor.
     * @param {number} scaleY - Y-axis scaling factor.
     * @param {boolean} isSelected - Whether this bbox should be highlighted.
     */
    drawBbox(ctx, bbox, scaleX, scaleY, isSelected = false) {
      const [x1, y1, x2, y2] = bbox;
      const width = x2 - x1;
      const height = y2 - y1;

      ctx.save(); // Lưu trạng thái hiện tại của context

      if (isSelected) {
        ctx.strokeStyle = '#007bff'; // Màu xanh nổi bật
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]); // Nét đứt
      } else {
        ctx.strokeStyle = 'rgba(255, 0, 0, 0.4)'; // Màu đỏ trong suốt
        ctx.lineWidth = 1;
        ctx.setLineDash([]); // Đảm bảo không nét đứt
      }
      ctx.fillStyle = 'rgba(255, 255, 0, 0.1)'; // Nền vàng trong suốt

      ctx.strokeRect(x1 * scaleX, y1 * scaleY, width * scaleX, height * scaleY);
      ctx.fillRect(x1 * scaleX, y1 * scaleY, width * scaleX, height * scaleY);

      ctx.restore(); // Khôi phục trạng thái context
    },

    /**
     * Handles click events on the canvas to detect clicks on bounding boxes.
     * @param {MouseEvent} event - The click event.
     * @param {number} pageIndex - The 0-based index of the current page.
     */
    handleCanvasClick(event, pageIndex) {
      const canvas = event.target;
      const rect = canvas.getBoundingClientRect(); // Kích thước thực tế của canvas trên màn hình
      
      // Tính toán tỷ lệ co giãn của canvas so với kích thước gốc của ảnh
      // (Kích thước canvas lúc vẽ là kích thước gốc của ảnh)
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;

      const clickX = (event.clientX - rect.left) * scaleX;
      const clickY = (event.clientY - rect.top) * scaleY;

      const paragraphsOnPage = this.parsedData.info_all_paragraphs.filter(
        p => p.page_index === pageIndex
      );

      // Tìm đoạn văn mà click vào (kiểm tra từ cuối mảng để ưu tiên các lớp trên cùng)
      let clickedParagraph = null;
      for (let i = paragraphsOnPage.length - 1; i >= 0; i--) {
        const p = paragraphsOnPage[i];
        if (p.bbox && p.bbox.length === 4) { // Sử dụng p.bbox
          const [x1, y1, x2, y2] = p.bbox; // Sử dụng p.bbox
          if (clickX >= x1 && clickX <= x2 && clickY >= y1 && clickY <= y2) {
            clickedParagraph = p;
            break;
          }
        }
      }

      if (clickedParagraph) {
        this.selectParagraph(clickedParagraph);
      } else {
        // Nếu click không trúng bbox nào, bỏ chọn đoạn văn
        this.clearSelectedParagraph();
      }
    },

    // Image handling - not needed for individual image loads anymore, managed by loadPageImages
    handleImageLoad() {
      // This handler is now part of the promise in loadPageImages
    },
    handleImageError() {
      // This handler is now part of the promise in loadPageImages
    },

    // Page navigation
    selectPage(index) {
      this.selectedPageIndex = index
      this.scrollToPageAndRedraw()
    },

    scrollToPageAndRedraw() {
      this.$nextTick(() => {
        // Đảm bảo ref tồn tại và là một mảng
        const pageWrapperElement = this.$refs.pdfViewer.querySelector(`.page-wrapper[data-v-show][style*="display: block"]`);
        if (pageWrapperElement) {
          pageWrapperElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        // Sau khi cuộn, vẽ lại nội dung trang được chọn
        this.drawPageContent(this.selectedPageIndex);
        // Cập nhật filterPage và áp dụng bộ lọc cho cột văn bản
        this.filterPage = this.selectedPageIndex; 
        this.applyFilters();
      });
    },
    
    prevPage() {
      if (this.selectedPageIndex > 0) {
        this.selectedPageIndex--;
        this.clearSelectedParagraph(); // Clear selection when changing page
        this.scrollToPageAndRedraw();
      }
    },

    nextPage() {
      if (this.selectedPageIndex < this.pageImages.length - 1) {
        this.selectedPageIndex++;
        this.clearSelectedParagraph(); // Clear selection when changing page
        this.scrollToPageAndRedraw();
      }
    },

    goToPage(pageIndex) {
      // Tìm index của ảnh trang dựa trên page_number (page_index + 1)
      const imageIndex = this.pageImages.findIndex(img => img.page_number === pageIndex + 1)
      if (imageIndex !== -1) {
        this.selectPage(imageIndex)
      }
    },

    // Paragraph handling
    selectParagraph(paragraph) {
      this.selectedParagraph = paragraph.index;
      this.selectedParagraphDetails = paragraph; // Lưu chi tiết đầy đủ
      this.goToPage(paragraph.page_index); // Chuyển đến trang của đoạn văn được chọn

      // Cuộn tới đoạn văn bản tương ứng trong panel bên phải nếu cần
      this.$nextTick(() => {
        const paragraphElement = this.$refs.textContent.querySelector(`.paragraph-item.selected`);
        if (paragraphElement) {
          paragraphElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      });
    },

    clearSelectedParagraph() {
      this.selectedParagraph = null;
      this.selectedParagraphDetails = null;
      // Vẽ lại trang hiện tại để bỏ highlight bbox
      this.drawPageContent(this.selectedPageIndex);
      // Áp dụng lại bộ lọc để hiển thị danh sách đoạn văn
      this.applyFilters(); 
    },

    toggleExpanded(paragraphIndex) {
      const index = this.expandedParagraphs.indexOf(paragraphIndex)
      if (index > -1) {
        this.expandedParagraphs.splice(index, 1)
      } else {
        this.expandedParagraphs.push(paragraphIndex)
      }
    },

    // Filtering and searching
    initializeFilters() {
      // Chỉ khởi tạo nếu parsedData.info_all_paragraphs tồn tại
      if (this.parsedData && this.parsedData.info_all_paragraphs) {
        this.filteredParagraphs = [...this.parsedData.info_all_paragraphs];
        // Đặt filterPage ban đầu theo trang hiện tại (nếu có ảnh)
        if (this.pageImages.length > 0) {
          this.filterPage = this.selectedPageIndex; 
        } else {
          this.filterPage = ''; // Nếu không có ảnh, mặc định hiển thị tất cả trang
        }
        this.applyFilters();
      } else {
        this.filteredParagraphs = [];
      }
    },

    applyFilters() {
      // Đảm bảo parsedData.info_all_paragraphs tồn tại
      if (!this.parsedData || !this.parsedData.info_all_paragraphs) {
        this.filteredParagraphs = [];
        return;
      }

      let filtered = [...this.parsedData.info_all_paragraphs]

      // Filter by type
      if (this.filterType) {
        filtered = filtered.filter(p => p.type === this.filterType)
      }

      // Filter by page
      // Lưu ý: filterPage có thể là chuỗi rỗng ('') hoặc một số (index trang 0-based)
      if (this.filterPage !== '') {
        filtered = filtered.filter(p => p.page_index === parseInt(this.filterPage))
      }

      // Search in text
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase().trim()
        filtered = filtered.filter(p => 
          p.full_text.toLowerCase().includes(query)
        )
      }

      this.filteredParagraphs = filtered
      this.sortParagraphs()
    },

    sortParagraphs() {
      this.filteredParagraphs.sort((a, b) => {
        // Sort by page first, then by reading order
        if (a.page_index !== b.page_index) {
          return a.page_index - b.page_index
        }
        return a.reading_order - b.reading_order
      })
    },

    // Utility methods
    getTypeIcon(type) {
      const icons = {
        title: 'fas fa-heading',
        text: 'fas fa-paragraph',
        table: 'fas fa-table',
        figure: 'fas fa-image',
        list: 'fas fa-list'
      }
      return icons[type] || 'fas fa-file-alt'
    },

    getTypeLabel(type) {
      const labels = {
        title: 'Tiêu đề',
        text: 'Văn bản',
        table: 'Bảng',
        figure: 'Hình ảnh',
        list: 'Danh sách'
      }
      return labels[type] || type
    },

    getColumnLabel(column) {
      const labels = {
        '1': 'Cột 1',
        '2': 'Cột 2',
        'full': 'Toàn trang'
      }
      return labels[column] || column
    },

    

    // Reset - Điều hướng về trang upload
    resetResult() {
      this.$router.push({ name: 'Upload' });
    },

    // Simple error display (for internal component errors, not main upload errors)
    showError(message) {
      this.internalError = message;
      console.error('Result Component Error:', message);
      setTimeout(() => { this.internalError = null; }, 5000);
    }
  },
  watch: {
    // Watch for changes in processedDataString and re-initialize if it changes
    processedDataString: {
      immediate: true, // Chạy lần đầu khi component mount
      async handler(newVal, oldVal) {
        if (newVal !== oldVal) {
          // Reset trạng thái
          this.pageImages = [];
          this.isLoadingImages = true;
          this.selectedPageIndex = 0;
          this.selectedParagraph = null;
          this.selectedParagraphDetails = null; // Reset chi tiết đoạn văn
          this.expandedParagraphs = [];
          this.filterType = '';
          this.filterPage = ''; // Reset filterPage
          this.searchQuery = '';
          this.filteredParagraphs = [];
          this.internalError = null;

          if (this.parsedData && this.parsedData.file_id) {
            await this.loadPageImages(); // Đợi ảnh tải xong
            // Sau khi ảnh tải xong, khởi tạo filter và vẽ lại trang
            this.initializeFilters();
            this.$nextTick(() => {
              if (this.pageImages.length > 0) {
                this.drawPageContent(this.selectedPageIndex);
              }
            });
          } else {
            this.isLoadingImages = false;
            if (!this.processedDataString || this.processedDataString === '{}') {
                console.warn('Result component received empty or default processedDataString.');
            } else {
                this.showError('Không thể tải ảnh trang: Không tìm thấy file_id trong dữ liệu.');
            }
            this.initializeFilters(); // Vẫn khởi tạo filters dù không có ảnh
          }
        }
      }
    },
    // Watch selectedPageIndex to redraw canvas when page changes via selection
    selectedPageIndex: {
      handler(newIndex, oldIndex) {
        if (newIndex !== oldIndex && this.pageImages.length > 0) {
          this.$nextTick(() => {
            this.drawPageContent(newIndex);
            // Cập nhật filterPage và áp dụng bộ lọc cho cột văn bản
            this.filterPage = newIndex; 
            this.applyFilters();
          });
        }
      }
    },
    // Watch selectedParagraph to redraw canvas when selection changes from text panel
    selectedParagraph: {
      handler(newVal, oldVal) {
        if (newVal !== oldVal && this.pageImages.length > 0) {
          this.$nextTick(() => {
             this.drawPageContent(this.selectedPageIndex); // Vẽ lại trang hiện tại
          });
        }
      }
    }
  }
}
</script>

<style scoped>
/* Biến CSS chung */
:root {
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --bg-light: #f8f9fa;
  --bg-dark: #343a40;
  --text-dark: #2c3e50;
  --text-light: #f4f7f6;
  --border-color: #e0e0e0;
  --shadow-light: 0 6px 20px rgba(0, 0, 0, 0.1);
  --shadow-medium: 0 4px 12px rgba(0, 123, 255, 0.4);
  --shadow-heavy: 0 6px 16px rgba(0, 123, 255, 0.5);
  --radius-sm: 8px;
  --radius-md: 12px;
  --font-body: 'Inter', sans-serif;
  --font-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;
}

/* Base styles */
.result-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
  max-width: 1200px;
  margin: 40px auto;
  padding: 30px;
  background-color: #ffffff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-light);
  animation: fadeIn 0.6s ease-out;
  border: 1px solid var(--border-color);
  font-family: var(--font-body);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.result-title {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-title h2 {
  color: var(--text-dark);
  font-size: 2em;
  font-weight: 600;
  letter-spacing: -0.5px;
  margin: 0;
  display: flex;
  align-items: center;
}

.result-title h2 i {
  margin-right: 15px;
  color: var(--primary-color);
  font-size: 1.2em;
}

.result-stats {
  display: flex;
  gap: 20px;
  color: #555;
  font-size: 0.95em;
  font-weight: 500;
}

.stat-item {
  display: flex;
  align-items: center;
}

.stat-item i {
  margin-right: 8px;
  color: var(--primary-color);
}

.result-actions {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.action-btn {
  background-color: darkblue;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}
.action-btn.reset {
  background-image: linear-gradient(to right, var(--primary-color), #0056b3);
  color: white;
  box-shadow: 0 4px 10px rgba(0, 123, 255, 0.3);
}

.action-btn.reset:hover {
  background-image: linear-gradient(to right, #0056b3, #003d80);
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(0, 123, 255, 0.4);
}
.action-search-btn {
  background-color: darkblue;
  padding: 10px 10px;
  border: none;
  border-radius: 5px;
  font-size: 0.95em;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}
.action-search-btn.reset {
  background-image: linear-gradient(to right, var(--primary-color), #0056b3);
  color: white;
  box-shadow: 0 4px 10px rgba(0, 123, 255, 0.3);
}

.action-search-btn.reset:hover {
  background-image: linear-gradient(to right, #0056b3, #003d80);
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(0, 123, 255, 0.4);
}




.action-btn.back-to-list {
  background-color: #f0f2f5;
  color: var(--text-dark);
  box-shadow: none;
  border: 1px solid var(--border-color);
}
.action-btn.back-to-list:hover {
  background-color: #e0e2e5;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}


/* Main Content Layout */
.result-content {
  display: flex;
  gap: 30px;
  flex-wrap: wrap; /* Cho phép wrap trên màn hình nhỏ */
}

.pdf-panel, .text-panel {
  width: 50%;
  background-color: var(--bg-light);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden; /* Quan trọng cho thanh cuộn nội dung */
}

.panel-header {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #f0f2f5;
  border-bottom: 1px solid var(--border-color);
  border-top-left-radius: var(--radius-md);
  border-top-right-radius: var(--radius-md);
  flex-wrap: wrap;
  gap: 10px;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.2em;
  color: var(--text-dark);
  display: flex;
  align-items: center;
}

.panel-header h3 i {
  margin-right: 10px;
  color: var(--primary-color);
}

/* PDF Viewer Specific */
.pdf-viewer {
  flex-grow: 1;
  overflow-y: auto; /* Giữ overflow-y để cuộn nếu nội dung dài */
  padding: 15px;
  background-color: #fcfcfc;
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
  min-height: 400px; /* Đảm bảo có chiều cao tối thiểu */
}

.loading-state, .error-state {
  text-align: center;
  padding: 50px;
  color: #777;
  font-size: 1.1em;
}

.loading-state i, .error-state i {
  font-size: 2.5em;
  color: var(--primary-color);
  margin-bottom: 15px;
}

.error-state i {
  color: #dc3545;
}

.pdf-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.page-nav-btn {
  background-color: darkblue;
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}
.page-nav-btn:hover:not(:disabled) {
  background-color: #0056b3;
  transform: translateY(-1px);
}
.page-nav-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.page-selector {
  width: 120px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: white;
  cursor: pointer;
  font-size: 0.9em;
  color: var(--text-dark);
  appearance: none; /* Loại bỏ style mặc định của select */
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 18px;
}

.pages-container {
  width: 100%;
  display: flex;
  flex-direction: column; /* Quan trọng để hiển thị từng trang riêng lẻ */
  align-items: center;
  gap: 20px;
}

.page-wrapper {
  background-color: #fff;
  border: 2px solid transparent;
  border-radius: var(--radius-sm);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  padding: 10px;
  text-align: center;
  width: 100%; /* Chiếm toàn bộ chiều rộng có sẵn */
  box-sizing: border-box;
  display: flex; /* Sử dụng flex để căn giữa canvas và số trang */
  flex-direction: column;
  align-items: center;
}

.page-wrapper.active-page {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.3);
}

.page-number {
  font-size: 0.85em;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.page-canvas {
  max-width: 100%;
  height: auto;
  display: block;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: crosshair; /* Thay đổi con trỏ chuột khi di chuyển trên canvas */
}

/* Text Analysis Specific */
.text-panel {
  flex: 1.5; /* Có thể rộng hơn panel PDF */
}

.text-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.filter-group, .search-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-select {
  width: 120px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: white;
  cursor: pointer;
  font-size: 0.9em;
  color: var(--text-dark);
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 18px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: 0.9em;
  width: 180px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.search-icon {
  color: white;
}

.text-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #fcfcfc;
  /* max-height: calc(100vh - 300px); Tùy chỉnh chiều cao để có thanh cuộn */
  /* min-height: 300px; */
}

.empty-state {
  text-align: center;
  padding: 50px;
  color: #777;
  font-size: 1.1em;
}

.empty-state i {
  font-size: 2.5em;
  color: #ccc;
  margin-bottom: 15px;
}

.paragraphs-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.paragraph-item {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  border-left: 5px solid transparent; /* Để chỉ thị loại */
  border-radius: var(--radius-sm);
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
  cursor: pointer;
}

.paragraph-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.paragraph-item.selected {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.2);
}

/* Loại border-left-color tùy theo loại đoạn văn */
.paragraph-item.type-title { border-left-color: #f0ad4e; }
.paragraph-item.type-text { border-left-color: #5bc0de; }
.paragraph-item.type-table { border-left-color: #5cb85c; }
.paragraph-item.type-figure { border-left-color: #f45a5a; }
.paragraph-item.type-list { border-left-color: #a270da; }


.paragraph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px dotted #eee;
  flex-wrap: wrap;
  gap: 10px;
}

.paragraph-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 0.85em;
  color: #777;
  font-weight: 500;
}

.paragraph-type {
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.8em;
  text-transform: uppercase;
  color: black;
}

/* Màu sắc cho badge loại đoạn văn */
.paragraph-type.type-title { background-color: #f0ad4e; }
.paragraph-type.type-text { background-color: #5bc0de; }
.paragraph-type.type-table { background-color: #5cb85c; }
.paragraph-type.type-figure { background-color: #f45a5a; }
.paragraph-type.type-list { background-color: #a270da; }

.paragraph-meta i {
  margin-right: 5px;
}

.goto-page-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 1.1em;
  transition: color 0.2s ease;
}

.goto-page-btn:hover {
  color: #0056b3;
}

.paragraph-content {
  font-size: 0.95em;
  line-height: 1.6;
  color: #333;
}

.paragraph-text {
  max-height: 100px; /* Chiều cao mặc định khi chưa mở rộng */
  overflow: hidden;
  text-overflow: ellipsis; /* Hiển thị dấu ba chấm nếu tràn */
  transition: max-height 0.3s ease-out;
}

.paragraph-text.expanded {
  max-height: none; /* Mở rộng hoàn toàn */
}

.expand-btn {
  background: none;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 600;
  margin-top: 5px;
  padding: 5px 0;
  display: block;
  text-align: right;
  transition: color 0.2s ease;
}

.expand-btn:hover {
  color: #0056b3;
  text-decoration: underline;
}

/* Selected Paragraph Details */
.selected-paragraph-details {
  padding: 15px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background-color: #f0f8ff; /* Màu nền nhẹ nhàng cho chi tiết */
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.selected-paragraph-details h4 {
  color: var(--primary-color);
  font-size: 1.3em;
  margin-top: 0;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px dashed #cceeff;
}

.detail-item {
  margin-bottom: 8px;
  font-size: 0.95em;
  line-height: 1.5;
}

.detail-item strong {
  color: var(--text-dark);
  margin-right: 5px;
}

.paragraph-type-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 0.8em;
  text-transform: uppercase;
  color: black;
}

.full-text-detail .full-text-content {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: var(--radius-sm);
  padding: 12px;
  margin-top: 5px;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-body);
  max-height: 250px;
  overflow-y: auto;
}
.bbox-detail {
  font-family: var(--font-mono);
  font-size: 0.85em;
  background-color: #fafafa;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #eee;
}


/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease-out;
}

.modal-content {
  background-color: #fff;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-light);
  padding: 25px;
  width: 90%;
  max-width: 500px;
  animation: slideIn 0.3s ease-out;
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 15px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  color: var(--text-dark);
  font-size: 1.5em;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5em;
  color: #888;
  cursor: pointer;
  transition: color 0.2s ease;
}

.close-btn:hover {
  color: #333;
}

/* Error message styling */
.error-message {
  background-color: #fdd;
  color: #d8000c;
  padding: 10px 15px;
  border: 1px solid #d8000c;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.95em;
}

.error-message i {
  color: #d8000c;
  font-size: 1.2em;
}

.error-message .close-error {
  background: none;
  border: none;
  color: #d8000c;
  font-size: 1.1em;
  cursor: pointer;
  margin-left: auto;
}
.error-message .close-error:hover {
  color: #a00000;
}


/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    transform: translateY(-50px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .result-container {
    padding: 20px;
    margin: 20px auto;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-stats {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .result-actions {
    width: 100%;
    justify-content: center;
  }

  .action-btn {
    flex: 1 1 auto;
    justify-content: center;
  }

  .result-content {
    flex-direction: column;
    gap: 20px;
  }

  .pdf-panel, .text-panel {
    min-width: unset;
    width: 100%;
  }

  .panel-header {

    align-items: flex-start;
    flex-direction: column;
  }

  .text-controls {
    flex-direction: column;
    width: 100%;
    gap: 10px;
  }

  .filter-group, .search-group {
    width: 100%;
    justify-content: space-between;
  }

  .filter-select, .search-input {
    width: calc(100% - 30px); /* Adjusted for padding */
  }

}
</style>
