"""
Camera persistence with MongoDB primary storage and JSON fallback.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymongo
from bson import ObjectId
from pymongo.errors import ConnectionFailure, DuplicateKeyError

from .camera_config import CameraConfig


def _normalize_camera_doc(doc: Dict[str, Any]) -> CameraConfig:
    normalized = dict(doc)
    if "_id" in normalized:
        normalized["id"] = str(normalized["_id"])
        del normalized["_id"]
    return CameraConfig.from_dict(normalized)


class MongoCameraDatabase:
    def __init__(self, uri: str = "mongodb://localhost:27017", db_name: str = "safety_monitoring"):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.cameras_collection = None
        self.events_collection = None
        self.connect()

    def connect(self) -> bool:
        try:
            self.client = pymongo.MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
            )
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.cameras_collection = self.db["cameras"]
            self.events_collection = self.db["camera_events"]
            self._create_indexes()
            print("MongoDB camera database connected")
            return True
        except ConnectionFailure as e:
            print(f"MongoDB unavailable, using fallback storage: {e}")
            self.client = None
            return False
        except Exception as e:
            print(f"MongoDB initialization error: {e}")
            self.client = None
            return False

    def _create_indexes(self):
        self.cameras_collection.create_index([("name", pymongo.ASCENDING)], unique=True)
        self.cameras_collection.create_index([("enabled", pymongo.ASCENDING)])
        self.cameras_collection.create_index([("camera_type", pymongo.ASCENDING)])
        self.events_collection.create_index([("camera_id", pymongo.ASCENDING)])
        self.events_collection.create_index([("timestamp", pymongo.DESCENDING)])
        self.events_collection.create_index([("event_type", pymongo.ASCENDING)])

    def add_camera(self, camera: CameraConfig) -> Dict[str, Any]:
        try:
            payload = camera.to_dict()
            payload["created_at"] = datetime.now()
            payload["updated_at"] = datetime.now()
            result = self.cameras_collection.insert_one(payload)
            camera_id = str(result.inserted_id)
            self.log_event(
                camera_id=camera_id,
                event_type="camera_added",
                message=f"Added camera {camera.name}",
                data={"name": camera.name, "type": camera.camera_type.value},
            )
            return {"success": True, "id": camera_id, "message": f"Added camera {camera.name}"}
        except DuplicateKeyError:
            return {"success": False, "message": f"Camera '{camera.name}' already exists"}
        except Exception as e:
            print(f"Add camera error: {e}")
            return {"success": False, "message": str(e)}

    def update_camera(self, camera_id: str, camera: CameraConfig) -> bool:
        try:
            object_id = ObjectId(camera_id) if isinstance(camera_id, str) else camera_id
            payload = camera.to_dict()
            payload["updated_at"] = datetime.now()
            result = self.cameras_collection.update_one({"_id": object_id}, {"$set": payload})
            if result.modified_count > 0:
                self.log_event(camera_id, "camera_updated", f"Updated camera {camera.name}")
                return True
            return False
        except Exception as e:
            print(f"Update camera error: {e}")
            return False

    def delete_camera(self, camera_id: str) -> bool:
        try:
            object_id = ObjectId(camera_id) if isinstance(camera_id, str) else camera_id
            camera = self.cameras_collection.find_one({"_id": object_id})
            if not camera:
                return False
            result = self.cameras_collection.delete_one({"_id": object_id})
            if result.deleted_count > 0:
                self.log_event(str(object_id), "camera_deleted", f"Deleted camera {camera.get('name', 'Unknown')}")
                return True
            return False
        except Exception as e:
            print(f"Delete camera error: {e}")
            return False

    def get_camera(self, camera_id: str) -> Optional[CameraConfig]:
        try:
            object_id = ObjectId(camera_id) if isinstance(camera_id, str) else camera_id
            doc = self.cameras_collection.find_one({"_id": object_id})
            return _normalize_camera_doc(doc) if doc else None
        except Exception:
            return None

    def get_camera_by_name(self, name: str) -> Optional[CameraConfig]:
        try:
            doc = self.cameras_collection.find_one({"name": name})
            return _normalize_camera_doc(doc) if doc else None
        except Exception:
            return None

    def get_all_cameras(self) -> List[CameraConfig]:
        try:
            return [_normalize_camera_doc(doc) for doc in self.cameras_collection.find({}).sort("name", pymongo.ASCENDING)]
        except Exception as e:
            print(f"Get all cameras error: {e}")
            return []

    def get_enabled_cameras(self) -> List[CameraConfig]:
        try:
            return [_normalize_camera_doc(doc) for doc in self.cameras_collection.find({"enabled": True}).sort("name", pymongo.ASCENDING)]
        except Exception as e:
            print(f"Get enabled cameras error: {e}")
            return []

    def search_cameras(self, query: Dict[str, Any]) -> List[CameraConfig]:
        try:
            return [_normalize_camera_doc(doc) for doc in self.cameras_collection.find(query).sort("name", pymongo.ASCENDING)]
        except Exception as e:
            print(f"Search cameras error: {e}")
            return []

    def update_camera_status(self, camera_id: str, status: Dict[str, Any]) -> bool:
        try:
            object_id = ObjectId(camera_id) if isinstance(camera_id, str) else camera_id
            result = self.cameras_collection.update_one(
                {"_id": object_id},
                {"$set": {"status": status, "last_seen": datetime.now(), "updated_at": datetime.now()}},
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Update camera status error: {e}")
            return False

    def log_event(self, camera_id: str, event_type: str, message: str, data: Dict[str, Any] = None):
        try:
            self.events_collection.insert_one({
                "camera_id": camera_id,
                "event_type": event_type,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now(),
                "created_at": datetime.now(),
            })
        except Exception as e:
            print(f"Log event warning: {e}")

    def get_camera_events(self, camera_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            events = []
            cursor = self.events_collection.find({"camera_id": camera_id}).sort("timestamp", pymongo.DESCENDING).limit(limit)
            for event in cursor:
                event["_id"] = str(event["_id"])
                events.append(event)
            return events
        except Exception as e:
            print(f"Get camera events error: {e}")
            return []

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            events = []
            cursor = self.events_collection.find({}).sort("timestamp", pymongo.DESCENDING).limit(limit)
            for event in cursor:
                event["_id"] = str(event["_id"])
                events.append(event)
            return events
        except Exception as e:
            print(f"Get recent events error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        try:
            total = self.cameras_collection.count_documents({})
            enabled = self.cameras_collection.count_documents({"enabled": True})
            by_type = {}
            for row in self.cameras_collection.aggregate([{"$group": {"_id": "$camera_type", "count": {"$sum": 1}}}]):
                by_type[row["_id"]] = row["count"]
            return {
                "total_cameras": total,
                "enabled_cameras": enabled,
                "disabled_cameras": total - enabled,
                "by_type": by_type,
            }
        except Exception as e:
            print(f"Get stats error: {e}")
            return {}

    def close(self):
        if self.client:
            self.client.close()


class FallbackCameraDatabase:
    def __init__(self, db_file: str = "cameras_backup.json"):
        self.db_file = Path(db_file)
        self.cameras: Dict[str, CameraConfig] = {}
        self.events: List[Dict[str, Any]] = []
        self.load_cameras()

    def load_cameras(self):
        try:
            if self.db_file.exists():
                with self.db_file.open("r", encoding="utf-8") as file:
                    payload = json.load(file)
                for cam_data in payload.get("cameras", []):
                    camera = CameraConfig.from_dict(cam_data)
                    self.cameras[camera.id] = camera
                self.events = payload.get("events", [])
        except Exception as e:
            print(f"Fallback load error: {e}")

    def save_cameras(self) -> bool:
        try:
            payload = {
                "cameras": [camera.to_dict() for camera in self.cameras.values()],
                "events": self.events,
            }
            with self.db_file.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Fallback save error: {e}")
            return False

    def add_camera(self, camera: CameraConfig) -> Dict[str, Any]:
        if any(existing.name == camera.name for existing in self.cameras.values()):
            return {"success": False, "message": f"Camera '{camera.name}' already exists"}
        self.cameras[camera.id] = camera
        self.save_cameras()
        self.log_event(camera.id, "camera_added", f"Added camera {camera.name}")
        return {"success": True, "id": camera.id, "message": f"Added camera {camera.name}"}

    def update_camera(self, camera_id: str, camera: CameraConfig) -> bool:
        if camera_id not in self.cameras:
            return False
        self.cameras[camera_id] = camera
        self.save_cameras()
        self.log_event(camera_id, "camera_updated", f"Updated camera {camera.name}")
        return True

    def delete_camera(self, camera_id: str) -> bool:
        camera = self.cameras.pop(camera_id, None)
        if not camera:
            return False
        self.save_cameras()
        self.log_event(camera_id, "camera_deleted", f"Deleted camera {camera.name}")
        return True

    def get_camera(self, camera_id: str) -> Optional[CameraConfig]:
        return self.cameras.get(camera_id)

    def get_camera_by_name(self, name: str) -> Optional[CameraConfig]:
        return next((camera for camera in self.cameras.values() if camera.name == name), None)

    def get_all_cameras(self) -> List[CameraConfig]:
        return list(sorted(self.cameras.values(), key=lambda camera: camera.name.lower()))

    def get_enabled_cameras(self) -> List[CameraConfig]:
        return [camera for camera in self.get_all_cameras() if camera.enabled]

    def search_cameras(self, query: Dict[str, Any]) -> List[CameraConfig]:
        results = self.get_all_cameras()
        for key, value in query.items():
            results = [camera for camera in results if getattr(camera, key, None) == value]
        return results

    def update_camera_status(self, camera_id: str, status: Dict[str, Any]) -> bool:
        if camera_id not in self.cameras:
            return False
        self.log_event(camera_id, "camera_status", "Updated camera status", status)
        return True

    def log_event(self, camera_id: str, event_type: str, message: str, data: Dict[str, Any] = None):
        self.events.insert(0, {
            "camera_id": camera_id,
            "event_type": event_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        })
        self.events = self.events[:500]
        self.save_cameras()

    def get_camera_events(self, camera_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        return [event for event in self.events if event.get("camera_id") == camera_id][:limit]

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.events[:limit]

    def get_stats(self) -> Dict[str, Any]:
        cameras = self.get_all_cameras()
        enabled = [camera for camera in cameras if camera.enabled]
        by_type = {}
        for camera in cameras:
            by_type[camera.camera_type.value] = by_type.get(camera.camera_type.value, 0) + 1
        return {
            "total_cameras": len(cameras),
            "enabled_cameras": len(enabled),
            "disabled_cameras": len(cameras) - len(enabled),
            "by_type": by_type,
        }

    def close(self):
        self.save_cameras()


class CameraDatabase:
    def __init__(self, uri: str = None, db_name: str = "safety_monitoring"):
        self.use_mongodb = False
        self.mongo_db = None
        self.fallback_db = None

        if uri:
            self.mongo_db = MongoCameraDatabase(uri, db_name)
            if self.mongo_db.client:
                self.use_mongodb = True
            else:
                self.fallback_db = FallbackCameraDatabase()
        else:
            self.fallback_db = FallbackCameraDatabase()

    def get_database(self):
        return self.mongo_db if self.use_mongodb else self.fallback_db

    def __getattr__(self, item):
        return getattr(self.get_database(), item)

    def close(self):
        self.get_database().close()
