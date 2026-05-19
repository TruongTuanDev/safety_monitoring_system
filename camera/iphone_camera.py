import cv2
import time


class iPhoneCamera:
    """
    Lớp đơn giản để kết nối iPhone thay cho webcam
    Chỉ cần thay cv2.VideoCapture(0) bằng iPhoneCamera()
    """

    def __init__(self, ip='192.168.1.100', port=4747, width=640, height=480):
        """
        Khởi tạo kết nối đến iPhone

        Args:
            ip: Địa chỉ IP của iPhone (xem trong app DroidCam)
            port: 4747 cho DroidCam, 8080 cho IP Webcam
            width, height: Độ phân giải
        """
        self.ip = ip
        self.port = port
        self.width = width
        self.height = height

        # URL stream từ iPhone
        self.stream_url = f'http://{ip}:{port}/video'

        # Đối tượng VideoCapture
        self.cap = None

        # Thông tin kết nối
        self.connected = False

    def connect(self, retries=3):
        """
        Kết nối đến iPhone

        Returns:
            bool: True nếu thành công
        """
        print(f"📱 Đang kết nối đến iPhone {self.ip}:{self.port}...")

        for attempt in range(retries):
            try:
                # Tạo VideoCapture với stream URL
                self.cap = cv2.VideoCapture(self.stream_url)

                # Đặt timeout cho kết nối mạng
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                # Đọc thử frame đầu tiên
                success, frame = self.cap.read()

                if success and frame is not None:
                    self.connected = True
                    print(f"✅ Đã kết nối đến iPhone! Kích thước: {frame.shape[1]}x{frame.shape[0]}")
                    return True
                else:
                    print(f"⚠️ Lần thử {attempt + 1}: Không nhận được frame")
                    self.cap.release()

            except Exception as e:
                print(f"⚠️ Lần thử {attempt + 1} thất bại: {e}")

            time.sleep(1)  # Chờ 1 giây trước khi thử lại

        print("❌ Không thể kết nối đến iPhone")
        return False

    def read(self):
        """
        Đọc frame từ iPhone (tương tự cv2.VideoCapture.read())

        Returns:
            tuple: (success, frame) hoặc (False, None)
        """
        if not self.connected or self.cap is None:
            return False, None

        try:
            return self.cap.read()
        except:
            return False, None

    def release(self):
        """Giải phóng tài nguyên"""
        if self.cap is not None:
            self.cap.release()
        self.connected = False
        print("📴 Đã ngắt kết nối iPhone")

    def isOpened(self):
        """Kiểm tra camera có đang mở không"""
        return self.connected and self.cap is not None and self.cap.isOpened()

    def get(self, prop_id):
        """Lấy thuộc tính camera (tương tự cv2.VideoCapture.get())"""
        if self.cap is not None:
            return self.cap.get(prop_id)
        return 0

    def set(self, prop_id, value):
        """Đặt thuộc tính camera"""
        if self.cap is not None:
            return self.cap.set(prop_id, value)
        return False


def find_iphone_ip():
    """
    Hướng dẫn người dùng tìm IP iPhone
    """
    print("\n" + "=" * 50)
    print("ĐỂ TÌM IP CỦA IPHONE:")
    print("=" * 50)
    print("1. Vào Settings > Wi-Fi")
    print("2. Nhấn vào biểu tượng (i) bên cạnh mạng Wi-Fi đang dùng")
    print("3. Tìm dòng 'IP Address' (ví dụ: 192.168.1.100)")
    print("4. Nhập IP đó vào chương trình")
    print("=" * 50 + "\n")

    ip = input("Nhập IP của iPhone (hoặc Enter để dùng 192.168.1.100): ")
    return ip if ip.strip() else '192.168.1.100'