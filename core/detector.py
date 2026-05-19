import cv2
import numpy as np
from ultralytics import YOLO


class SafetyDetector:
    def __init__(self, model_path='best.pt', conf_threshold=0.5, target_classes=None, alert_classes=None,
                 safety_equipment=None):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

        self.target_classes = target_classes if target_classes else []
        self.alert_classes = alert_classes if alert_classes else []
        self.safety_equipment = safety_equipment if safety_equipment else []

        try:
            self.class_names = self.model.names
            print(f"✅ Model loaded: {model_path}")
            print(f"📋 Available classes: {self.class_names}")
            print(f"🎯 Target classes: {self.target_classes}")
            print(f"🚨 Alert classes: {self.alert_classes}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.class_names = {}

    def detect_objects(self, frame):
        results = self.model(frame, conf=self.conf_threshold, verbose=False)

        detections = []
        person_detected = False

        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = box.conf[0].cpu().numpy()
                cls = int(box.cls[0].cpu().numpy())
                class_name = self.class_names.get(cls, f"class_{cls}")

                if class_name in self.target_classes:
                    if class_name == 'person':
                        person_detected = True

                    detections.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': conf,
                        'class_id': cls,
                        'class_name': class_name,
                        'foot_point': self._get_center_point([x1, y1, x2, y2]),
                        'is_alert': class_name in self.alert_classes
                    })

        safety_status = {}
        if person_detected:
            safety_status = self.analyze_safety_equipment(detections)

        return detections, safety_status

    def analyze_safety_equipment(self, detections):
        safety_status = {
            'has_helmet': False,
            'has_gloves': False,
            'has_vest': False,
            'has_boots': False,
            'has_goggles': False,
            'missing_equipment': []
        }

        detected_equipment = [det['class_name'] for det in detections if det['class_name'] in self.safety_equipment]

        safety_status.update({
            'has_helmet': 'helmet' in detected_equipment,
            'has_gloves': 'gloves' in detected_equipment,
            'has_vest': 'vest' in detected_equipment,
            'has_boots': 'boots' in detected_equipment,
            'has_goggles': 'goggles' in detected_equipment
        })

        for equipment in self.safety_equipment:
            if equipment not in detected_equipment:
                safety_status['missing_equipment'].append(equipment)

        return safety_status

    def _get_center_point(self, bbox):
        # Lấy tọa độ bounding box: [x1, y1, x2, y2]
        x1, y1, x2, y2 = bbox

        # Tính tọa độ x trung tâm: trung bình của x1 và x2
        center_x = (x1 + x2) / 2

        # Tính tọa độ y trung tâm: trung bình của y1 và y2 (điểm cắt 2 đường chéo)
        center_y = (y1 + y2) / 2

        # Trả về tọa độ [center_x, center_y]
        return [center_x, center_y]

    def count_people(self, detections):
        people_count = 0
        for det in detections:
            if det['class_name'] == 'person':
                people_count += 1
        return people_count