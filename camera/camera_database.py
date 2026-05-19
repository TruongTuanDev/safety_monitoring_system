"""
Compatibility exports for camera persistence.

The actual implementation lives in `camera_database_mongo.py`.
"""

from .camera_database_mongo import CameraDatabase, FallbackCameraDatabase, MongoCameraDatabase

__all__ = ["CameraDatabase", "FallbackCameraDatabase", "MongoCameraDatabase"]
