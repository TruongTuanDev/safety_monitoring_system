from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import cv2
import numpy as np
import datetime
import os
import simpleaudio as sa


def isInside(points, centroid):
    polygon = Polygon(points)
    centroid = Point(centroid)
    return polygon.contains(centroid)


class YoloDetect:
    def __init__(self, detect_class="person", frame_width=700, frame_height=300):
        # Đường dẫn tuyệt đối
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.classnames_file = os.path.join(base_path, "model", "classnames.txt")
        self.weights_file = os.path.join(base_path, "model", "yolov4-tiny.weights")
        self.config_file = os.path.join(base_path, "model", "yolov4-tiny.cfg")
        self.alert_sound_file = os.path.join(base_path, "canhbao.wav")

        # Tham số YOLO
        self.conf_threshold = 0.5
        self.nms_threshold = 0.4
        self.detect_class = detect_class
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.scale = 1 / 255.0

        # Load model
        self.model = cv2.dnn.readNet(self.weights_file, self.config_file)
        self.classes = []
        self.output_layers = []
        self.read_class_file()
        self.get_output_layers()

        # Audio alert
        self.last_alert = None
        self.alert_interval = 3  # giây
        self.wave_obj = self.load_sound_file()
        self.play_obj = None

    def load_sound_file(self):

        if not os.path.exists(self.alert_sound_file):
            print(f"Lỗi: File âm thanh {self.alert_sound_file} không tồn tại.")
            return None
        try:
            return sa.WaveObject.from_wave_file(self.alert_sound_file)
        except Exception as e:
            print(f"Lỗi khi tải file âm thanh: {e}")
            return None

    def read_class_file(self):
        if not os.path.exists(self.classnames_file):
            raise FileNotFoundError(f"{self.classnames_file} không tồn tại")
        with open(self.classnames_file, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]

    def get_output_layers(self):
        layer_names = self.model.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.model.getUnconnectedOutLayers()]

    def draw_prediction(self, img, class_id, x, y, x_plus_w, y_plus_h, points):
        if class_id >= len(self.classes):
            return False
        label = str(self.classes[class_id])
        color = (0, 255, 0)
        cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), color, 2)
        cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # centroid
        centroid = ((x + x_plus_w) // 2, (y + y_plus_h) // 2)
        cv2.circle(img, centroid, 5, color, -1)

        if isInside(points, centroid):
            img = self.alert(img)
            return True

        return False

    def play_sound(self):

        if self.wave_obj and (self.play_obj is None or not self.play_obj.is_playing()):

            self.play_obj = self.wave_obj.play()

    def alert(self, img):

        # Kiểm tra khoảng thời gian và đối tượng âm thanh đã được tải
        if self.wave_obj is not None and \
                ((self.last_alert is None) or (
                        (datetime.datetime.utcnow() - self.last_alert).total_seconds() > self.alert_interval)):
            self.last_alert = datetime.datetime.utcnow()

            self.play_sound()

        return img

    def detect(self, frame, points):
        if frame is None:
            return frame

        (H, W) = frame.shape[:2]
        self.frame_width = W
        self.frame_height = H
        # END SỬA LỖI

        # TỐI ƯU TỐC ĐỘ
        blob = cv2.dnn.blobFromImage(frame, self.scale, (320, 320), (0, 0, 0), True, crop=False)
        self.model.setInput(blob)
        outs = self.model.forward(self.output_layers)

        class_ids = []
        confidences = []
        boxes = []
        is_alarming = False  # Biến trạng thái cảnh báo mới

        for out in outs:
            for detection in out:
                scores = detection[5:]
                if len(scores) == 0:
                    continue
                class_id = int(np.argmax(scores))
                confidence = float(scores[class_id])

                # kiểm tra class_id hợp lệ
                if class_id >= len(self.classes):
                    continue

                if confidence >= self.conf_threshold and self.classes[class_id] == self.detect_class:
                    center_x = int(detection[0] * self.frame_width)
                    center_y = int(detection[1] * self.frame_height)
                    w = int(detection[2] * self.frame_width)
                    h = int(detection[3] * self.frame_height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    class_ids.append(class_id)
                    confidences.append(confidence)
                    boxes.append([x, y, w, h])

        # Kiểm tra NMS
        if len(boxes) > 0:
            indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_threshold, self.nms_threshold)
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                # Kiểm tra draw_prediction có kích hoạt cảnh báo không
                if self.draw_prediction(frame, class_ids[i], x, y, x + w, y + h, points):
                    is_alarming = True

        # TRẢ VỀ CẢ TRẠNG THÁI CẢNH BÁO
        return frame, is_alarming