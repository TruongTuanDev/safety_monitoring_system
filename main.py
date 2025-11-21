import os
import cv2
import time
import pygame
import yaml
import numpy as np

from utils import SafetyDetector, SafetyVisualizer


class SafetyMonitoringSystem:
    def __init__(self, config_path='config.yaml'):

        # Load config
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Init components
        self.detector = SafetyDetector(
            conf_threshold=self.config['system']['confidence_threshold']
        )
        self.visualizer = SafetyVisualizer()

        # State
        self.alert_count = 0
        self.fps = 0

        print("🚀 Hệ thống giám sát an toàn đã khởi chạy!")

    # -----------------------------
    # KIỂM TRA ĐIỂM TRONG VÙNG NGUY HIỂM
    # -----------------------------
    def is_point_in_polygon(self, point, polygon):
        point = np.array(point)
        polygon = np.array(polygon)
        x, y = point
        inside = False

        p1x, p1y = polygon[0]
        for i in range(len(polygon) + 1):
            p2x, p2y = polygon[i % len(polygon)]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    # -----------------------------
    # KIỂM TRA XÂM NHẬP VÙNG NGUY HIỂM
    # -----------------------------
    def check_danger_zone_intrusion(self, detections, danger_zones, frame_shape):
        intrusions = []
        h, w = frame_shape[:2]

        for det in detections:
            foot_point = det['foot_point']
            norm_point = [foot_point[0] / w, foot_point[1] / h]

            for zone in danger_zones:
                if self.is_point_in_polygon(norm_point, zone['points']):
                    intrusions.append({"detection": det, "zone": zone})
                    break

        return intrusions

    # -----------------------------
    # HÀM CHÍNH CHẠY CAMERA
    # -----------------------------
    def run(self):
        cap = cv2.VideoCapture(self.config['camera']['source'])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['camera']['width'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['camera']['height'])

        print("📹 Camera đang chạy...")
        print("➡ Nhấn Q thoát")

        prev_time = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Không đọc được frame!")
                break

            # FPS
            now = time.time()
            self.fps = 1 / (now - prev_time) if prev_time != 0 else 0
            prev_time = now

            # PHÁT HIỆN NGƯỜI
            detections = self.detector.detect_people(frame)

            # 👉 In ra khi phát hiện có người
            if len(detections) > 0:
                print(f"👤 PHÁT HIỆN {len(detections)} NGƯỜI TRONG KHUNG HÌNH")
            else:
                print("⭕ KHÔNG CÓ NGƯỜI")

            # KIỂM TRA XÂM NHẬP
            intrusions = self.check_danger_zone_intrusion(
                detections,
                self.config['danger_zones'],
                frame.shape
            )

            # 👉 In ra khi có người vào vùng nguy hiểm
            if len(intrusions) > 0:
                print(f"⚠️ {len(intrusions)} NGƯỜI ĐÃ VÀO VÙNG NGUY HIỂM!")

            self.alert_count = len(intrusions)

            # Visual
            frame = self.visualizer.draw_danger_zones(frame, self.config['danger_zones'])

            safe = [d for d in detections if d not in [i['detection'] for i in intrusions]]
            danger = [i['detection'] for i in intrusions]

            frame = self.visualizer.draw_detections(frame, safe, False)
            frame = self.visualizer.draw_detections(frame, danger, True)

            frame = self.visualizer.draw_status(frame, self.alert_count, self.fps)

            cv2.imshow("Safety Monitoring System", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        print("👋 Hệ thống đã tắt.")


if __name__ == "__main__":
    system = SafetyMonitoringSystem()
    system.run()
