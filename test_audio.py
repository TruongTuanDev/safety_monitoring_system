import pygame
import time


def test_audio():
    print("🔊 Kiểm tra hệ thống âm thanh...")

    try:
        # Khởi tạo pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        print(f"✅ Pygame init: {pygame.mixer.get_init()}")

        # Tạo âm thanh đơn giản
        duration = 1  # giây
        sample_rate = 22050
        n_samples = int(sample_rate * duration)

        import array
        buf = array.array('h', [0] * n_samples * 2)

        # Tạo sóng sine
        for i in range(n_samples):
            t = float(i) / sample_rate
            freq = 800
            val = int(30000 * (0.5 * (1 + math.sin(2 * math.pi * freq * t))))
            buf[2 * i] = val
            buf[2 * i + 1] = val

        # Tạo và phát sound
        sound = pygame.sndarray.make_sound(buf)
        print("🎵 Đang phát âm thanh kiểm tra...")
        sound.play()

        # Chờ cho phát xong
        time.sleep(2)
        print("✅ Kiểm tra hoàn tất")

    except Exception as e:
        print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    import math

    test_audio()