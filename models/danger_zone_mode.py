import cv2
import time
from .base_mode import BaseMode
from utils.helpers import check_danger_zone_intrusion


class DangerZoneMode(BaseMode):
    def __init__(self, detector, visualizer, audio_manager, zone_manager):
        super().__init__("Danger Zone Monitoring", detector, visualizer, audio_manager)
        self.zone_manager = zone_manager
        self.last_alert_time = 0
        self.alert_cooldown = 5
        self.people_in_danger = 0
        self.total_intrusions = 0
        self.allow_empty_zones = True  # Cho phép kích hoạt mà không cần vùng

    def process_frame(self, frame):
        if not self.is_active:
            return frame, False

        # Draw danger zones (vẽ ngay cả khi chưa có vùng)
        frame = self.zone_manager.draw_danger_zones(frame)

        # Only check for intrusions if we have zones
        if self.zone_manager.has_zones():
            detections, safety_status = self.detector.detect_objects(frame)

            # Check for intrusions
            danger_zones = self.zone_manager.get_danger_zones()
            intrusions = check_danger_zone_intrusion(detections, danger_zones, frame.shape)

            self.people_in_danger = len(intrusions)

            # Handle alerts
            if intrusions:
                current_time = time.time()
                if current_time - self.last_alert_time > self.alert_cooldown:
                    print(f"🚨 DANGER ZONE INTRUSION: {len(intrusions)} people in danger zone!")
                    self.audio_manager.play_alert_sound('intrusion')
                    self.last_alert_time = current_time
                    self.total_intrusions += len(intrusions)

            # Draw detections
            safe_detections = [det for det in detections if not any(
                intrusion['detection'] == det for intrusion in intrusions
            )]
            danger_detections = [intrusion['detection'] for intrusion in intrusions]

            frame = self.visualizer.draw_detections(frame, safe_detections, False)
            frame = self.visualizer.draw_detections(frame, danger_detections, True)

            return frame, len(intrusions) > 0
        else:
            # No zones yet, just draw instructions
            return frame, False

    def draw_ui(self, frame):
        if not self.is_active:
            return frame

        # Draw mode-specific UI
        cv2.putText(frame, "MODE: DANGER ZONE MONITORING", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Draw zone statistics
        cv2.putText(frame, f"Danger Zones: {len(self.zone_manager.danger_zones)}",
                    (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if self.zone_manager.has_zones():
            cv2.putText(frame, f"People in Danger: {self.people_in_danger}",
                        (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, f"Total Intrusions: {self.total_intrusions}",
                        (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        else:
            # Show zone drawing instructions
            cv2.putText(frame, "NO DANGER ZONES DEFINED", (10, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            cv2.putText(frame, "Press 'n' to start drawing danger zones", (10, 210),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
            cv2.putText(frame, "Left click to add points, 'c' to complete", (10, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)

        return frame

    def get_instructions(self):
        return [
            "🎯 DANGER ZONE MODE:",
            "- Draw custom danger zones on screen",
            "- Alerts when people enter danger zones",
            "- Draw zones AFTER activating this mode",
            "- Press 'n' to start drawing zones",
            "- Left click to add points, 'c' to complete"
        ]

    def can_activate(self):
        # Always allow activation, even without zones
        return True

    def reset_stats(self):
        self.people_in_danger = 0
        self.total_intrusions = 0