import cv2
import screeninfo


class WindowManager:
    def __init__(self, window_name="Safety Monitoring System"):
        self.window_name = window_name
        self.window_width = 1200
        self.window_height = 800
        self.setup_window()

    def setup_window(self):
        try:
            monitor = screeninfo.get_monitors()[0]
            screen_width = monitor.width
            screen_height = monitor.height

            window_percent = 0.8
            self.window_width = int(screen_width * window_percent)
            self.window_height = int(screen_height * window_percent)

            x_pos = int((screen_width - self.window_width) / 2)
            y_pos = int((screen_height - self.window_height) / 2)

            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.window_width, self.window_height)
            cv2.moveWindow(self.window_name, x_pos, y_pos)

        except Exception as e:
            print(f"⚠️ Using default window size: {e}")
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.window_width, self.window_height)

    def display_frame(self, frame):
        cv2.imshow(self.window_name, frame)

    def set_mouse_callback(self, callback):
        cv2.setMouseCallback(self.window_name, callback)

    def get_window_size(self):
        return self.window_width, self.window_height