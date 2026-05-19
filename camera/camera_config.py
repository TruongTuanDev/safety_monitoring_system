"""
camera_config.py - Cấu hình camera đơn giản
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class CameraType(Enum):
    WEBCAM = "webcam"
    IP_CAMERA = "ip_camera"
    IPHONE = "iphone"
    ANDROID = "android"
    RTSP = "rtsp"

@dataclass
class CameraConfig:
    id: str
    name: str
    camera_type: CameraType
    source: str  # 0,1,2 cho webcam hoặc URL
    ip_address: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    resolution: tuple = (640, 480)
    fps: int = 30  # THÊM TRƯỜNG NÀY
    enabled: bool = True
    position_x: int = 0
    position_y: int = 0
    width: int = 320
    height: int = 240

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'camera_type': self.camera_type.value,
            'source': self.source,
            'ip_address': self.ip_address,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'resolution': list(self.resolution),
            'fps': self.fps,  # THÊM VÀO ĐÂY
            'enabled': self.enabled,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'width': self.width,
            'height': self.height
        }

    @classmethod
    def from_dict(cls, data):
        # Loại bỏ các trường không cần thiết từ MongoDB
        data = data.copy()

        # Xóa _id nếu có
        if '_id' in data:
            if 'id' not in data or not data['id']:
                data['id'] = str(data['_id'])
            del data['_id']

        # Chuyển đổi camera_type
        data['camera_type'] = CameraType(data['camera_type'])

        # Chuyển đổi resolution
        if 'resolution' in data and isinstance(data['resolution'], list):
            data['resolution'] = tuple(data['resolution'])

        # Đảm bảo có fps, mặc định là 30
        if 'fps' not in data:
            data['fps'] = 30

        # Loại bỏ các trường không thuộc class
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)
