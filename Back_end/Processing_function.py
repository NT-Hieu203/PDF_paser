import fitz
from PIL import Image
import numpy as np
import time
import os

def pdf_to_images(documents, output_folder):
    """
    Chuyển đổi từng trang của file PDF sang định dạng PIL Image.
    Args:
        documents (fitz.Document): Đối tượng PDF.
    Returns:
        list: Một list các dictionary, mỗi dict chứa 'image' (PIL Image)
              và 'page_number' của trang tương ứng.
    """

    doc_images = []

    for page_index, page in enumerate(documents):
        image_name = f"page_{page_index}.png"
        image_path = os.path.join(output_folder, image_name)

        try:
            pix = page.get_pixmap(dpi=300)
            if not pix:
                print(f"Error: Could not get pixmap for page {page_index}")
                continue

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            if not img:
                print(f"Error: Could not create PIL Image for page {page_index}")
                continue

            img.save(image_path, "PNG")
            print(f"Saved: {image_path}") # Debugging
            doc_images.append({
                "image": img,
                "page_index": page_index,
                "page": page
            })
        except Exception as e:
            print(f"Error processing page {page_index}: {e}")

    return doc_images, len(doc_images)
def detect_layout(model_detect_layout, pil_image_obj):
    """
    Phát hiện bố cục trên một PIL Image bằng model YOLOv10.
    Args:
        model_detect_layout: Model Doclayout-yolo
        pil_image_obj (PIL.Image.Image): Đối tượng PIL Image của trang.
    Returns:
        ultralytics.engine.results.Results: Đối tượng kết quả từ YOLOv10 predict.
    """

    results = model_detect_layout.predict(
                  pil_image_obj,   # Image to predict
                  imgsz=1024,        # Prediction image size
                  conf=0.3,          # Confidence threshold
                  device="cpu"    # Device to use (e.g., 'cuda:0' or 'cpu')
              )
    return results[0]


def recognize_text_from_image(reader, img_array_or_pil_image):
    """
    Thực hiện OCR trên một hình ảnh (NumPy array hoặc PIL Image) bằng EasyOCR.
    Args:
        reader: easyocr.readers.ImageReader
        img_array_or_pil_image: Hình ảnh dưới dạng NumPy array (OpenCV format) hoặc PIL Image.
    Returns:
        list: Một list các tuple (bbox, text, confidence) từ EasyOCR.
    """
    results = reader.readtext(img_array_or_pil_image, detail=0)
    return results
# def recognize_text_from_pymupdf_page(docs, page_index, bbox):
#     """
#     Trích xuất văn bản từ một trang PyMuPDF trong một vùng (bounding box) nhất định.

#     Args:
#         docs (fitz.Document): Đối tượng PDF.
#         page_index (int): Index của trang trong PDF.
#         bbox (list hoặc tuple): Bounding box dưới dạng [x1, y1, x2, y2], đây là tọa độ hình ảnh

#     Returns:
#         str: Văn bản được trích xuất từ vùng đã cho. Trả về chuỗi rỗng nếu không tìm thấy text.
#     """
#     try:

#         # chuyển sang tọa độ hình ảnh sang tọa độ PDF
#         # 300 DPI = 300/72 = 4.167 pixels per point

#         scale = 300/72
#         # Tạo một fitz.Rect từ bounding box
#         x1, y1, x2, y2 = [coord / scale for coord in bbox]

#         # Tạo clip rect và trích xuất text
#         clip_rect = fitz.Rect(x1, y1, x2, y2)
#         pymupdf_page = docs[page_index]
#         block = pymupdf_page.get_text('blocks',clip= clip_rect)

#         text = block[0][4]
#         text = text.replace('.\n','.#')
#         text = text.replace('\n',' ')

#         return  text

#     except Exception as e:
#         print('Không có text trong vùng đã cho')
#         return "" # Trả về chuỗi rỗng nếu có lỗi

def recognize_text_from_pymupdf_page(docs, page_index, bbox):
    """
    Trích xuất văn bản và bounding box của từng từ từ một trang PyMuPDF
    trong một vùng (bounding box) nhất định.

    Args:
        docs (fitz.Document): Đối tượng PDF.
        page_index (int): Index của trang trong PDF.
        bbox (list hoặc tuple): Bounding box dưới dạng [x1, y1, x2, y2],
                                là tọa độ hình ảnh (ví dụ: từ ảnh scan).

    Returns:
        list: Một danh sách các dictionary, mỗi dictionary chứa
              'text' (nội dung của từ) và 'bbox' (bounding box của từ)
              trong tọa độ hình ảnh. Trả về danh sách rỗng nếu không tìm thấy text.
    """
    try:
        # Chuyển đổi tọa độ hình ảnh sang tọa độ PDF
        # Giả định 300 DPI và 72 DPI là mặc định của PDF
        scale = 300 / 72
        x1_img, y1_img, x2_img, y2_img = bbox

        # Chuyển đổi tọa độ bbox đầu vào từ ảnh (DPI=300) sang PDF (DPI=72)
        x1_pdf = x1_img / scale
        y1_pdf = y1_img / scale
        x2_pdf = x2_img / scale
        y2_pdf = y2_img / scale

        # Tạo một fitz.Rect từ bounding box đã chuyển đổi
        clip_rect_pdf = fitz.Rect(x1_pdf, y1_pdf, x2_pdf, y2_pdf)
        pymupdf_page = docs[page_index]

        block = pymupdf_page.get_text('blocks',clip= clip_rect_pdf)

        text = block[0][4]
        text = text.replace('.\n','.')
        text = text.replace('\n',' ')
        # Trích xuất từng từ với bounding box của chúng
        # 'words' trả về một danh sách các tuple: (x0, y0, x1, y1, word, block_no, line_no, word_no)
        words_data = pymupdf_page.get_text('words', clip=clip_rect_pdf)

        bbox_words_of_text = []
        for word_info in words_data:
            # Lấy thông tin từ tuple
            x0_word_pdf, y0_word_pdf, x1_word_pdf, y1_word_pdf, word_text = word_info[:5] # Chỉ lấy 5 phần tử đầu

            # Chuyển đổi bounding box của từng từ trở lại tọa độ hình ảnh
            x0_word_img = int(x0_word_pdf * scale)
            y0_word_img = int(y0_word_pdf * scale)
            x1_word_img = int(x1_word_pdf * scale)
            y1_word_img = int(y1_word_pdf * scale)

            word_bbox_img = [x0_word_img, y0_word_img, x1_word_img, y1_word_img]

            bbox_words_of_text.append(word_bbox_img)

        return text, bbox_words_of_text

    except Exception as e:
        print(f'Lỗi khi trích xuất text hoặc không có text trong vùng đã cho: {e}')
        return [] # Trả về danh sách rỗng nếu có lỗi

def sort_boxes_2column_simpler(pil_image, is_first_page, boxes):
    """
    Sắp xếp boxes theo thứ tự đọc 2 cột:
    - Boxes toàn chiều ngang (như tiêu đề): được ưu tiên theo vị trí Y
    - Cột 1: tất cả boxes từ trên xuống
    - Cột 2: tất cả boxes từ trên xuống
    """
    if not boxes:
        return []

    page_width = pil_image.width
    if is_first_page:
        column_divider = page_width / 3
    else:
        column_divider = page_width / 2

    # Phân loại boxes
    full_width_boxes = []
    column1_boxes = []
    column2_boxes = []

    for box in boxes:
        x1, y1, x2, y2 = box['bbox']
        if x1 < column_divider:
            column1_boxes.append(box)
            box['column'] = 1
        else:
            column2_boxes.append(box)
            box['column'] = 2

    # Sắp xếp từng nhóm theo Y (từ trên xuống)
    full_width_boxes.sort(key=lambda x: x['bbox'][1])  # Sắp xếp theo y1
    column1_boxes.sort(key=lambda x: x['bbox'][1])  # Sắp xếp theo y1
    column2_boxes.sort(key=lambda x: x['bbox'][1])  # Sắp xếp theo y1

    result = []

    # Thêm tất cả full-width boxes
    result.extend(full_width_boxes)
    # Thêm tất cả column 1 boxes
    result.extend(column1_boxes)
    # Thêm tất cả column 2 boxes
    result.extend(column2_boxes)

    return result

def process_pdf_page(docs, model_detect_layout,classifier, reader, pdf_page_data, parent_info, continue_index, parent_index):
    """
    Xử lý một trang PDF: phát hiện bố cục và nhận dạng văn bản theo thứ tự đọc 2 cột.
    Args:
        model_detect_layout: model Doclayout_yolo
        pdf_page_data (dict): Dictionary chứa 'image' (PIL Image) và 'page_index'.
        continue_index (int): Index tiếp tục từ lần xử lý trước
    Returns:
        tuple: (continue_index, processed_paragraphs, page_results)
    """
    page_index = pdf_page_data["page_index"]
    pil_image = pdf_page_data["image"]

    print(f"\n--- Xử lý trang: {page_index} ---")

    # 1. Phát hiện bố cục
    layout_results = detect_layout(model_detect_layout, pil_image)
    processed_paragraphs = []

    # Kiểm tra xem có boxes không
    if not (hasattr(layout_results, 'boxes') and layout_results.boxes):
        print("    Không tìm thấy đối tượng bố cục nào.")
        return continue_index, processed_paragraphs

    # 2. Lọc và chuẩn bị boxes
    valid_boxes = []
    for box in layout_results.boxes:
        bbox = box.xyxy[0].tolist()
        x1, y1, x2, y2 = map(int, bbox)
        label = model_detect_layout.names[int(box.cls[0])]
        score = box.conf[0].item()

        # Chỉ xử lý box không phải abandon và có confidence >= threshold
        if label != 'abandon' and score >= 0.4:
            valid_boxes.append({
                'box': box,
                'bbox': (x1, y1, x2, y2),
                'label': label,
                'score': score
            })

    if not valid_boxes:
        print("    Không có box hợp lệ nào.")
        return continue_index, processed_paragraphs

    # 3. Sắp xếp boxes theo thứ tự đọc 2 cột
    if page_index == 0:
        is_first_page = True
    else:
        is_first_page = False
    s_time = time.time()
    sorted_boxes = sort_boxes_2column_simpler(pil_image,is_first_page, valid_boxes)
    e_time = time.time()
    print(f"    ⏱️  Thời gian sắp xếp boxes: {e_time - s_time:.2f} giây")
    print(f"    📋 Tìm thấy {len(sorted_boxes)} boxes hợp lệ, đã sắp xếp theo thứ tự đọc 2 cột")

    # 4. Xử lý từng box theo thứ tự đã sắp xếp
    for i, box_info in enumerate(sorted_boxes):
        bbox = box_info['bbox']
        x1, y1, x2, y2 = bbox
        label = box_info['label']
        score = box_info['score']
        if label == 'abandon' or label == 'figure' or label == 'table':
            continue


        print(f"    📦 Box {i+1}/{len(sorted_boxes)}: {label} (confidence: {score:.2f})")
        print(f"        📍 Vị trí: ({x1}, {y1}) -> ({x2}, {y2})")

        try:
            # Cắt ảnh theo bbox
            image_cut = pil_image.crop((x1, y1, x2, y2))
            img_np = np.array(image_cut)

            # 5. Nhận dạng văn bản
            start_time = time.time()
            recognized_text_results, bbox_of_text = recognize_text_from_pymupdf_page(docs, page_index, bbox)
            recognized_text_results = recognized_text_results.strip()
            end_time = time.time()
            print(f"      ⏱️  Thời gian trích text: {end_time - start_time:.2f} giây")

            if recognized_text_results == "":
                recognized_text_results = recognize_text_from_image(reader, img_np)
                recognized_text_results = ' '.join(recognized_text_results)

            print(f"      ✅ Nhận dạng được: {recognized_text_results[:100]}..." if len(recognized_text_results) > 100 else f"      ✅ Nhận dạng được: {recognized_text_results}")

            # 6. Tạo thông tin paragraph
            if recognized_text_results:

                if label == 'title':
                    sample_words = recognized_text_results.split(' ')
                    result = classifier.predict_single(
                        pil_image,
                        sample_words,
                        bbox_of_text,
                        return_probabilities=True
                    )
                    parent_info[f'Level {result["predicted_class"]}'] = continue_index
                    parent_info['parent plain text'] = continue_index
                    if result["predicted_class"] > 0:
                        parent_index = parent_info[f'Level {result["predicted_class"] - 1}']
                        print(result["predicted_class"],'========================', page_index)
                    else:
                        parent_index = -1
                        print(result["predicted_class"],'========================', page_index)
                else:
                    parent_index = parent_info['parent plain text']
                paragraph_info = {
                    'type': label,
                    'bbox': [x1, y1, x2, y2],
                    'full_text': recognized_text_results,
                    'page_index': page_index,
                    'parent_index': parent_index,
                    'index': continue_index,
                    'is_title': label == 'title',
                    'reading_order': i + 1,  # Thêm thứ tự đọc
                    'column': box_info.get('column', 'unknown') # Thông tin cột (1, 2, hoặc 'full')
                    }

                continue_index += 1
                processed_paragraphs.append(paragraph_info)
                print(f"      ✅ Đã lưu paragraph (thứ tự: {i+1}, cột: {paragraph_info['column']}")

            else:
                print(f"      ⚠ Không nhận dạng được text")
                continue_index -= 1  # Rollback index nếu không nhận dạng được

        except Exception as e:
            print(f"      ❌ Lỗi khi xử lý box: {str(e)}")
            continue_index -= 1  # Rollback index nếu có lỗi

    print(f"\n  >>> Hoàn thành xử lý trang {page_index}: {len(processed_paragraphs)} paragraphs (theo thứ tự đọc 2 cột)")
    return continue_index, parent_index, processed_paragraphs

def process_full_pdf(model_detect_layout, classifier, reader, pdf_path, folder_output_path):
    """
    Xử lý toàn bộ file PDF: chuyển đổi, phát hiện bố cục và nhận dạng văn bản từng trang.
    Args:
        pdf_path (str): Đường dẫn đến file PDF.
    Returns:
        dict: Dictionary chứa tất cả kết quả xử lý và thống kê
    """
    print(f"\n🚀 Bắt đầu xử lý PDF: {pdf_path}")
    documents = fitz.open(pdf_path)
    # Chuyển đổi PDF thành ảnh
    start_time = time.time()
    all_page_images, total_pages = pdf_to_images(documents, folder_output_path)
    end_time = time.time()
    parent_info = {
            "Level 0" : -1,
            "Level 1" : -1,
            "Level 2" : -1,
            "Level 3" : -1,
            "parent plain text" : -1
        }
    print(f"📄 Tổng số trang: {total_pages}")
    print(f"⏱️  Thời gian chuyển đổi: {end_time - start_time:.2f} giây")
    # Khởi tạo kết quả

    all_paragraphs = []
    continue_index = 0
    parent_index = -1
    # Xử lý từng trang
    for i, page_data in enumerate(all_page_images, 1):
        print(f"\n📖 Đang xử lý trang {i}/{total_pages}...")

        try:
            # Xử lý trang và nhận kết quả
            start_time = time.time()
            continue_index, parent_index, page_paragraphs = process_pdf_page(documents, model_detect_layout, classifier, reader, page_data,parent_info, continue_index, parent_index)
            end_time = time.time()
            print(f"⏱️  Thời gian detect và trích text trang {i}: {end_time - start_time:.2f} giây")
            # Thêm paragraphs vào danh sách tổng
            all_paragraphs.extend(page_paragraphs)

            print(f"✅ Hoàn thành trang {i}: {len(page_paragraphs)} paragraphs")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý trang {i}: {str(e)}")


    # Tạo thống kê tổng quan
    total_paragraphs = len(all_paragraphs)
    return {
        "pdf_path": pdf_path,
        "total_pages": total_pages,
        "total_paragraphs": total_paragraphs,
        "all_paragraphs": all_paragraphs,
    }
