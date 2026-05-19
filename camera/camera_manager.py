"""
Camera stream management.
"""

from __future__ import annotations

import threading
import time
from typing import Dict, Optional

import cv2

from .camera_config import CameraConfig, CameraType
from .camera_database import CameraDatabase


class CameraStream:
    def __init__(self, camera_config: CameraConfig):
        self.config = camera_config
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.last_frame_time = None
        self.frames_received = 0

    def _build_source(self):
        if self.config.camera_type == CameraType.WEBCAM:
            return int(self.config.source) if str(self.config.source).isdigit() else self.config.source

        if self.config.camera_type == CameraType.RTSP:
            return self.config.source

        if self.config.username and self.config.password:
            return (
                f"http://{self.config.username}:{self.config.password}"
                f"@{self.config.ip_address}:{self.config.port}/video"
            )
        return f"http://{self.config.ip_address}:{self.config.port}/video"

    def start(self):
        try:
            self.cap = cv2.VideoCapture(self._build_source())
            if not self.cap.isOpened():
                print(f"Cannot open camera: {self.config.name}")
                return False

            width, height = self.config.resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)

            self.running = True
            self.thread = threading.Thread(target=self._update_frame, daemon=True)
            self.thread.start()
            print(f"Camera connected: {self.config.name}")
            return True
        except Exception as e:
            print(f"Camera error {self.config.name}: {e}")
            return False

    def _update_frame(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = frame
                self.frames_received += 1
                self.last_frame_time = time.time()
            else:
                time.sleep(0.1)

    def get_frame(self):
        return self.frame

    def is_active(self):
        return self.running and self.frame is not None

    def get_info(self):
        resolution = self.config.resolution
        if self.frame is not None:
            resolution = (self.frame.shape[1], self.frame.shape[0])
        return {
            "id": self.config.id,
            "name": self.config.name,
            "active": self.is_active(),
            "frames_received": self.frames_received,
            "last_frame_time": self.last_frame_time,
            "resolution": resolution,
            "camera_type": self.config.camera_type.value,
        }

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        if self.cap:
            self.cap.release()
        print(f"Camera stopped: {self.config.name}")


class CameraManager:
    def __init__(self, mongo_uri: str = "mongodb://localhost:27017", db_name: str = "safety_monitoring"):
        self.database = CameraDatabase(mongo_uri, db_name)
        self.streams: Dict[str, CameraStream] = {}
        self.load_cameras()

    def load_cameras(self):
        cameras = self.database.get_all_cameras()
        print(f"Starting {len(cameras)} camera(s)")
        for camera in cameras:
            if camera.enabled:
                self.add_camera_stream(camera)

    def add_camera_stream(self, camera: CameraConfig) -> bool:
        if camera.id in self.streams:
            return False

        stream = CameraStream(camera)
        if stream.start():
            self.streams[camera.id] = stream
            return True
        return False

    def get_camera_frame(self, camera_id: str):
        stream = self.streams.get(camera_id)
        return stream.get_frame() if stream else None

    def get_all_frames(self):
        return {camera_id: stream.get_frame() for camera_id, stream in self.streams.items()}

    def get_camera_info(self, camera_id: str):
        stream = self.streams.get(camera_id)
        if stream:
            return stream.get_info()

        camera = self.database.get_camera(camera_id)
        if not camera:
            return None

        return {
            "id": camera.id,
            "name": camera.name,
            "active": False,
            "frames_received": 0,
            "last_frame_time": None,
            "resolution": camera.resolution,
            "camera_type": camera.camera_type.value,
        }

    def get_all_camera_info(self):
        return [self.get_camera_info(camera.id) for camera in self.get_all_cameras()]

    def get_all_cameras(self):
        return self.database.get_all_cameras()

    def add_new_camera(
        self,
        name: str,
        camera_type: str,
        ip: str = None,
        port: int = None,
        source: str = "0",
        username: str = None,
        password: str = None,
        resolution=(640, 480),
        fps: int = 30,
    ) -> bool:
        import uuid

        camera = CameraConfig(
            id=f"cam_{uuid.uuid4().hex[:8]}",
            name=name,
            camera_type=CameraType(camera_type),
            source=str(source),
            ip_address=ip,
            port=port,
            username=username,
            password=password,
            resolution=tuple(resolution),
            fps=fps,
            position_x=0,
            position_y=0,
        )

        result = self.database.add_camera(camera)
        if isinstance(result, dict) and not result.get("success"):
            print(result.get("message", "Add camera failed"))
            return False
        return self.add_camera_stream(camera)

    def delete_camera(self, camera_id: str) -> bool:
        stream = self.streams.pop(camera_id, None)
        if stream:
            stream.stop()
        return self.database.delete_camera(camera_id)

    def get_database_stats(self):
        return self.database.get_stats()

    def get_recent_events(self, limit: int = 50):
        return self.database.get_recent_events(limit)

    def stop_all(self):
        for stream in list(self.streams.values()):
            stream.stop()
        self.streams.clear()
        self.database.close()
