import cv2
import numpy as np


class ZoneManager:
    def __init__(self):
        self.danger_zones = []
        self.current_zone_points = []
        self.drawing_mode = False
        self.selected_zone_index = -1

    def handle_left_click(self, event, x, y, flags, param):
        if self.drawing_mode:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.current_zone_points.append([x, y])
                print(f"📍 Added point: ({x}, {y}) - Total: {len(self.current_zone_points)}")

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.select_zone_for_deletion(x, y)

    def select_zone_for_deletion(self, x, y):
        for i, zone in enumerate(self.danger_zones):
            points = np.array(zone['points']) * [self.window_width, self.window_height]
            points = points.astype(np.int32)

            if cv2.pointPolygonTest(points, (x, y), False) >= 0:
                self.selected_zone_index = i
                print(f"🎯 Selected zone {i + 1} for deletion. Press 'x' to confirm.")
                return

        self.selected_zone_index = -1

    def set_window_size(self, width, height):
        self.window_width = width
        self.window_height = height

    def draw_danger_zones(self, frame):
        zone_colors = [
            [0, 0, 255],
            [0, 255, 255],
            [255, 0, 0],
            [255, 0, 255],
            [0, 255, 0],
        ]

        for i, zone in enumerate(self.danger_zones):
            color = zone_colors[i % len(zone_colors)]
            points = np.array(zone['points']) * [self.window_width, self.window_height]
            points = points.astype(np.int32)

            overlay = frame.copy()
            cv2.fillPoly(overlay, [points], color)
            cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

            cv2.polylines(frame, [points], True, color, 2)

            zone_name = f"Zone {i + 1}"
            text_size = cv2.getTextSize(zone_name, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            text_x = points[0][0]
            text_y = points[0][1] - 10

            cv2.rectangle(frame, (text_x, text_y - text_size[1]),
                          (text_x + text_size[0], text_y), color, -1)
            cv2.putText(frame, zone_name, (text_x, text_y - 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            if i == self.selected_zone_index:
                cv2.polylines(frame, [points], True, (255, 255, 255), 4)

        if self.drawing_mode and len(self.current_zone_points) > 0:
            for point in self.current_zone_points:
                frame = cv2.circle(frame, (point[0], point[1]), 6, (0, 165, 255), -1)

            if len(self.current_zone_points) > 1:
                cv2.polylines(frame, [np.int32(self.current_zone_points)], False, (0, 165, 255), 2)

            if len(self.current_zone_points) >= 3:
                cv2.putText(frame, f"Points: {len(self.current_zone_points)} (Press 'c' to complete)",
                            (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        return frame

    def complete_current_zone(self):
        if len(self.current_zone_points) >= 3:
            if self.current_zone_points[0] != self.current_zone_points[-1]:
                self.current_zone_points.append(self.current_zone_points[0])

            normalized_points = []
            for point in self.current_zone_points:
                x_norm = point[0] / self.window_width
                y_norm = point[1] / self.window_height
                normalized_points.append([x_norm, y_norm])

            new_zone = {
                'name': f"Zone {len(self.danger_zones) + 1}",
                'points': normalized_points,
                'color': [0, 0, 255]
            }
            self.danger_zones.append(new_zone)

            print(f"✅ Created danger zone {len(self.danger_zones)} with {len(self.current_zone_points)} points")
            self.current_zone_points = []
            self.drawing_mode = False
            return True
        else:
            print("❌ Need at least 3 points to create a zone!")
            return False

    def delete_selected_zone(self):
        if 0 <= self.selected_zone_index < len(self.danger_zones):
            deleted_zone = self.danger_zones.pop(self.selected_zone_index)
            print(f"🗑️ Deleted zone {self.selected_zone_index + 1}")
            self.selected_zone_index = -1

            for i, zone in enumerate(self.danger_zones):
                zone['name'] = f"Zone {i + 1}"
            return True
        else:
            print("❌ No zone selected for deletion!")
            return False

    def get_danger_zones(self):
        return self.danger_zones

    def has_zones(self):
        return len(self.danger_zones) > 0

    def reset(self):
        self.danger_zones = []
        self.current_zone_points = []
        self.drawing_mode = False
        self.selected_zone_index = -1