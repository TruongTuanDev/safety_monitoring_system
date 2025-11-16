import pygame
import threading
import time
import os
import sys


class AudioAlertSystem:
    def __init__(self):
        """
        Khởi tạo hệ thống cảnh báo âm thanh với debug
        """
        print("🎵 Đang khởi tạo hệ thống âm thanh...")

        try:
            # Khởi tạo pygame mixer với cấu hình cụ thể
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            print(f"✅ Pygame mixer đã khởi tạo: {pygame.mixer.get_init()}")

            self.alert_sound = None
            self.is_playing = False
            self.alert_thread = None

            # Tạo âm thanh cảnh báo đơn giản hơn
            self._create_simple_beep()

        except Exception as e:
            print(f"❌ Lỗi khởi tạo pygame: {e}")
            self.alert_sound = None

    def _create_simple_beep(self):
        """
        Tạo âm thanh beep đơn giản sử dụng pygame
        """
        try:
            # Tạo âm thanh trực tiếp với pygame
            duration = 1000  # milliseconds
            frequency = 800  # Hz
            sample_rate = 22050

            # Tạo mảng âm thanh
            n_samples = int(round(duration * 0.001 * sample_rate))
            buf = numpy.zeros((n_samples, 2), dtype=numpy.int16)
            max_sample = 2 ** (16 - 1) - 1

            for i in range(n_samples):
                t = float(i) / sample_rate  # time in seconds
                # Tạo sóng sine
                sample = int(round(max_sample * math.sin(2 * math.pi * frequency * t)))
                buf[i][0] = sample  # left channel
                buf[i][1] = sample  # right channel

            # Tạo Sound object từ buffer
            self.alert_sound = pygame.sndarray.make_sound(buf)
            print("✅ Đã tạo âm thanh beep thành công!")

        except Exception as e:
            print(f"❌ Không thể tạo âm thanh: {e}")
            # Phương pháp dự phòng - sử dụng system beep
            self.alert_sound = "system"

    def _play_alert_thread(self):
        """
        Phát âm thanh cảnh báo trong thread riêng
        """
        try:
            if not self.is_playing:
                self.is_playing = True
                print("🔊 Đang phát âm thanh cảnh báo...")

                if self.alert_sound == "system":
                    # Sử dụng system beep
                    print("\a")  # System beep
                elif self.alert_sound:
                    # Phát âm thanh với pygame
                    self.alert_sound.play()
                    # Chờ cho âm thanh phát xong
                    pygame.time.wait(1000)
                else:
                    print("❌ Không có âm thanh để phát")

                self.is_playing = False
                print("✅ Đã phát xong âm thanh cảnh báo")

        except Exception as e:
            print(f"❌ Lỗi khi phát âm thanh: {e}")
            self.is_playing = False

    def trigger_alert(self):
        """
        Kích hoạt cảnh báo âm thanh
        """
        if not self.is_playing:
            self.alert_thread = threading.Thread(target=self._play_alert_thread)
            self.alert_thread.daemon = True
            self.alert_thread.start()
            return True
        return False

    def stop_alert(self):
        """
        Dừng âm thanh cảnh báo
        """
        if self.is_playing:
            pygame.mixer.stop()
            self.is_playing = False

    def __del__(self):
        """
        Dọn dẹp khi hủy đối tượng
        """
        self.stop_alert()
        try:
            pygame.mixer.quit()
        except:
            pass


# Thêm imports cần thiết
try:
    import numpy
    import math
except ImportError:
    print("❌ Cần cài đặt numpy: pip install numpy")
    numpy = None
    math = None