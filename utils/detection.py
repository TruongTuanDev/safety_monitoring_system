import cv2
import numpy as np
from ultralytics import YOLO


class SafetyDetector:
    def __init__(self, model_path='yolov8n.pt', conf_threshold=0.5):
        """
        Khởi tạo detector sử dụng YOLO
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.class_names = ['person']  # Chỉ quan tâm đến class person

    def detect_people(self, frame):
        """
        Phát hiện người trong frame
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Lấy thông tin bounding box
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())

                # Chỉ lấy detection của class person
                if cls == 0:  # class 0 là person trong COCO
                    detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': conf,
                        'foot_point': self._get_foot_point([x1, y1, x2, y2])
                    })

        return detections

    def _get_foot_point(self, bbox):
        """
        Tính điểm chân (điểm giữa dưới của bounding box)
        """
        x1, y1, x2, y2 = bbox
        foot_x = (x1 + x2) / 2
        foot_y = y2  # Điểm dưới cùng
        return [foot_x, foot_y]