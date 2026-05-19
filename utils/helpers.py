import numpy as np


def is_point_in_polygon(point, polygon):
    point = np.array(point)
    polygon = np.array(polygon)

    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def check_danger_zone_intrusion(detections, danger_zones, frame_shape):
    intrusions = []
    h, w = frame_shape[:2]

    for det in detections:
        if det['is_alert'] and det['class_name'] == 'person':
            foot_point = det['foot_point']
            normalized_point = [foot_point[0] / w, foot_point[1] / h]

            for zone in danger_zones:
                if is_point_in_polygon(normalized_point, zone['points']):
                    intrusions.append({
                        'detection': det,
                        'zone': zone
                    })
                    break

    return intrusions