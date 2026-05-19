import sys
import time

import cv2
import yaml

from auth.db import DatabaseClient
from auth.manager import ensure_indexes
from camera.camera_manager import CameraManager
from core.audio_manager import AudioManager
from core.detector import SafetyDetector
from core.visualizer import SafetyVisualizer
from models.danger_zone_mode import DangerZoneMode
from models.safety_gear_mode import SafetyGearMode
from ui.auth_ui import show_auth_window
from ui.camera_dashboard import CameraDashboard
from ui.window_manager import WindowManager
from ui.zone_manager import ZoneManager


class SafetyMonitoringSystem:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        self.current_user = None
        db_conf = self.config.get("database", {})
        mongo_uri = db_conf.get("mongo_uri", "mongodb://localhost:27017")
        mongo_db = db_conf.get("mongo_db", "safety_monitoring")

        try:
            self.db_client = DatabaseClient(mongo_uri, mongo_db)
            ensure_indexes(self.db_client)
            auth_result = show_auth_window(self.db_client)
            if isinstance(auth_result, dict):
                self.current_user = auth_result
                name = self.current_user.get("full_name") or self.current_user.get("username")
                print(f"User authenticated: {name}")
            else:
                raise SystemExit("Authentication required")
        except Exception as e:
            print(f"Warning: could not initialize auth, continuing without authenticated user ({e})")
            self.db_client = None

        self.camera_manager = CameraManager(mongo_uri, mongo_db)
        self.camera_dashboard = CameraDashboard()

        self.show_camera_dashboard = True
        self.current_camera_index = 0

        self.detector = SafetyDetector(
            model_path=self.config["system"]["model_path"],
            conf_threshold=self.config["system"]["confidence_threshold"],
            target_classes=self.config["classes"]["target_classes"],
            alert_classes=self.config["classes"]["alert_classes"],
            safety_equipment=self.config["classes"]["safety_equipment"],
        )

        self.visualizer = SafetyVisualizer()
        self.audio_manager = AudioManager()
        self.audio_enabled = self.config.get("alerts", {}).get("sound_alert", True)
        self.audio_manager.set_enabled(self.audio_enabled)
        self.window_manager = WindowManager()
        self.zone_manager = ZoneManager()

        self.safety_gear_mode = SafetyGearMode(self.detector, self.visualizer, self.audio_manager)
        self.danger_zone_mode = DangerZoneMode(
            self.detector,
            self.visualizer,
            self.audio_manager,
            self.zone_manager,
        )

        self.current_mode = None
        self.modes = {
            "1": self.safety_gear_mode,
            "2": self.danger_zone_mode,
            "3": "camera_dashboard",
        }

        self.last_mode_switch = 0
        self.mode_switch_cooldown = 1.0

        print("Safety Monitoring System started")
        print("Available modes:")
        print("1. Safety Gear Check")
        print("2. Danger Zone Monitoring")
        print("3. Camera Dashboard")

    def run(self):
        prev_time = 0
        frame_count = 0
        start_time = time.time()

        window_width, window_height = self.window_manager.get_window_size()
        self.zone_manager.set_window_size(window_width, window_height)
        self.window_manager.set_mouse_callback(self.zone_manager.handle_left_click)

        self.print_instructions()

        while True:
            if self.show_camera_dashboard:
                cameras = self.camera_manager.get_all_cameras()
                action = self.camera_dashboard.display(self.camera_manager, cameras)
                key = cv2.waitKey(100) & 0xFF

                if action == "add_camera" or key in (ord("a"), ord("A")):
                    self._add_new_camera()
                    continue
                if key == ord("q"):
                    break
                if key == ord("1"):
                    self._switch_to_mode("1")
                elif key == ord("2"):
                    self._switch_to_mode("2")
                elif key == ord("0"):
                    self.show_camera_dashboard = True
                elif key == ord("r"):
                    self._refresh_cameras()
                elif key == ord("m"):
                    self._toggle_audio()
                continue

            frame = self._get_current_camera_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            frame = cv2.resize(frame, (window_width, window_height))
            frame = cv2.flip(frame, 1)

            current_time = time.time()
            fps = 1 / (current_time - prev_time) if prev_time > 0 else 0
            prev_time = current_time
            frame_count += 1

            is_alarming = False
            if self.current_mode:
                frame, is_alarming = self.current_mode.process_frame(frame)
                frame = self.current_mode.draw_ui(frame)
            else:
                frame = self.draw_mode_selection(frame)

            frame = self.draw_common_ui(frame, current_time, start_time, frame_count, fps, is_alarming)
            self.window_manager.display_frame(frame)

            if self.handle_keyboard_input(current_time):
                break

        self.camera_manager.stop_all()
        cv2.destroyAllWindows()

        if self.db_client:
            self.db_client.close()
        print("System stopped")

    def _toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        self.audio_manager.set_enabled(self.audio_enabled)
        status = "ENABLED" if self.audio_enabled else "DISABLED"
        print(f"Audio alerts {status}")

    def _get_current_camera_frame(self):
        cameras = self.camera_manager.get_all_cameras()
        if not cameras:
            return None

        if self.current_camera_index >= len(cameras):
            self.current_camera_index = 0

        return self.camera_manager.get_camera_frame(cameras[self.current_camera_index].id)

    def _add_new_camera(self):
        camera_info = self.camera_dashboard.show_add_camera_dialog()
        if not camera_info:
            return

        print(f"Adding camera: {camera_info['name']}")
        success = self.camera_manager.add_new_camera(
            name=camera_info["name"],
            camera_type=camera_info["type"],
            ip=camera_info.get("ip"),
            port=camera_info.get("port"),
            source=camera_info.get("source", "0"),
            username=camera_info.get("username"),
            password=camera_info.get("password"),
        )

        if success:
            print(f"Added camera: {camera_info['name']}")
        else:
            print(f"Failed to add camera: {camera_info['name']}")

    def _refresh_cameras(self):
        print("Refreshing camera list")
        self.camera_manager.stop_all()
        db_conf = self.config.get("database", {})
        self.camera_manager = CameraManager(
            db_conf.get("mongo_uri", "mongodb://localhost:27017"),
            db_conf.get("mongo_db", "safety_monitoring"),
        )
        self.current_camera_index = 0

    def _switch_to_mode(self, mode_key):
        self.show_camera_dashboard = False
        self.switch_mode(mode_key)

    def draw_mode_selection(self, frame):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        cv2.putText(
            frame,
            "SAFETY MONITORING SYSTEM",
            (frame.shape[1] // 2 - 200, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (255, 255, 255),
            3,
        )

        zone_status = f"Danger Zones: {len(self.zone_manager.danger_zones)}"
        zone_color = (0, 255, 0) if self.zone_manager.has_zones() else (255, 255, 255)
        cv2.putText(frame, zone_status, (frame.shape[1] // 2 - 80, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, zone_color, 2)

        y_offset = 170
        modes = [
            ("1 - SAFETY GEAR CHECK", "Entrance - Check PPE equipment", (0, 255, 255)),
            ("2 - DANGER ZONE MONITORING", "Work Area - Monitor restricted zones", (255, 255, 0)),
            ("3 - CAMERA DASHBOARD", "View all cameras in dashboard", (100, 255, 100)),
        ]

        for title, description, color in modes:
            cv2.putText(frame, title, (frame.shape[1] // 2 - 150, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(
                frame,
                description,
                (frame.shape[1] // 2 - 150, y_offset + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )
            y_offset += 90

        cameras = self.camera_manager.get_all_cameras()
        if cameras and self.current_camera_index < len(cameras):
            current_cam = cameras[self.current_camera_index]
            cv2.putText(
                frame,
                f"Current Camera: {current_cam.name} (Press 'n' to switch)",
                (frame.shape[1] // 2 - 180, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (100, 255, 100),
                1,
            )

        cv2.putText(
            frame,
            "Press number key to select mode | 'q' to quit",
            (frame.shape[1] // 2 - 180, y_offset + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        hint = (
            f"Ready! {len(self.zone_manager.danger_zones)} zones defined"
            if self.zone_manager.has_zones()
            else "You can draw zones after activating Danger Zone Mode"
        )
        hint_color = (0, 255, 0) if self.zone_manager.has_zones() else (255, 255, 0)
        cv2.putText(frame, hint, (frame.shape[1] // 2 - 180, y_offset + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, hint_color, 1)

        return frame

    def draw_common_ui(self, frame, current_time, start_time, frame_count, fps, is_alarming):
        window_width, window_height = self.window_manager.get_window_size()

        if self.current_user:
            display_name = self.current_user.get("full_name") or self.current_user.get("username")
            cv2.putText(frame, f"User: {display_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 255), 2)

        cameras = self.camera_manager.get_all_cameras()
        if cameras and self.current_camera_index < len(cameras):
            current_cam = cameras[self.current_camera_index]
            cv2.putText(frame, current_cam.name, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 1)

        current_fps = frame_count / (current_time - start_time) if (current_time - start_time) >= 1 else fps
        cv2.putText(frame, f"FPS: {current_fps:.2f}", (window_width - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        zones_text = f"Zones: {len(self.zone_manager.danger_zones)}"
        zones_color = (0, 255, 0) if self.zone_manager.has_zones() else (255, 255, 0)
        cv2.putText(frame, zones_text, (window_width - 300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, zones_color, 2)

        if self.current_mode:
            status_color = (0, 255, 0) if not is_alarming else (0, 0, 255)
            status_text = f"ACTIVE: {self.current_mode.name}" + (" - ALERT!" if is_alarming else "")
            if self.current_mode == self.danger_zone_mode and not self.zone_manager.has_zones() and not self.zone_manager.drawing_mode:
                cv2.putText(frame, "Press 'n' to draw danger zones", (10, window_height - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
        else:
            status_color = (255, 255, 0)
            status_text = "SELECT MODE"

        cv2.putText(frame, status_text, (10, window_height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        if self.zone_manager.drawing_mode:
            points_text = f"Drawing: {len(self.zone_manager.current_zone_points)} points - Press 'c' to complete"
            cv2.putText(frame, points_text, (window_width // 2 - 150, window_height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)

        if is_alarming:
            cv2.putText(frame, "ALERT!", (window_width // 2 - 100, 50), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 3)
            frame = cv2.rectangle(frame, (0, 0), (window_width, window_height), (0, 0, 255), 10)

        return frame

    def handle_keyboard_input(self, current_time):
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            return True

        if key in [ord("1"), ord("2"), ord("3")] and current_time - self.last_mode_switch > self.mode_switch_cooldown:
            mode_key = chr(key)
            if mode_key == "3":
                self.show_camera_dashboard = True
                self.current_mode = None
                print("Activated camera dashboard")
            else:
                self._switch_to_mode(mode_key)
            self.last_mode_switch = current_time
            return False

        if key == ord("a") and not self.show_camera_dashboard:
            self._add_new_camera()
            return False

        if key == ord("n"):
            cameras = self.camera_manager.get_all_cameras()
            if self.current_mode == self.safety_gear_mode and len(cameras) > 1:
                self.current_camera_index = (self.current_camera_index + 1) % len(cameras)
                print(f"Switch to camera: {cameras[self.current_camera_index].name}")
            elif self.current_mode != self.safety_gear_mode:
                self.zone_manager.drawing_mode = True
                self.zone_manager.current_zone_points = []
                self.zone_manager.selected_zone_index = -1
                print("Started drawing new danger zone")
            return False

        if key == ord("c") and self.zone_manager.drawing_mode:
            if self.zone_manager.complete_current_zone():
                print("Zone created")
            return False

        if key == ord("x"):
            self.zone_manager.delete_selected_zone()
            return False

        if key == ord("r"):
            self.reset_system()
            return False

        if key == ord("m"):
            self._toggle_audio()
            return False

        if key == ord("0"):
            self.show_camera_dashboard = False
            self.switch_mode(None)

        return False

    def switch_mode(self, mode_key):
        if self.current_mode:
            self.current_mode.deactivate()

        if mode_key and mode_key in self.modes and mode_key != "3":
            self.current_mode = self.modes[mode_key]
            self.current_mode.activate()

            if self.current_mode == self.danger_zone_mode and not self.zone_manager.has_zones():
                print("Danger Zone Mode activated. Press 'n' to start drawing danger zones")

            print("\n" + "=" * 50)
            print(f"ACTIVATED: {self.current_mode.name}")
            print("=" * 50)
            for instruction in self.current_mode.get_instructions():
                print(f"  {instruction}")
            print("=" * 50)
        else:
            self.current_mode = None
            print("Returned to mode selection")

    def reset_system(self):
        for mode in self.modes.values():
            if hasattr(mode, "reset_stats"):
                mode.reset_stats()

        self.zone_manager.reset()

        if self.current_mode:
            self.current_mode.deactivate()
            self.current_mode = None

        self.audio_manager.stop_alert_sound()
        print("System reset complete")

    def print_instructions(self):
        print("SYSTEM OVERVIEW:")
        print("  1 - Safety Gear Mode")
        print("  2 - Danger Zone Mode")
        print("  3 - Camera Dashboard")
        print("  0 - Return to mode selection")
        print("  n - Switch camera in mode 1, draw zone in mode 2")
        print("  c - Complete current zone")
        print("  x - Delete selected zone")
        print("  m - Toggle audio")
        print("  q - Quit")


if __name__ == "__main__":
    system = SafetyMonitoringSystem()
    system.run()
