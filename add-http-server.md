# Add HTTP Server to models-varroa-bottom

## Context
Add HTTP inference server similar to models-bee-detector and models-frame-resources to allow API-based Varroa mite detection.

## Plan
- [x] Analyze existing varroa_mite_gui.py to understand model usage
- [x] Review server.py from models-bee-detector and models-frame-resources
- [x] Create server.py with HTTP endpoint
- [x] Extract inference logic into reusable function (detect.py)
- [x] Add Dockerfile for containerization
- [x] Add docker-compose.yml
- [x] Add .dockerignore
- [x] Add justfile for easier management
- [x] Test server locally (running on port 8750)
- [x] Update README with detailed API documentation and schema
- [x] Test with actual image - confirmed working!

## Key findings
- Model: YOLOv11 nano at `model/weights/best.pt`
- Ultralytics YOLO used for inference
- Inference call: `self.model(img_path, imgsz=(6016), max_det=2000, conf=0.1, iou=0.5, ...)`
- Returns bounding boxes in format: [x, y, w, h, confidence]
- Port: 8750 (8700 taken by bee-detector, 8540 by frame-resources)

## Files created/modified
- server.py (new) - HTTP server with POST endpoint for image inference
- detect.py (new) - Extracted inference logic from GUI application
- Dockerfile (new) - Container build instructions
- docker-compose.yml (new) - Container orchestration
- .dockerignore (new) - Files to exclude from Docker build
- justfile (new) - Task automation
- README.md (modified) - Added HTTP server documentation under "Option 3"

## Implementation details
- Server listens on port 8750 (8700 taken by bee-detector, 8540 by frame-resources)
- Accepts multipart/form-data POST requests with "file" field
- Returns JSON with detections array containing bounding boxes
- Uses YOLOv11 nano model at model/weights/best.pt
- Default inference params: conf=0.1, iou=0.5, imgsz=6016, max_det=2000
- Model loaded once globally for efficiency
- Works with image buffer (no temp files needed)

## Test Results
Successfully tested with real image:
- Detected 8 varroa mites with high confidence scores (0.92-0.94)
- Response format validated
- Bounding box coordinates returned correctly
- Server responding on port 8750

## Summary
HTTP inference server successfully added to models-varroa-bottom repository. The server provides a REST API compatible with the architecture used in models-bee-detector and models-frame-resources, allowing integration with the Gratheon ecosystem. All core functionality implemented and tested.

