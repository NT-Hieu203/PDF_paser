import os
from PIL import Image
import torch
from transformers import LayoutLMv3Processor, LayoutLMv3ForSequenceClassification
import warnings
warnings.filterwarnings("ignore")

class LayoutLMv3Classifier:
    def __init__(self, model_path="model/best_Layout_LMv3"):
        """
        Khởi tạo classifier với model đã train

        Args:
            model_path (str): Đường dẫn đến folder chứa model đã train
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")

        # Load processor và model
        try:
            self.processor = LayoutLMv3Processor.from_pretrained(model_path, apply_ocr=False)
            self.model = LayoutLMv3ForSequenceClassification.from_pretrained(model_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"Model loaded successfully from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to base model
            print("Loading base model instead...")
            self.processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base", apply_ocr=False)
            self.model = LayoutLMv3ForSequenceClassification.from_pretrained("microsoft/layoutlmv3-base", num_labels=4)
            self.model.to(self.device)
            self.model.eval()

        # Định nghĩa mapping labels
        self.id_to_label = {
            0: "Level 0",
            1: "Level 1",
            2: "Level 2",
            3: "Level 3"
        }

        # Constants từ training
        self.LAYOUTLM_IMAGE_SIZE = 224
        self.MAX_SEQ_LENGTH = 512

    def normalize_box(self, box, width, height):
        """Normalize bounding box coordinates to 0-1000 scale"""
        return [
            int(1000 * (box[0] / width)),
            int(1000 * (box[1] / height)),
            int(1000 * (box[2] / width)),
            int(1000 * (box[3] / height))
        ]

    def resize_image_and_boxes(self, image, boxes, target_size=None):
        """Resize image and adjust bounding boxes"""
        if target_size is None:
            target_size = self.LAYOUTLM_IMAGE_SIZE

        original_width, original_height = image.size

        # Resize image
        resized_image = image.resize((target_size, target_size), Image.Resampling.LANCZOS)

        # Calculate scaling factors
        width_scale = target_size / original_width
        height_scale = target_size / original_height

        # Adjust boxes
        adjusted_boxes = []
        for box in boxes:
            if len(box) == 4:
                adjusted_box = [
                    int(box[0] * width_scale),
                    int(box[1] * height_scale),
                    int(box[2] * width_scale),
                    int(box[3] * height_scale)
                ]
                # Ensure boxes are within image bounds
                adjusted_box = [
                    max(0, min(adjusted_box[0], target_size-1)),
                    max(0, min(adjusted_box[1], target_size-1)),
                    max(0, min(adjusted_box[2], target_size-1)),
                    max(0, min(adjusted_box[3], target_size-1))
                ]
                # Ensure x1 > x0 and y1 > y0
                if adjusted_box[2] <= adjusted_box[0]:
                    adjusted_box[2] = adjusted_box[0] + 1
                if adjusted_box[3] <= adjusted_box[1]:
                    adjusted_box[3] = adjusted_box[1] + 1

                adjusted_boxes.append(adjusted_box)
            else:
                adjusted_boxes.append([0, 0, 1, 1])  # fallback box

        return resized_image, adjusted_boxes

    def validate_and_clean_data(self, words, boxes):
        """Validate và clean dữ liệu words và boxes"""
        if not isinstance(words, list) or not isinstance(boxes, list):
            return ["dummy"], [[0, 0, 100, 20]]

        if len(words) != len(boxes):
            min_len = min(len(words), len(boxes))
            words = words[:min_len]
            boxes = boxes[:min_len]

        clean_words = []
        clean_boxes = []

        for word, box in zip(words, boxes):
            # Validate word
            if not isinstance(word, str) or len(word.strip()) == 0:
                word = "empty"

            # Validate box
            if not isinstance(box, list) or len(box) != 4:
                box = [0, 0, 100, 20]

            try:
                box = [int(coord) for coord in box]
                # Ensure valid box coordinates
                if box[0] >= box[2] or box[1] >= box[3]:
                    box = [0, 0, 100, 20]
            except (ValueError, TypeError):
                box = [0, 0, 100, 20]

            clean_words.append(str(word).strip())
            clean_boxes.append(box)

        # Ensure at least one valid entry
        if not clean_words:
            clean_words = ["dummy"]
            clean_boxes = [[0, 0, 100, 20]]

        return clean_words, clean_boxes

    def predict_single(self, image, words, boxes, return_probabilities=False):
        """
        Dự đoán cho một mẫu duy nhất

        Args:
            image: pil image object
            words (list): Danh sách các từ
            boxes (list): Danh sách các bounding box tương ứng
            return_probabilities (bool): Có trả về xác suất hay không

        Returns:
            dict: Kết quả dự đoán
        """
        try:
            # Load image
            image = image.convert("RGB")
            original_width, original_height = image.size

            # Validate and clean data
            words, boxes = self.validate_and_clean_data(words, boxes)

            # Resize image and adjust boxes
            resized_image, adjusted_boxes = self.resize_image_and_boxes(
                image, boxes, target_size=self.LAYOUTLM_IMAGE_SIZE
            )

            # Normalize boxes to 0-1000 scale for LayoutLM
            normalized_boxes = []
            for box in adjusted_boxes:
                normalized_box = self.normalize_box(box, self.LAYOUTLM_IMAGE_SIZE, self.LAYOUTLM_IMAGE_SIZE)
                normalized_boxes.append(normalized_box)

            # Limit sequence length
            if len(words) > self.MAX_SEQ_LENGTH - 2:
                words = words[:self.MAX_SEQ_LENGTH - 2]
                normalized_boxes = normalized_boxes[:self.MAX_SEQ_LENGTH - 2]

            # Process with LayoutLMv3Processor
            encoding = self.processor(
                resized_image,
                words,
                boxes=normalized_boxes,
                truncation=True,
                padding="max_length",
                max_length=self.MAX_SEQ_LENGTH,
                return_tensors="pt"
            )

            # Move to device
            encoding = {k: v.to(self.device) for k, v in encoding.items()}

            # Inference
            with torch.no_grad():
                outputs = self.model(**encoding)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
                predicted_class = torch.argmax(logits, dim=-1).item()

            # Prepare results
            result = {
                'predicted_class': predicted_class,
                'predicted_label': self.id_to_label[predicted_class],
                'confidence': float(probabilities[0][predicted_class])
            }

            if return_probabilities:
                result['probabilities'] = {
                    self.id_to_label[i]: float(prob)
                    for i, prob in enumerate(probabilities[0])
                }

            return result

        except Exception as e:
            print(f"Error in prediction: {e}")
            return {
                'predicted_class': 0,
                'predicted_label': self.id_to_label[0],
                'confidence': 0.0,
                'error': str(e)
            }

    def predict_from_json(self, json_data, base_dir="", return_probabilities=False):
        """
        Dự đoán từ dữ liệu JSON (format giống như trong training)

        Args:
            json_data (dict): Dữ liệu JSON chứa image_path, words, boxes
            base_dir (str): Thư mục gốc chứa ảnh
            return_probabilities (bool): Có trả về xác suất hay không

        Returns:
            dict: Kết quả dự đoán
        """
        image_path = os.path.join(base_dir, json_data['image_path'])
        words = json_data.get('words', [])
        boxes = json_data.get('boxes', [])

        return self.predict_single(image_path, words, boxes, return_probabilities)

    def predict_batch(self, data_list, base_dir="", return_probabilities=False):
        """
        Dự đoán cho một batch dữ liệu

        Args:
            data_list (list): Danh sách các dict chứa dữ liệu
            base_dir (str): Thư mục gốc chứa ảnh
            return_probabilities (bool): Có trả về xác suất hay không

        Returns:
            list: Danh sách kết quả dự đoán
        """
        results = []

        print(f"Processing {len(data_list)} samples...")
        for i, data in enumerate(data_list):
            if i % 10 == 0:
                print(f"Processing {i+1}/{len(data_list)}")

            result = self.predict_from_json(data, base_dir, return_probabilities)
            result['sample_index'] = i
            results.append(result)

        return results

    def evaluate_predictions(self, predictions, true_labels):
        """
        Đánh giá kết quả dự đoán

        Args:
            predictions (list): Danh sách kết quả dự đoán
            true_labels (list): Danh sách label thực tế

        Returns:
            dict: Các metric đánh giá
        """
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report

        pred_classes = [p['predicted_class'] for p in predictions]

        # Convert string labels to int if needed
        true_labels_int = []
        for label in true_labels:
            if isinstance(label, str):
                true_labels_int.append(int(label))
            else:
                true_labels_int.append(label)

        metrics = {
            'accuracy': accuracy_score(true_labels_int, pred_classes),
            'f1_weighted': f1_score(true_labels_int, pred_classes, average='weighted'),
            'f1_macro': f1_score(true_labels_int, pred_classes, average='macro'),
            'precision_weighted': precision_score(true_labels_int, pred_classes, average='weighted'),
            'recall_weighted': recall_score(true_labels_int, pred_classes, average='weighted')
        }

        # Classification report
        report = classification_report(
            true_labels_int, pred_classes,
            target_names=[self.id_to_label[i] for i in range(4)],
            output_dict=True
        )

        metrics['classification_report'] = report

        return metrics
