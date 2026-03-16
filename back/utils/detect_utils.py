import base64
import io
from PIL import Image, ImageEnhance, ImageFilter
import torch
from ultralytics import YOLO


class YOLODetector:
    def __init__(self, model_path='models/yolov11n.pt', device='cpu'):
        self.device = device if torch.cuda.is_available() and device == 'cuda' else 'cpu'
        try:
            self.model = YOLO(model_path)
            self.model.eval()
            self.model = self.model.to(self.device)
            print(f"YOLOv8 model loaded successfully from {model_path} on device: {self.device}")
            self.image = None
            # self.rendered_image = None
        except Exception as e:
            print(f"Error loading YOLOv8 model: {e}")
            self.model = None

    def read_image(self, image_data):
        if isinstance(image_data, bytes):
            self.image = Image.open(io.BytesIO(image_data)).convert("RGB")
        elif isinstance(image_data, str):
            self.image = Image.open(image_data).convert("RGB")
        else:
            raise ValueError("Invalid image data format. Expected bytes or file path string.")

    def get_image_base64(self):
        if self.image is None:
            raise RuntimeError("No image has been read. Please call read_image() first.")
        img_byte_arr = io.BytesIO()
        self.image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return base64.b64encode(img_byte_arr).decode('utf-8')

    def detect(self):
        if self.model is None:
            raise RuntimeError("YOLOv11 model is not loaded. Please check the model path and device settings.")

        try:
            results = self.model(self.image)[0]
            # self.rendered_image = results.plot()[..., ::-1]
            # self.rendered_image = Image.fromarray(self.rendered_image)
            detections = []
            boxes = results.boxes
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].cpu().numpy().astype(int).tolist()
                conf = boxes.conf[i].cpu().item()
                cls = boxes.cls[i].cpu().item()
                x1, y1, x2, y2 = xyxy

                detections.append({
                    "class": self.model.names[int(cls)],
                    "box": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": float(conf),
                })

            return detections

        except Exception as e:
            raise RuntimeError(f"Error during detection: {e}")

    # def get_rendered_image(self):
    #     if self.rendered_image is None:
    #         raise RuntimeError("No rendered image available. Please run detection first.")
    #
    #     img_byte_arr = io.BytesIO()
    #     self.rendered_image.save(img_byte_arr, format='PNG')
    #     img_byte_arr = img_byte_arr.getvalue()
    #     return base64.b64encode(img_byte_arr).decode('utf-8')

    def enhance_image(self):
        self.image = ImageEnhance.Brightness(self.image).enhance(1.2)
        self.image = ImageEnhance.Contrast(self.image).enhance(1.3)
        self.image = ImageEnhance.Color(self.image).enhance(1.1)
        self.image = ImageEnhance.Sharpness(self.image).enhance(1.5)

    def denoise_image(self):
        self.image = self.image.filter(ImageFilter.MedianFilter(size=3))
