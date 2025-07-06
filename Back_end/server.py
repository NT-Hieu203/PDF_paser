import json
from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import os
import time
import shutil
from Processing_function import process_full_pdf
from doclayout_yolo import YOLOv10
import easyocr
from LayoutLMv3Classifier import LayoutLMv3Classifier
# ********ĐỊNH NGHĨA CÁC ĐƯỜNG DẪN********
MODEL_PATH = "model/model_doclayout/doclayout_yolo_docstructbench_imgsz1024.pt"
model = YOLOv10(MODEL_PATH)
reader = easyocr.Reader(['vi', 'en'], gpu=False)
classifier = LayoutLMv3Classifier()

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
IMAGES_FOLDER = os.path.join(os.getcwd(), 'page_images')  # Thư mục lưu ảnh các trang
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)

# *****************
app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGES_FOLDER'] = IMAGES_FOLDER

# Dictionary lưu thông tin các file đã xử lý (trong thực tế nên dùng database)
processed_files = {}

# Route trả file PDF về cho trình duyệt
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route trả ảnh trang PDF về cho trình duyệt
@app.route('/page_images/<file_id>/<page_name>')
def get_page_image(file_id, page_name):
    file_folder = os.path.join(app.config['IMAGES_FOLDER'], file_id)
    if not os.path.exists(file_folder):
        return jsonify({"error": "Không tìm thấy thư mục ảnh của file"}), 404
    
    image_path = os.path.join(file_folder, page_name)
    if not os.path.exists(image_path):
        return jsonify({"error": "Không tìm thấy ảnh trang"}), 404
    
    return send_from_directory(file_folder, page_name)

# Route lấy danh sách ảnh của một file
@app.route('/api/get_page_images/<file_id>')
def get_file_page_images(file_id):
    if file_id not in processed_files:
        return jsonify({"error": "File không tồn tại hoặc chưa được xử lý"}), 404
    
    file_info = processed_files[file_id]
    page_images = []
    
    # THAY ĐỔI DÒNG NÀY: range từ 0 đến total_pages - 1
    for i in range(0, file_info['total_pages']): 
        page_name = f"page_{i}.png" # <-- Sử dụng i (page_index) trực tiếp
        image_url = url_for('get_page_image', file_id=file_id, page_name=page_name, _external=True)
        page_images.append({
            "page_number": i + 1, # Vẫn hiển thị page_number từ 1 cho người dùng
            "image_url": image_url,
            "page_name": page_name
        })
    
    return jsonify({
        "file_id": file_id,
        "total_pages": file_info['total_pages'],
        "page_images": page_images
    }), 200

@app.route(f'/api/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdfFile' not in request.files:
        return jsonify({"error": "Không có phần file 'pdfFile' trong yêu cầu"}), 400

    file = request.files['pdfFile']

    if file.filename == '':
        return jsonify({"error": "Không có file được chọn"}), 400

    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Tạo ID duy nhất cho file này
        file_id = str(uuid.uuid4())
        folder_path = os.path.join(app.config['IMAGES_FOLDER'], file_id)
        os.makedirs(folder_path, exist_ok=True)
        try:
            # Xử lý PDF để lấy data
            print("Đang xử lý nội dung PDF...")
            data = process_full_pdf(model, classifier, reader, file_path, folder_path)
            print("Xử lý PDF hoàn tất")

            # Lưu thông tin file đã xử lý
            processed_files[file_id] = {
                'filename': unique_filename,
                'original_name': filename,
                'total_pages': data['total_pages'],
                'total_paragraphs': data['total_paragraphs'],
                'upload_time': time.time()
            }

            pdf_url = url_for('uploaded_file', filename=unique_filename, _external=True)
            page_images_url = url_for('get_file_page_images', file_id=file_id, _external=True)

            return jsonify({
                "message": "File PDF đã được xử lý thành công.",
                "file_id": file_id,  # ID để lấy ảnh các trang
                "pdf_url": pdf_url,  # URL để hiển thị PDF
                "page_images_url": page_images_url,  # URL để lấy danh sách ảnh các trang
                "total_pages": data['total_pages'],
                "total_paragraphs": data['total_paragraphs'],
                "info_all_paragraphs": data['all_paragraphs']
            }), 200
        except Exception as e:
            print(f"Lỗi khi xử lý PDF: {e}")
            # Xóa file PDF lỗi
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Đã xóa file PDF lỗi: {file_path}")
            
            # Xóa thư mục ảnh nếu có
            file_images_folder = os.path.join(app.config['IMAGES_FOLDER'], file_id)
            if os.path.exists(file_images_folder):
                shutil.rmtree(file_images_folder)
                print(f"Đã xóa thư mục ảnh lỗi: {file_images_folder}")
            
            return jsonify({"error": f"Lỗi khi xử lý PDF: {str(e)}"}), 500
    else:
        return jsonify({"error": "Chỉ chấp nhận file PDF"}), 400


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)