"""
multi_view.py - Hiển thị đa màn hình camera
"""
import cv2
import numpy as np
from typing import Dict, List
import sys
import os

# Sửa import - thêm đường dẫn project vào sys.path
try:
    # Thử import tuyệt đối trước
    from cameras.camera_manager import CameraManager
except ImportError:
    # Nếu không được, thêm đường dẫn project
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from camera.camera_manager import CameraManager

class MultiViewDisplay:
    """Hiển thị nhiều camera trên một màn hình"""

    def __init__(self, grid_size=(2, 2), window_name="Multi-Camera View"):
        self.grid_size = grid_size  # (rows, cols)
        self.window_name = window_name
        self.cell_width = 320
        self.cell_height = 240
        self.margin = 10
        self.padding = 5
        self.show_info = True

        # Tính toán kích thước tổng
        self.total_width = (self.cell_width + self.margin) * grid_size[1] + self.margin
        self.total_height = (self.cell_height + self.margin) * grid_size[0] + self.margin

        # Tạo window
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, self.total_width, self.total_height)

    def display(self, camera_manager: CameraManager, selected_cameras: List[str]):
        """
        Hiển thị nhiều camera

        Args:
            camera_manager: CameraManager instance
            selected_cameras: Danh sách ID camera cần hiển thị
        """
        # Tạo canvas tổng
        canvas = np.ones((self.total_height, self.total_width, 3), dtype=np.uint8) * 20

        # Lấy tất cả frame
        frames = camera_manager.get_all_frames()

        # Hiển thị từng camera theo grid
        for idx, cam_id in enumerate(selected_cameras):
            if idx >= self.grid_size[0] * self.grid_size[1]:
                break

            if cam_id in frames and frames[cam_id] is not None:
                frame = frames[cam_id].copy()

                # Tính vị trí trong grid
                row = idx // self.grid_size[1]
                col = idx % self.grid_size[1]

                x = self.margin + col * (self.cell_width + self.margin)
                y = self.margin + row * (self.cell_height + self.margin)

                # Resize frame về kích thước cell
                frame = cv2.resize(frame, (self.cell_width, self.cell_height))

                # Vẽ border
                cv2.rectangle(canvas,
                            (x - self.padding, y - self.padding),
                            (x + self.cell_width + self.padding,
                             y + self.cell_height + self.padding),
                            (100, 100, 150), 2)

                # Đặt frame lên canvas
                canvas[y:y+self.cell_height, x:x+self.cell_width] = frame

                # Thêm thông tin camera
                if self.show_info:
                    cam_info = camera_manager.get_camera_info(cam_id)
                    if cam_info:
                        # Name
                        cv2.putText(canvas, cam_info['name'][:20],
                                  (x + 5, y + 20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                        # Status indicator
                        status_color = (0, 255, 0) if cam_info['active'] else (0, 0, 255)
                        status_text = "LIVE" if cam_info['active'] else "OFF"
                        cv2.putText(canvas, status_text,
                                  (x + self.cell_width - 50, y + 20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)

                        # Resolution
                        res_text = f"{cam_info['resolution'][0]}x{cam_info['resolution'][1]}"
                        cv2.putText(canvas, res_text,
                                  (x + 5, y + self.cell_height - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            else:
                # Camera không có frame - hiển thị placeholder
                row = idx // self.grid_size[1]
                col = idx % self.grid_size[1]

                x = self.margin + col * (self.cell_width + self.margin)
                y = self.margin + row * (self.cell_height + self.margin)

                # Vẽ placeholder
                cv2.rectangle(canvas,
                            (x, y),
                            (x + self.cell_width, y + self.cell_height),
                            (50, 50, 50), -1)

                cv2.putText(canvas, "NO SIGNAL",
                          (x + self.cell_width//2 - 40, y + self.cell_height//2),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)

        # Hiển thị tổng số camera
        cv2.putText(canvas, f"Cameras: {len(selected_cameras)}/{self.grid_size[0]*self.grid_size[1]}",
                  (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 255), 1)

        # Hiển thị canvas
        cv2.imshow(self.window_name, canvas)

        # Xử lý phím
        key = cv2.waitKey(1) & 0xFF
        return key

    def update_grid_size(self, rows, cols):
        """Cập nhật kích thước grid"""
        self.grid_size = (rows, cols)
        self.total_width = (self.cell_width + self.margin) * cols + self.margin
        self.total_height = (self.cell_height + self.margin) * rows + self.margin
        cv2.resizeWindow(self.window_name, self.total_width, self.total_height)


class CameraSelectorUI:
    """Giao diện chọn camera để hiển thị"""

    def __init__(self, camera_manager):
        self.camera_manager = camera_manager
        self.selected_cameras = []
        self.max_cameras = 4  # Số camera tối đa có thể hiển thị

    def show_selection_ui(self):
        """Hiển thị UI chọn camera"""
        window_name = "Chọn Camera"
        width, height = 600, 400

        canvas = np.ones((height, width, 3), dtype=np.uint8) * 40
        all_cameras = self.camera_manager.database.get_database().get_all_cameras()
        active_cameras = [cam.id for cam in all_cameras if cam.enabled]

        running = True
        selected_idx = 0

        while running:
            canvas = np.ones((height, width, 3), dtype=np.uint8) * 40

            # Title
            cv2.putText(canvas, "CHỌN CAMERA HIỂN THỊ", (width//2 - 150, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

            cv2.putText(canvas, f"Đã chọn: {len(self.selected_cameras)}/{self.max_cameras}",
                       (width//2 - 80, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 255), 1)

            # List cameras
            y_start = 100
            for i, cam in enumerate(all_cameras):
                is_selected = i == selected_idx
                is_in_selection = cam.id in self.selected_cameras
                is_active = cam.id in active_cameras

                # Colors
                bg_color = (70, 70, 120) if is_selected else (50, 50, 80)
                name_color = (0, 255, 255) if is_in_selection else (255, 255, 255)
                status_color = (0, 255, 0) if is_active else (100, 100, 100)

                # Draw item
                cv2.rectangle(canvas, (50, y_start + i*40), (width-50, y_start + i*40 + 35),
                             bg_color, -1)

                # Camera name with checkbox
                checkbox = "[✓]" if is_in_selection else "[ ]"
                display_text = f"{checkbox} {cam.name}"
                cv2.putText(canvas, display_text, (70, y_start + i*40 + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, name_color, 1)

                # Camera type and status
                type_text = f"{cam.camera_type.value}"
                if cam.ip_address:
                    type_text += f" | {cam.ip_address}"

                cv2.putText(canvas, type_text, (300, y_start + i*40 + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

                # Status
                status_text = "●" if is_active else "○"
                cv2.putText(canvas, status_text, (width - 80, y_start + i*40 + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

            # Selected cameras preview
            if self.selected_cameras:
                cv2.putText(canvas, "Camera đã chọn:", (50, height - 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

                selected_names = []
                for cam_id in self.selected_cameras:
                    cam = self.camera_manager.database.get_database().get_camera(cam_id)
                    if cam:
                        selected_names.append(cam.name[:15])

                preview_text = ", ".join(selected_names)
                cv2.putText(canvas, preview_text, (50, height - 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)

            # Instructions
            cv2.putText(canvas, "SPACE: Chọn/Bỏ chọn | ENTER: Xác nhận | ESC: Hủy | MŨI TÊN: Di chuyển",
                       (50, height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

            cv2.imshow(window_name, canvas)
            key = cv2.waitKey(30) & 0xFF

            if key == 27:  # ESC
                self.selected_cameras = []
                running = False
            elif key == 13:  # ENTER
                if self.selected_cameras:
                    running = False
            elif key == 32 and all_cameras:  # SPACE
                cam = all_cameras[selected_idx]
                if cam.id in self.selected_cameras:
                    self.selected_cameras.remove(cam.id)
                else:
                    if len(self.selected_cameras) < self.max_cameras:
                        self.selected_cameras.append(cam.id)
            elif key == 82 and all_cameras:  # Up arrow
                selected_idx = max(0, selected_idx - 1)
            elif key == 84 and all_cameras:  # Down arrow
                selected_idx = min(len(all_cameras) - 1, selected_idx + 1)

        cv2.destroyWindow(window_name)
        return self.selected_cameras if self.selected_cameras else None