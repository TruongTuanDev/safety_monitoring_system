import cv2
import numpy as np


class SafetyVisualizer:
    def __init__(self):
        self.colors = {
            'safe': (0, 255, 0),  # Xanh lá
            'danger': (0, 0, 255),  # Đỏ
            'warning': (0, 255, 255)  # Vàng
        }

    def draw_danger_zones(self, frame, danger_zones):
        """
        Vẽ các vùng nguy hiểm lên frame
        """
        h, w = frame.shape[:2]

        for zone in danger_zones:
            points = np.array(zone['points']) * [w, h]
            points = points.astype(np.int32)

            # Vẽ polygon trong suốt
            overlay = frame.copy()
            cv2.fillPoly(overlay, [points], zone['color'])
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

            # Vẽ viền
            cv2.polylines(frame, [points], True, zone['color'], 2)

            # Hiển thị tên vùng
            cv2.putText(frame, zone['name'], (points[0][0], points[0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, zone['color'], 2)

        return frame

    def draw_detections(self, frame, detections, in_danger=False):
        """
        Vẽ bounding box và thông tin detection
        """
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']

            # Chọn màu dựa trên trạng thái
            color = self.colors['danger'] if in_danger else self.colors['safe']

            # Vẽ bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Vẽ label
            label = f"Person: {conf:.2f}"
            if in_danger:
                label = "DANGER! " + label

            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Vẽ điểm chân
            foot_x, foot_y = int(det['foot_point'][0]), int(det['foot_point'][1])
            cv2.circle(frame, (foot_x, foot_y), 5, color, -1)

        return frame

    def draw_status(self, frame, alert_count, fps):
        """
        Vẽ thông tin trạng thái hệ thống
        """
        # Hiển thị FPS
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Hiển thị số cảnh báo
        cv2.putText(frame, f"Alerts: {alert_count}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Hiển thị trạng thái
        status = "SAFE" if alert_count == 0 else "DANGER!"
        color = (0, 255, 0) if alert_count == 0 else (0, 0, 255)
        cv2.putText(frame, f"Status: {status}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        return frame