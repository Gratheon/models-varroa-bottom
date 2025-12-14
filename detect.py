import numpy as np
import cv2
from ultralytics import YOLO

model = None

def load_model(weights_path="/app/model/weights/best.pt"):
    global model
    if model is None:
        model = YOLO(weights_path, verbose=False)
    return model

def run(weights="/app/model/weights/best.pt", image_buffer=None, conf_thres=0.1, iou_thres=0.5, imgsz=6016, max_det=2000):
    global model

    if model is None:
        model = load_model(weights)

    if image_buffer is None:
        return []

    nparr = np.frombuffer(image_buffer, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return []

    results = model(
        img,
        imgsz=imgsz,
        max_det=max_det,
        conf=conf_thres,
        iou=iou_thres,
        verbose=False
    )

    detections = []
    for result in results:
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                detections.append({
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "confidence": conf,
                    "class": cls,
                    "class_name": "varroa_mite"
                })

    return detections

