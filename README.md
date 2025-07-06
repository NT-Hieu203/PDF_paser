# PDF Parser

## Các bước xử lý chính:

- **Chuyển đổi PDF sang ảnh:** Chuyển đổi mỗi trang của tài liệu PDF thành định dạng ảnh PIL Image.  
- **Phát hiện bố cục:** Sử dụng mô hình YOLOv10 để phát hiện các thành phần bố cục (ví dụ: đoạn văn, tiêu đề, bảng biểu, hình ảnh) trên mỗi trang.  
- **Nhận dạng văn bản (OCR):** Trích xuất văn bản từ các vùng được phát hiện bằng cách sử dụng PyMuPDF cho văn bản gốc và EasyOCR cho các trường hợp cần OCR trên ảnh.
- **Sắp xếp bố cục hai cột:** Đặc biệt xử lý các tài liệu có bố cục hai cột, đảm bảo thứ tự đọc chính xác của văn bản.
- **Cấu trúc dữ liệu đầu ra:** Kết quả được trả về dưới dạng một cấu trúc rõ ràng, bao gồm nội dung văn bản, loại bố cục, vị trí và thông tin trang.

## Hướng dẫn cài đặt Backend Flask:
### Cấu trúc thư mục:
```bash
Back_end/
├── page_images/
├── uploads/
├── models/
│   ├── best_Layout_LMv3/
│   └── model_doclayout/
├── LayoutLMv3Classifier.py
├── Processing_function.py
├── requirements.txt
└── server.py
```
### Khuyến khích tạo môi trường ảo với conda:
```bash
conda create -n flask_env python=3.12
#kích hoạt môi trường ảo
conda activate flask_env
```

### Cài các Dependencies:
```bash
pip install -r requirements.txt
```
### Tải các model cần thiết:
#### DocLayout-YOLO:
- Tải file doclayout_yolo_docstructbench_imgsz1024.pt thủ công từ [juliozhao/DocLayout-YOLO-DocStructBench](https://huggingface.co/juliozhao/DocLayout-YOLO-DocStructBench)
- Tải xuống với hf_hub_download:
```bash
filepath = hf_hub_download(repo_id="juliozhao/DocLayout-YOLO-DocStructBench", filename="doclayout_yolo_docstructbench_imgsz1024.pt")
```
#### Model LayoutLM-v3:
- Tải best model ở output Notebook Kaggle: [Best Model](https://www.kaggle.com/code/nguyenthanhhieu1006/trainlayoutlm)

### Chuyển vào thư mục Back_end và chạy dự án:
```bash
cd Back_end
python server.py
```

   
## Hướng dẫn cài đặt Frontend Vue.js:
### Di chuyển vào thư mục Front_end:
```bash:
cd Front_end
```
### Tải các Dependencies:
```bash
npm install
```
### Chạy dự án:
```bash
npm run dev
```
