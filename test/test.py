from pathlib import Path

import cv2
import yaml
from ultralytics import YOLO


root = Path(__file__).resolve().parents[1]
with (root / "config.yaml").open("r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

model = YOLO(str(root / config["system"]["model_path"]))
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=config["system"]["confidence_threshold"])
    annotated = results[0].plot()

    cv2.imshow("PPE Detection", annotated)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
