import cv2
import numpy as np
from imutils.video import VideoStream
from yolodetect import YoloDetect
import screeninfo
import time

# Lấy thông tin màn hình chính
monitor = screeninfo.get_monitors()[0]
screen_width = monitor.width
screen_height = monitor.height

# Xác định kích thước cửa sổ mong muốn
window_percent = 0.8
window_width = int(screen_width * window_percent)
window_height = int(screen_height * window_percent)

# Tính toán vị trí để cửa sổ nằm ở giữa
x_pos = int((screen_width - window_width) / 2)
y_pos = int((screen_height - window_height) / 2)

# Khởi tạo cửa sổ và thiết lập kích thước/vị trí
WINDOW_NAME = "Intrusion Warning"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, window_width, window_height)
cv2.moveWindow(WINDOW_NAME, x_pos, y_pos)

# TỐI ƯU TỐC ĐỘ: Thiết lập độ phân giải thấp cho camera
video = VideoStream(src=0, resolution=(640, 480)).start()
# Chua cac diem nguoi dung chon de tao da giac
points = []

# new model Yolo
model = YoloDetect()


def handle_left_click(event, x, y, flags, points):
    if not detect:
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append([x, y])


def draw_polygon(frame, points):
    # 1. Vẽ các điểm
    for point in points:
        # Tăng kích thước điểm
        frame = cv2.circle(frame, (point[0], point[1]), 8, (0, 165, 255), -1)

    # 2. Vẽ đường đa giác
    if len(points) > 1:
        is_closed = True if detect else False
        line_color = (0, 255, 255) if detect else (255, 100, 0)

        frame = cv2.polylines(frame, [np.int32(points)], is_closed, line_color, thickness=3)

        # 3. Tô màu mờ khu vực (Chỉ khi đã bắt đầu detect)
        if detect and len(points) > 2:
            overlay = frame.copy()
            alpha = 0.3  # Độ trong suốt

            pts = np.array([points], np.int32)
            cv2.fillPoly(overlay, pts, (255, 0, 0))  # màu xanh (khu vực giám sát)

            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    return frame


detect = False
raw_is_alarming = False
is_alarming_display = False


alarm_display_duration = 3.0
last_alarm_time = 0.0

# tính FPS
start_time = time.time()
frame_count = 0

while True:
    frame = video.read()
    # Điều chỉnh kích thước frame để khớp với kích thước cửa sổ
    frame = cv2.resize(frame, (window_width, window_height))
    frame = cv2.flip(frame, 1)

    # Ve ploygon
    frame = draw_polygon(frame, points)

    # KHI ĐANG DETECT
    if detect:
        frame, raw_is_alarming = model.detect(frame=frame, points=points)

    # LOGIC GIỮ TRẠNG THÁI CẢNH BÁO
    current_time = time.time()

    if raw_is_alarming:

        last_alarm_time = current_time
        is_alarming_display = True
    elif current_time - last_alarm_time > alarm_display_duration:

        is_alarming_display = False

    # HIỆU ỨNG CẢNH BÁO TOÀN KHUNG HÌNH
    if is_alarming_display:

        cv2.putText(frame, "🚨 INTRUSION DETECTED 🚨", (10, 50), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 3)

        frame = cv2.rectangle(frame, (0, 0), (window_width, window_height), (0, 0, 255), 10)

    # HIỂN THỊ TRẠNG THÁI
    status_text = "STATUS: Drawing Zone (Click + Press 'd')"
    status_color = (0, 255, 0)
    if detect:
        status_text = "STATUS: Intrusion Monitoring (Press 'q' to exit)"
        status_color = (0, 255, 255)

    cv2.putText(frame, status_text, (10, window_height - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    # TÍNH VÀ HIỂN THỊ FPS
    frame_count += 1
    if (current_time - start_time) >= 1:  # Cập nhật mỗi 1 giây
        fps = frame_count / (current_time - start_time)

        cv2.putText(frame, f"FPS: {fps:.2f}", (window_width - 150, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        start_time = current_time
        frame_count = 0

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('d'):
        if len(points) >= 3 and not detect:  # Chỉ bắt đầu detect khi có ít nhất 3 điểm
            points.append(points[0])
            detect = True
            print("Intrusion Monitoring Started.")

    # Hien anh ra man hinh
    cv2.imshow(WINDOW_NAME, frame)

    cv2.setMouseCallback(WINDOW_NAME, handle_left_click, points)

video.stop()
cv2.destroyAllWindows()