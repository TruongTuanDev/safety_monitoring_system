import cv2
import time
from .base_mode import BaseMode


class SafetyGearMode(BaseMode):
    def __init__(self, detector, visualizer, audio_manager):
        super().__init__("Safety Gear Check", detector, visualizer, audio_manager)
        self.last_alert_time = 0
        self.alert_cooldown = 5
        self.unsafe_people = 0
        self.safe_people = 0
        self.current_people_count = 0

    def process_frame(self, frame):
        if not self.is_active:
            return frame, False

        detections, safety_status = self.detector.detect_objects(frame)

        # Count people and check safety equipment
        people_detections = [det for det in detections if det['class_name'] == 'person']
        self.current_people_count = len(people_detections)

        # Analyze safety status for each person
        unsafe_count = 0
        safe_count = 0
        is_alarming = False

        if people_detections:
            missing_equipment = safety_status.get('missing_equipment', [])
            if missing_equipment:
                unsafe_count = len(people_detections)
                safe_count = 0
                is_alarming = True

                # Alert for unsafe person (ONLY in safety gear mode)
                current_time = time.time()
                if current_time - self.last_alert_time > self.alert_cooldown:
                    # print(f"🚨 SAFETY GEAR ALERT: Missing {', '.join(missing_equipment)}")
                    # self.audio_manager.play_alert_sound('intrusion')
                    self.last_alert_time = current_time
            else:
                unsafe_count = 0
                safe_count = len(people_detections)
                print(f"✅ SAFE PERSON: All equipment present")

        self.unsafe_people = unsafe_count
        self.safe_people = safe_count

        # Draw all detections (NO danger zone checking in this mode)
        frame = self.visualizer.draw_detections(frame, detections, False)

        # Draw safety status
        person_detected = len(people_detections) > 0
        frame = self.visualizer.draw_safety_status(frame, safety_status, person_detected)

        return frame, is_alarming

    def draw_ui(self, frame):
        if not self.is_active:
            return frame

        # Draw mode-specific UI
        cv2.putText(frame, "MODE: SAFETY GEAR CHECK", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Draw safety statistics
        cv2.putText(frame, f"People: {self.current_people_count}", (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Safe: {self.safe_people}", (10, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(frame, f"Unsafe: {self.unsafe_people}", (10, 210),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Draw instructions
        cv2.putText(frame, "Checking: Helmet, Gloves, Vest, Boots, Goggles",
                    (10, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Warning about no zone monitoring
        cv2.putText(frame, "NOT monitoring danger zones in this mode",
                    (10, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        return frame

    def get_instructions(self):
        return [
            "🎯 SAFETY GEAR MODE:",
            "- ONLY checks personal protective equipment",
            "- Alerts when missing safety gear",
            "- Does NOT monitor danger zones",
            "- Use for entrance/exit points"
        ]

    def reset_stats(self):
        self.unsafe_people = 0
        self.safe_people = 0
        self.current_people_count = 0