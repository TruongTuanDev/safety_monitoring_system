from abc import ABC, abstractmethod
import cv2


class BaseMode(ABC):
    def __init__(self, name, detector, visualizer, audio_manager):
        self.name = name
        self.detector = detector
        self.visualizer = visualizer
        self.audio_manager = audio_manager
        self.is_active = False

    @abstractmethod
    def process_frame(self, frame):
        pass

    @abstractmethod
    def draw_ui(self, frame):
        pass

    def activate(self):
        self.is_active = True
        print(f"✅ {self.name} activated")

    def deactivate(self):
        self.is_active = False
        print(f"❌ {self.name} deactivated")

    def get_instructions(self):
        return []