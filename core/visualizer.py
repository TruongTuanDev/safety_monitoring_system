import cv2
import numpy as np


class SafetyVisualizer:
    def __init__(self):
        self.colors = {
            'person': (0, 255, 0),
            'helmet': (0, 255, 255),
            'gloves': (255, 255, 0),
            'vest': (255, 165, 0),
            'boots': (128, 0, 128),
            'goggles': (255, 0, 255),
            'no_helmet': (0, 0, 255),
            'no_gloves': (0, 0, 255),
            'no_vest': (0, 0, 255),
            'no_boots': (0, 0, 255),
            'no_goggle': (0, 0, 255),
            'none': (128, 128, 128),
            'danger': (0, 0, 255),
            'safe': (0, 255, 0),
            'warning': (0, 255, 255)
        }

    def draw_detections(self, frame, detections, in_danger=False):
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            class_name = det['class_name']

            color = self.colors.get(class_name, (255, 255, 255))

            if in_danger and det['is_alert']:
                color = self.colors['danger']

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{class_name}: {conf:.2f}"
            if in_danger and det['is_alert']:
                label = "🚨 " + label

            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            if class_name == 'person':
                foot_x, foot_y = int(det['foot_point'][0]), int(det['foot_point'][1])
                cv2.circle(frame, (foot_x, foot_y), 5, color, -1)

        return frame

    def draw_safety_status(self, frame, safety_status, person_detected):
        if not person_detected:
            return frame

        y_offset = 180
        cv2.putText(frame, "SAFETY STATUS:", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y_offset += 25

        equipment_status = {
            'helmet': safety_status.get('has_helmet', False),
            'gloves': safety_status.get('has_gloves', False),
            'vest': safety_status.get('has_vest', False),
            'boots': safety_status.get('has_boots', False),
            'goggles': safety_status.get('has_goggles', False)
        }

        for equipment, has_equipment in equipment_status.items():
            color = self.colors['safe'] if has_equipment else self.colors['danger']
            status = "OK" if has_equipment else "NO"
            text = f"{equipment}: {status}"

            cv2.putText(frame, text, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            y_offset += 20

        missing = safety_status.get('missing_equipment', [])
        if missing:
            cv2.putText(frame, f"Missing: {', '.join(missing)}", (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['danger'], 2)
            y_offset += 20

        all_equipped = all(equipment_status.values())
        overall_status = "FULLY EQUIPPED" if all_equipped else "MISSING EQUIPMENT"
        overall_color = self.colors['safe'] if all_equipped else self.colors['danger']

        cv2.putText(frame, f"Overall: {overall_status}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, overall_color, 2)

        return frame

    def draw_status(self, frame, alert_count, fps, safety_status=None):
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(frame, f"Alerts: {alert_count}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        status = "SAFE" if alert_count == 0 else "DANGER!"
        color = (0, 255, 0) if alert_count == 0 else (0, 0, 255)
        cv2.putText(frame, f"Status: {status}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        person_detected = safety_status is not None
        person_status = "Person: Detected" if person_detected else "Person: Not Found"
        person_color = (0, 255, 0) if person_detected else (0, 0, 255)
        cv2.putText(frame, person_status, (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, person_color, 2)

        return frame

    def draw_people_counter(self, frame, current_count, total_count, danger_count, window_width=None):
        """
        Vẽ bộ đếm người lên frame
        window_width: có thể là số hoặc None (sẽ tự động lấy từ frame)
        """
        # Nếu không có window_width, lấy từ frame
        if window_width is None:
            window_width = frame.shape[1]

        # Đảm bảo window_width là số
        if callable(window_width):
            window_width = window_width()

        # Tính toán vị trí
        counter_width = 250
        counter_height = 120
        margin = 10

        start_x = window_width - counter_width - margin
        end_x = window_width - margin
        start_y = margin
        end_y = margin + counter_height

        # Đảm bảo không vượt quá kích thước frame
        if start_x < 0:
            start_x = 0
        if end_x > frame.shape[1]:
            end_x = frame.shape[1]
        if end_y > frame.shape[0]:
            end_y = frame.shape[0]

        # Tạo background
        counter_bg = np.zeros((counter_height, counter_width, 3), dtype=np.uint8)
        counter_bg[:, :] = [0, 0, 0]

        # Đặt background vào frame
        frame[start_y:end_y, start_x:end_x] = counter_bg

        # Vẽ text
        text_start_x = start_x + 10

        cv2.putText(frame, "PEOPLE COUNTER",
                    (text_start_x, start_y + 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.putText(frame, f"Current: {current_count}",
                    (text_start_x, start_y + 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.putText(frame, f"Total: {total_count}",
                    (text_start_x, start_y + 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        cv2.putText(frame, f"In Danger: {danger_count}",
                    (text_start_x, start_y + 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return frame