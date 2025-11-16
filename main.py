import cv2
import time
import yaml
import numpy as np
from utils import SafetyDetector, SafetyVisualizer, AudioAlertSystem  # Thêm AudioAlertSystem


class SafetyMonitoringSystem:
    def __init__(self, config_path='config.yaml'):
        # Load cấu hình
        with open('config.yaml', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # Khởi tạo các component
        self.detector = SafetyDetector(
            conf_threshold=self.config['system']['confidence_threshold']
        )
        self.visualizer = SafetyVisualizer()
        self.audio_alert = AudioAlertSystem()  # Thêm hệ thống âm thanh

        # Biến theo dõi
        self.alert_count = 0
        self.fps = 0
        self.last_alert_time = 0
        self.alert_cooldown = 3  # Giây giữa các lần cảnh báo

        print("🚀 Hệ thống giám sát an toàn đã được khởi chạy!")
        print("🔊 Hệ thống âm thanh cảnh báo đã sẵn sàng!")

    def is_point_in_polygon(self, point, polygon):
        """
        Kiểm tra điểm có nằm trong đa giác không
        """
        point = np.array(point)
        polygon = np.array(polygon)

        # Thuật toán ray casting
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def check_danger_zone_intrusion(self, detections, danger_zones, frame_shape):
        """
        Kiểm tra xem có người nào xâm nhập vùng nguy hiểm không
        """
        intrusions = []
        h, w = frame_shape[:2]

        for det in detections:
            foot_point = det['foot_point']
            # Chuẩn hóa tọa độ điểm chân
            normalized_point = [foot_point[0] / w, foot_point[1] / h]

            for zone in danger_zones:
                if self.is_point_in_polygon(normalized_point, zone['points']):
                    intrusions.append({
                        'detection': det,
                        'zone': zone
                    })
                    break  # Một người chỉ cần cảnh báo một lần

        return intrusions

    def handle_audio_alert(self, intrusions):
        """
        Xử lý cảnh báo âm thanh khi có xâm nhập
        """
        current_time = time.time()

        if intrusions and (current_time - self.last_alert_time) > self.alert_cooldown:
            # Có xâm nhập và đã qua thời gian chờ
            if self.audio_alert.trigger_alert():
                print(f"🚨 CẢNH BÁO: Phát hiện {len(intrusions)} người xâm nhập khu vực nguy hiểm!")
                self.last_alert_time = current_time
        elif not intrusions:
            # Không có xâm nhập, dừng cảnh báo nếu đang phát
            self.audio_alert.stop_alert()

    def run(self):
        """
        Chạy hệ thống giám sát chính
        """
        # Khởi tạo camera
        cap = cv2.VideoCapture(self.config['camera']['source'])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['camera']['width'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['camera']['height'])

        prev_time = 0

        print("📹 Đang khởi động camera...")
        print("🎯 Nhấn 'q' để thoát")
        print("🎯 Nhấn 'r' để reset cảnh báo")
        print("🎯 Nhấn 'm' để tắt/bật âm thanh")

        audio_enabled = self.config['alerts']['sound_alert']

        while True:
            # Đọc frame
            ret, frame = cap.read()
            if not ret:
                print("❌ Không thể đọc frame từ camera!")
                break

            # Tính FPS
            current_time = time.time()
            self.fps = 1 / (current_time - prev_time) if prev_time > 0 else 0
            prev_time = current_time

            # Phát hiện người
            detections = self.detector.detect_people(frame)

            # Kiểm tra xâm nhập vùng nguy hiểm
            intrusions = self.check_danger_zone_intrusion(
                detections,
                self.config['danger_zones'],
                frame.shape
            )

            # Cập nhật số cảnh báo
            self.alert_count = len(intrusions)

            # Xử lý cảnh báo âm thanh
            if audio_enabled:
                self.handle_audio_alert(intrusions)

            # Visualize
            # Vẽ vùng nguy hiểm
            frame = self.visualizer.draw_danger_zones(frame, self.config['danger_zones'])

            # Vẽ detections (phân biệt người an toàn và nguy hiểm)
            safe_detections = [det for det in detections if not any(
                intrusion['detection'] == det for intrusion in intrusions
            )]
            danger_detections = [intrusion['detection'] for intrusion in intrusions]

            frame = self.visualizer.draw_detections(frame, safe_detections, False)
            frame = self.visualizer.draw_detections(frame, danger_detections, True)

            # Vẽ trạng thái hệ thống (thêm trạng thái âm thanh)
            frame = self.visualizer.draw_status(frame, self.alert_count, self.fps)

            # Hiển thị trạng thái âm thanh
            audio_status = "ON" if audio_enabled else "OFF"
            audio_color = (0, 255, 0) if audio_enabled else (0, 0, 255)
            cv2.putText(frame, f"Audio: {audio_status}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, audio_color, 2)

            # Hiển thị frame
            cv2.imshow('Safety Monitoring System', frame)

            # Xử lý phím
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.alert_count = 0
                self.audio_alert.stop_alert()
                print("🔄 Đã reset số cảnh báo!")
            elif key == ord('m'):
                audio_enabled = not audio_enabled
                status = "BẬT" if audio_enabled else "TẮT"
                print(f"🔊 Đã {status} âm thanh cảnh báo!")
                if not audio_enabled:
                    self.audio_alert.stop_alert()

        # Giải phóng tài nguyên
        cap.release()
        cv2.destroyAllWindows()
        self.audio_alert.stop_alert()
        print("👋 Hệ thống đã dừng!")


if __name__ == "__main__":
    system = SafetyMonitoringSystem()
    system.run()