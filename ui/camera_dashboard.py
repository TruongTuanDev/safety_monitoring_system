"""
Dashboard UI for viewing multiple cameras and adding new ones.
"""

from __future__ import annotations

import time
from typing import List, Optional

import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk

from camera.camera_config import CameraConfig, CameraType


class CameraDashboard:
    def __init__(self, window_name="He Thong Giam Sat Cong Trinh"):
        self.window_name = window_name
        self.grid_columns = 3
        self.cell_width = 426
        self.cell_height = 320
        self.margin = 10
        self.last_mouse_click_time = 0
        self.click_cooldown = 0.5
        self.add_camera_clicked = False

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 960)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)

    def _mouse_callback(self, event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return

        current_time = time.time()
        if current_time - self.last_mouse_click_time < self.click_cooldown:
            return

        self.last_mouse_click_time = current_time
        self.add_camera_clicked = 1100 <= x <= 1250 and 20 <= y <= 60

    def calculate_grid_position(self, index: int):
        row = index // self.grid_columns
        col = index % self.grid_columns
        x = col * (self.cell_width + self.margin) + self.margin
        y = row * (self.cell_height + self.margin) + self.margin + 70
        return x, y

    def draw_camera_cell(self, canvas, camera: CameraConfig, frame, x: int, y: int):
        cv2.rectangle(canvas, (x, y), (x + self.cell_width, y + self.cell_height), (40, 40, 60), -1)
        cv2.rectangle(canvas, (x, y), (x + self.cell_width, y + self.cell_height), (100, 100, 150), 2)

        if frame is not None:
            try:
                frame_resized = cv2.resize(frame, (self.cell_width - 20, self.cell_height - 60))
                canvas[y + 10:y + 10 + frame_resized.shape[0], x + 10:x + 10 + frame_resized.shape[1]] = frame_resized
                cv2.rectangle(
                    canvas,
                    (x + 8, y + 8),
                    (x + 12 + frame_resized.shape[1], y + 12 + frame_resized.shape[0]),
                    (0, 0, 0),
                    2,
                )
            except Exception as e:
                print(f"Frame render error: {e}")

        name_bg_y = y + 10
        cv2.rectangle(canvas, (x, name_bg_y), (x + self.cell_width, name_bg_y + 30), (60, 60, 80), -1)
        cv2.putText(canvas, camera.name, (x + 10, name_bg_y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        info_text = camera.camera_type.value
        if camera.ip_address:
            info_text += f" | {camera.ip_address}"
        cv2.putText(canvas, info_text, (x + 10, y + self.cell_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        status_text = "Online" if frame is not None else "Offline"
        status_color = (0, 255, 0) if frame is not None else (255, 100, 100)
        cv2.rectangle(canvas, (x + self.cell_width - 150, y + 10), (x + self.cell_width - 10, y + 35), (40, 40, 60), -1)
        cv2.putText(canvas, status_text, (x + self.cell_width - 140, y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, status_color, 1)
        return canvas

    def show_add_camera_dialog(self) -> Optional[dict]:
        result = {"value": None}

        root = tk.Tk()
        root.withdraw()

        dialog = tk.Toplevel(root)
        dialog.title("Them Camera")
        dialog.geometry("420x380")
        dialog.resizable(False, False)
        dialog.grab_set()

        fields = {
            "name": tk.StringVar(value=""),
            "type": tk.StringVar(value=CameraType.WEBCAM.value),
            "source": tk.StringVar(value="0"),
            "ip": tk.StringVar(value=""),
            "port": tk.StringVar(value="4747"),
            "username": tk.StringVar(value=""),
            "password": tk.StringVar(value=""),
        }

        ttk.Label(dialog, text="Them camera moi", font=("Segoe UI", 12, "bold")).pack(pady=(15, 10))
        form = ttk.Frame(dialog, padding=12)
        form.pack(fill="both", expand=True)

        field_order = ["name", "type", "source", "ip", "port", "username", "password"]
        widgets = {}
        labels = {
            "name": "Ten camera",
            "type": "Loai",
            "source": "Source",
            "ip": "IP",
            "port": "Port",
            "username": "Username",
            "password": "Password",
        }

        for row, key in enumerate(field_order):
            ttk.Label(form, text=labels[key]).grid(row=row, column=0, sticky="w", pady=6)
            if key == "type":
                widgets[key] = ttk.Combobox(
                    form,
                    textvariable=fields[key],
                    values=[camera_type.value for camera_type in CameraType],
                    state="readonly",
                    width=24,
                )
            else:
                widgets[key] = ttk.Entry(form, textvariable=fields[key], show="*" if key == "password" else "", width=28)
            widgets[key].grid(row=row, column=1, sticky="ew", pady=6)

        form.grid_columnconfigure(1, weight=1)

        def update_field_state(*_args):
            selected_type = fields["type"].get()
            is_webcam = selected_type == CameraType.WEBCAM.value
            widgets["source"].configure(state="normal" if is_webcam or selected_type == CameraType.RTSP.value else "disabled")
            for key in ("ip", "port", "username", "password"):
                widgets[key].configure(state="disabled" if is_webcam else "normal")

        def submit():
            name = fields["name"].get().strip()
            camera_type = fields["type"].get()
            source = fields["source"].get().strip() or "0"
            ip = fields["ip"].get().strip() or None
            username = fields["username"].get().strip() or None
            password = fields["password"].get().strip() or None

            if not name:
                messagebox.showerror("Loi", "Ten camera khong duoc de trong", parent=dialog)
                return

            try:
                port = int(fields["port"].get().strip()) if fields["port"].get().strip() else None
            except ValueError:
                messagebox.showerror("Loi", "Port phai la so", parent=dialog)
                return

            if camera_type not in (CameraType.WEBCAM.value, CameraType.RTSP.value) and not ip:
                messagebox.showerror("Loi", "Camera mang can IP", parent=dialog)
                return

            result["value"] = {
                "name": name,
                "type": camera_type,
                "ip": ip,
                "port": port,
                "source": source,
                "username": username,
                "password": password,
            }
            dialog.destroy()

        button_bar = ttk.Frame(dialog, padding=(12, 0, 12, 12))
        button_bar.pack(fill="x")
        ttk.Button(button_bar, text="Luu", command=submit).pack(side="left")
        ttk.Button(button_bar, text="Huy", command=dialog.destroy).pack(side="right")

        fields["type"].trace_add("write", update_field_state)
        update_field_state()
        dialog.wait_window()
        root.destroy()
        return result["value"]

    def display(self, camera_manager, cameras: List[CameraConfig]) -> Optional[str]:
        canvas = np.ones((960, 1280, 3), dtype=np.uint8) * 30

        cv2.rectangle(canvas, (0, 0), (1280, 70), (40, 40, 60), -1)
        cv2.putText(canvas, "HE THONG GIAM SAT CONG TRINH", (400, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)
        cv2.putText(canvas, f"Camera: {len(cameras)}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 255), 1)

        cv2.rectangle(canvas, (1100, 20), (1250, 60), (40, 160, 40), -1)
        cv2.rectangle(canvas, (1100, 20), (1250, 60), (100, 200, 100), 2)
        cv2.putText(canvas, "THEM CAMERA", (1110, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        for i, camera in enumerate(cameras):
            x, y = self.calculate_grid_position(i)
            frame = camera_manager.get_camera_frame(camera.id)
            self.draw_camera_cell(canvas, camera, frame, x, y)

        cv2.putText(canvas, "Click THEM CAMERA hoac nhan phim A", (20, 950), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        cv2.imshow(self.window_name, canvas)

        if self.add_camera_clicked:
            self.add_camera_clicked = False
            return "add_camera"
        return None
