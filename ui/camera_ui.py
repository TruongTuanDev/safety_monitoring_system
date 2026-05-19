"""
camera_ui.py - Giao diện thêm/sửa camera với MongoDB
"""
import cv2
import numpy as np
from typing import Optional, Callable
from datetime import datetime

try:
    from cameras.camera_config import CameraConfig, CameraType
    from cameras.camera_database_mongo import MongoCameraDatabase
    from cameras.camera_manager import CameraManager
except ImportError:
    # Cho phép chạy trong môi trường development
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from camera.camera_config import CameraConfig, CameraType
    from camera.camera_database_mongo import MongoCameraDatabase
    from camera.camera_manager import CameraManager
class CameraConfigUI:
    """Giao diện cấu hình camera với MongoDB"""

    def __init__(self, window_name="Camera Configuration", width=600, height=500):
        self.window_name = window_name
        self.width = width
        self.height = height
        self.canvas = np.ones((height, width, 3), dtype=np.uint8) * 40
        self.running = False
        self.callback = None

        # Form fields
        self.fields = {
            'name': {'label': 'Tên camera*:', 'value': '', 'y': 80, 'required': True},
            'type': {'label': 'Loại camera*:', 'value': 'webcam', 'options': [
                ('Webcam', 'webcam'),
                ('iPhone (DroidCam)', 'iphone'),
                ('Android (IP Webcam)', 'android'),
                ('IP Camera', 'ip_camera'),
                ('RTSP Stream', 'rtsp')
            ], 'y': 120, 'required': True},
            'source': {'label': 'Nguồn (0,1,2...):', 'value': '0', 'y': 160, 'required': False},
            'ip': {'label': 'IP Address:', 'value': '192.168.1.100', 'y': 200, 'required': False},
            'port': {'label': 'Port:', 'value': '4747', 'y': 240, 'required': False},
            'username': {'label': 'Username:', 'value': '', 'y': 280, 'required': False},
            'password': {'label': 'Password:', 'value': '', 'y': 320, 'required': False},
            'width': {'label': 'Width:', 'value': '640', 'y': 360, 'required': False},
            'height': {'label': 'Height:', 'value': '480', 'y': 400, 'required': False}
        }

        self.current_field = 0
        self.field_keys = list(self.fields.keys())
        self.editing = False

    def show(self, callback: Callable, existing_config: Optional[CameraConfig] = None):
        """Hiển thị giao diện cấu hình"""
        self.running = True
        self.callback = callback

        # Nếu có config cũ, điền vào form
        if existing_config:
            self._load_config(existing_config)

        cv2.namedWindow(self.window_name)
        cv2.resizeWindow(self.window_name, self.width, self.height)

        while self.running:
            self._draw_ui()
            key = cv2.waitKey(30) & 0xFF

            if key == 27:  # ESC
                self.running = False
                callback(None)  # Hủy
            elif key == 13:  # Enter
                if self._validate_form():
                    self._save_and_exit()
            elif key == 9:  # Tab
                self.current_field = (self.current_field + 1) % len(self.field_keys)
            elif key == ord('+') or key == ord('='):
                self._change_field_value(1)
            elif key == ord('-'):
                self._change_field_value(-1)
            elif key in [81, 83, 84, 82]:  # Arrow keys
                self._handle_arrow_keys(key)
            elif key >= 32 and key <= 126:  # Printable characters
                self._handle_text_input(chr(key))
            elif key == 8:  # Backspace
                self._handle_backspace()

        cv2.destroyWindow(self.window_name)

    def _validate_form(self) -> bool:
        """Validate form data"""
        current_type = self.fields['type']['value']

        # Kiểm tra required fields
        if not self.fields['name']['value'].strip():
            self._show_error("Vui lòng nhập tên camera")
            return False

        # Kiểm tra theo loại camera
        if current_type in ['iphone', 'android', 'ip_camera', 'rtsp']:
            if not self.fields['ip']['value'].strip():
                self._show_error("Vui lòng nhập IP Address")
                return False

            if not self.fields['port']['value'].strip():
                self._show_error("Vui lòng nhập Port")
                return False

        # Kiểm tra số
        try:
            if self.fields['width']['value']:
                int(self.fields['width']['value'])
            if self.fields['height']['value']:
                int(self.fields['height']['value'])
            if self.fields['port']['value']:
                int(self.fields['port']['value'])
        except ValueError:
            self._show_error("Width, Height, Port phải là số")
            return False

        return True

    def _show_error(self, message: str):
        """Hiển thị lỗi"""
        print(f"❌ {message}")
        # Có thể thêm hiển thị trên UI

    def _save_and_exit(self):
        """Lưu và thoát"""
        try:
            # Tạo CameraConfig từ form data
            camera_type = CameraType(self.fields['type']['value'])

            # Xử lý source field
            source = self.fields['source']['value']
            if camera_type == CameraType.WEBCAM and source.isdigit():
                source = int(source)

            config_dict = {
                'name': self.fields['name']['value'],
                'camera_type': camera_type.value,
                'source': str(source),
                'ip_address': self.fields['ip']['value'] if self.fields['ip']['value'] else None,
                'port': int(self.fields['port']['value']) if self.fields['port']['value'] else None,
                'username': self.fields['username']['value'] if self.fields['username']['value'] else None,
                'password': self.fields['password']['value'] if self.fields['password']['value'] else None,
                'resolution': (int(self.fields['width']['value']),
                             int(self.fields['height']['value'])),
                'enabled': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.running = False
            if self.callback:
                self.callback(config_dict)

        except Exception as e:
            print(f"❌ Lỗi tạo config: {e}")

def show_camera_stats_ui(camera_manager):
    """Hiển thị thống kê camera từ MongoDB"""
    window_name = "Camera Statistics"
    width, height = 600, 400

    canvas = np.ones((height, width, 3), dtype=np.uint8) * 30

    # Lấy thống kê
    stats = camera_manager.get_database_stats()
    recent_events = camera_manager.get_recent_events(10)

    running = True

    while running:
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 30

        # Title
        cv2.putText(canvas, "📊 THỐNG KÊ CAMERA", (width//2 - 120, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

        # Stats
        y_offset = 80
        cv2.putText(canvas, f"Tổng số camera: {stats.get('total_cameras', 0)}",
                   (50, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 1)

        cv2.putText(canvas, f"Đang bật: {stats.get('enabled_cameras', 0)} | Đang tắt: {stats.get('disabled_cameras', 0)}",
                   (50, y_offset + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 1)

        # Camera by type
        y_offset += 60
        cv2.putText(canvas, "Phân loại camera:",
                   (50, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

        type_y = y_offset + 25
        for cam_type, count in stats.get('by_type', {}).items():
            cv2.putText(canvas, f"  {cam_type}: {count}",
                       (70, type_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            type_y += 20

        # Recent events
        y_offset = type_y + 20
        cv2.putText(canvas, "Sự kiện gần đây:",
                   (50, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

        event_y = y_offset + 25
        for i, event in enumerate(recent_events[:5]):
            event_text = f"{event.get('event_type', 'Unknown')}: {event.get('message', '')[:30]}..."
            cv2.putText(canvas, event_text,
                       (70, event_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                       (150, 150, 150) if i % 2 == 0 else (180, 180, 180), 1)
            event_y += 15

        # Instructions
        cv2.putText(canvas, "Nhấn ESC để thoát",
                   (width//2 - 60, height - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        cv2.imshow(window_name, canvas)
        key = cv2.waitKey(30) & 0xFF

        if key == 27:  # ESC
            running = False

    cv2.destroyWindow(window_name)


"""
camera_ui.py - Giao diện quản lý camera với MongoDB
"""


def show_camera_list_ui(camera_manager, on_camera_select=None, on_add_camera=None):
    """Hiển thị danh sách camera với UI đẹp và MongoDB"""
    window_name = "📷 Quản lý Camera"
    width, height = 800, 600

    # Tạo canvas
    canvas = np.ones((height, width, 3), dtype=np.uint8) * 30

    # Lấy danh sách camera từ database
    cameras = camera_manager.database.get_database().get_all_cameras()
    active_cameras_info = camera_manager.get_all_camera_info()

    # Tạo dict để tra cứu nhanh trạng thái
    active_status = {info['id']: info for info in active_cameras_info}

    running = True
    selected_index = 0
    view_mode = 'all'  # 'all', 'active', 'inactive'
    filter_text = ""

    # Lấy thống kê
    stats = camera_manager.get_database_stats()

    while running:
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 30

        # Title
        cv2.putText(canvas, "QUẢN LÝ CAMERA - MongoDB", (width // 2 - 150, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)

        # Stats bar
        stats_text = f"Tổng: {len(cameras)} | Đang hoạt động: {len(active_cameras_info)}"
        cv2.rectangle(canvas, (20, 70), (width - 20, 100), (40, 40, 60), -1)
        cv2.putText(canvas, stats_text, (width // 2 - 100, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 255), 1)

        # Filter bar
        cv2.putText(canvas, "Lọc:", (30, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # Filter buttons
        filter_buttons = [
            ("Tất cả", 'all', (100, 120)),
            ("Đang hoạt động", 'active', (180, 120)),
            ("Ngừng hoạt động", 'inactive', (330, 120))
        ]

        for text, mode, pos in filter_buttons:
            color = (0, 200, 255) if view_mode == mode else (100, 100, 150)
            cv2.rectangle(canvas, (pos[0], pos[1]), (pos[0] + 140, pos[1] + 25), color, -1)
            cv2.putText(canvas, text, (pos[0] + 10, pos[1] + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Search box
        cv2.putText(canvas, "Tìm kiếm:", (500, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        cv2.rectangle(canvas, (580, 120), (750, 145), (60, 60, 80), -1)
        cv2.putText(canvas, filter_text + "█", (590, 138),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # Filter cameras
        filtered_cameras = []
        for cam in cameras:
            # Filter by status
            if view_mode == 'active' and cam.id not in active_status:
                continue
            elif view_mode == 'inactive' and cam.id in active_status:
                continue

            # Filter by search text
            if filter_text and filter_text.lower() not in cam.name.lower():
                continue

            filtered_cameras.append(cam)

        # Camera list
        y_start = 160
        items_per_page = 6
        start_idx = max(0, selected_index - items_per_page + 1)
        end_idx = min(len(filtered_cameras), start_idx + items_per_page)

        for i in range(start_idx, end_idx):
            cam = filtered_cameras[i]
            list_idx = i - start_idx
            is_selected = i == selected_index
            is_active = cam.id in active_status
            active_info = active_status.get(cam.id, {})

            # Calculate position
            y = y_start + list_idx * 70

            # Background color
            bg_color = (70, 70, 120) if is_selected else (50, 50, 80)
            status_color = (0, 255, 0) if is_active else (100, 100, 100)

            # Draw item background
            cv2.rectangle(canvas, (30, y), (width - 30, y + 65), bg_color, -1)
            cv2.rectangle(canvas, (30, y), (width - 30, y + 65),
                          (100, 100, 150), 2 if is_selected else 1)

            # Camera icon based on type
            icon = "📷"
            if cam.camera_type.value == 'iphone':
                icon = "📱"
            elif cam.camera_type.value == 'android':
                icon = "🤖"
            elif cam.camera_type.value == 'ip_camera':
                icon = "🌐"
            elif cam.camera_type.value == 'rtsp':
                icon = "🔗"

            # Camera name and icon
            cv2.putText(canvas, f"{icon} {cam.name}", (50, y + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Camera details
            details = f"{cam.camera_type.value.upper()}"
            if cam.ip_address:
                details += f" | {cam.ip_address}:{cam.port}"
            else:
                details += f" | Source: {cam.source}"

            cv2.putText(canvas, details, (50, y + 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

            # Resolution
            res_text = f"{cam.resolution[0]}x{cam.resolution[1]}"
            cv2.putText(canvas, res_text, (width - 200, y + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

            # Status indicator
            status_text = "● ĐANG HOẠT ĐỘNG" if is_active else "○ NGỪNG HOẠT ĐỘNG"
            if is_active and active_info.get('frames_received'):
                fps_text = f" | Frames: {active_info['frames_received']}"
                status_text += fps_text

            status_x = width - 450
            cv2.putText(canvas, status_text, (status_x, y + 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)

        # Page info
        if len(filtered_cameras) > 0:
            page_info = f"Camera {selected_index + 1}/{len(filtered_cameras)}"
            cv2.putText(canvas, page_info, (width // 2 - 50, y_start + items_per_page * 70 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 255), 1)
        else:
            cv2.putText(canvas, "Không tìm thấy camera nào", (width // 2 - 100, y_start + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 1)

        # Action buttons area
        button_y = height - 100
        cv2.rectangle(canvas, (20, button_y), (width - 20, button_y + 70), (40, 40, 60), -1)

        # Action buttons
        buttons = [
            ("[A] Thêm mới", (50, button_y + 25)),
            ("[ENTER] Chọn/Chỉnh sửa", (200, button_y + 25)),
            ("[D] Xóa", (400, button_y + 25)),
            ("[R] Làm mới", (500, button_y + 25)),
            ("[S] Thống kê", (650, button_y + 25))
        ]

        for text, pos in buttons:
            cv2.putText(canvas, text, pos,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)

        # Quick stats
        stats_y = button_y + 50
        type_stats = stats.get('by_type', {})
        stats_text = " | ".join([f"{k}: {v}" for k, v in type_stats.items()])
        cv2.putText(canvas, stats_text[:80], (50, stats_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 200), 1)

        # Instructions
        cv2.putText(canvas, "MŨI TÊN: Di chuyển | TAB: Đổi chế độ lọc | ESC: Thoát",
                    (50, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

        cv2.imshow(window_name, canvas)
        key = cv2.waitKey(30) & 0xFF

        if key == 27:  # ESC
            running = False
        elif key == 13 and filtered_cameras:  # ENTER
            if on_camera_select and filtered_cameras:
                on_camera_select(filtered_cameras[selected_index])
                running = False
        elif key == ord('a') or key == ord('A'):  # Add
            if on_add_camera:
                on_add_camera()
                # Refresh list
                cameras = camera_manager.database.get_database().get_all_cameras()
                active_cameras_info = camera_manager.get_all_camera_info()
                active_status = {info['id']: info for info in active_cameras_info}
        elif key == ord('d') or key == ord('D') and filtered_cameras:  # Delete
            cam_to_delete = filtered_cameras[selected_index]
            # Show confirmation dialog
            confirm_canvas = np.ones((200, 500, 3), dtype=np.uint8) * 40

            cv2.putText(confirm_canvas, "XÁC NHẬN XÓA CAMERA", (150, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(confirm_canvas, f"Bạn có chắc muốn xóa camera:", (50, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(confirm_canvas, f"'{cam_to_delete.name}'?", (50, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 100), 2)
            cv2.putText(confirm_canvas, "Y - Xóa | N - Hủy", (150, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            cv2.imshow("Xác nhận xóa", confirm_canvas)
            confirm_key = cv2.waitKey(0) & 0xFF
            cv2.destroyWindow("Xác nhận xóa")

            if confirm_key == ord('y') or confirm_key == ord('Y'):
                success = camera_manager.delete_camera(cam_to_delete.id)
                if success:
                    print(f"✅ Đã xóa camera: {cam_to_delete.name}")
                    # Refresh list
                    cameras = camera_manager.database.get_database().get_all_cameras()
                    active_cameras_info = camera_manager.get_all_camera_info()
                    active_status = {info['id']: info for info in active_cameras_info}

                    # Adjust selected index
                    if selected_index >= len(filtered_cameras):
                        selected_index = max(0, len(filtered_cameras) - 1)
        elif key == ord('r') or key == ord('R'):  # Refresh
            cameras = camera_manager.database.get_database().get_all_cameras()
            active_cameras_info = camera_manager.get_all_camera_info()
            active_status = {info['id']: info for info in active_cameras_info}
            print("🔄 Đã làm mới danh sách camera")
        elif key == ord('s') or key == ord('S'):  # Stats
            show_camera_stats_ui(camera_manager)
        elif key == 9:  # TAB - Switch filter mode
            modes = ['all', 'active', 'inactive']
            current_idx = modes.index(view_mode)
            view_mode = modes[(current_idx + 1) % len(modes)]
        elif key == 82 and filtered_cameras:  # Up arrow
            selected_index = max(0, selected_index - 1)
        elif key == 84 and filtered_cameras:  # Down arrow
            selected_index = min(len(filtered_cameras) - 1, selected_index + 1)
        elif key == 81:  # Left arrow - Page up
            selected_index = max(0, selected_index - items_per_page)
        elif key == 83:  # Right arrow - Page down
            selected_index = min(len(filtered_cameras) - 1, selected_index + items_per_page)
        elif key == 8:  # Backspace
            filter_text = filter_text[:-1]
        elif 32 <= key <= 126:  # Printable characters
            filter_text += chr(key)

    cv2.destroyWindow(window_name)
    return None


def show_camera_details_ui(camera_manager, camera_id):
    """Hiển thị chi tiết camera với thông tin từ MongoDB"""
    window_name = "Chi tiết Camera"
    width, height = 700, 500

    # Lấy thông tin camera
    camera = camera_manager.database.get_database().get_camera(camera_id)
    if not camera:
        print(f"❌ Không tìm thấy camera với ID: {camera_id}")
        return

    # Lấy events của camera
    events = camera_manager.database.get_database().get_camera_events(camera_id, 20)

    canvas = np.ones((height, width, 3), dtype=np.uint8) * 30

    running = True
    current_tab = 'info'  # 'info', 'events', 'preview'

    while running:
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 30

        # Title
        cv2.putText(canvas, f"📋 CHI TIẾT CAMERA", (width // 2 - 120, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 255), 2)
        cv2.putText(canvas, camera.name, (width // 2 - 100, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        # Tab selector
        tabs = [
            ("📝 Thông tin", 'info', (50, 100)),
            ("📊 Sự kiện", 'events', (200, 100)),
            ("👁️ Xem trước", 'preview', (350, 100))
        ]

        for text, tab, pos in tabs:
            color = (0, 200, 255) if current_tab == tab else (80, 80, 100)
            cv2.rectangle(canvas, (pos[0], pos[1]), (pos[0] + 140, pos[1] + 30), color, -1)
            cv2.putText(canvas, text, (pos[0] + 10, pos[1] + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Content area
        content_y = 140

        if current_tab == 'info':
            # Camera information
            info_lines = [
                f"ID: {camera.id}",
                f"Loại: {camera.camera_type.value}",
                f"Nguồn: {camera.source}",
                f"IP: {camera.ip_address or 'N/A'}",
                f"Port: {camera.port or 'N/A'}",
                f"Độ phân giải: {camera.resolution[0]}x{camera.resolution[1]}",
                f"FPS: {camera.fps}",
                f"Trạng thái: {'✅ Bật' if camera.enabled else '❌ Tắt'}"
            ]

            y = content_y + 30
            for line in info_lines:
                cv2.putText(canvas, line, (60, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1)
                y += 30

        elif current_tab == 'events':
            # Events list
            cv2.putText(canvas, "LỊCH SỬ SỰ KIỆN", (width // 2 - 80, content_y + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1)

            if events:
                y = content_y + 70
                for i, event in enumerate(events[:10]):
                    timestamp = event.get('timestamp', '')
                    if isinstance(timestamp, str):
                        timestamp = timestamp[:19]

                    event_type = event.get('event_type', 'Unknown')
                    message = event.get('message', '')[:40]

                    # Color based on event type
                    if 'error' in event_type:
                        color = (0, 0, 255)
                    elif 'connected' in event_type:
                        color = (0, 255, 0)
                    else:
                        color = (200, 200, 200)

                    line = f"[{timestamp}] {event_type}: {message}"
                    cv2.putText(canvas, line, (50, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                    y += 25
            else:
                cv2.putText(canvas, "Không có sự kiện nào", (width // 2 - 100, content_y + 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

        elif current_tab == 'preview':
            # Camera preview
            cv2.putText(canvas, "XEM TRƯỚC CAMERA", (width // 2 - 100, content_y + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1)

            # Try to get frame
            frame = camera_manager.get_camera_frame(camera_id)

            if frame is not None:
                # Resize frame to fit
                preview_width = 400
                preview_height = 300
                frame_resized = cv2.resize(frame, (preview_width, preview_height))

                # Place on canvas
                x_offset = (width - preview_width) // 2
                y_offset = content_y + 50

                canvas[y_offset:y_offset + preview_height, x_offset:x_offset + preview_width] = frame_resized

                # Status
                cv2.putText(canvas, "✅ ĐANG PHÁT TRỰC TIẾP",
                            (width // 2 - 100, y_offset + preview_height + 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            else:
                cv2.putText(canvas, "❌ KHÔNG CÓ TÍN HIỆU",
                            (width // 2 - 100, content_y + 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1)
                cv2.putText(canvas, "Camera có thể đang tắt hoặc mất kết nối",
                            (width // 2 - 150, content_y + 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

        # Instructions
        cv2.putText(canvas, "TAB: Đổi tab | 1/2/3: Chọn tab | ESC: Thoát",
                    (50, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

        cv2.imshow(window_name, canvas)
        key = cv2.waitKey(30) & 0xFF

        if key == 27:  # ESC
            running = False
        elif key == 9:  # TAB
            tabs_order = ['info', 'events', 'preview']
            current_idx = tabs_order.index(current_tab)
            current_tab = tabs_order[(current_idx + 1) % len(tabs_order)]
        elif key == ord('1'):
            current_tab = 'info'
        elif key == ord('2'):
            current_tab = 'events'
        elif key == ord('3'):
            current_tab = 'preview'

    cv2.destroyWindow(window_name)
