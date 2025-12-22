import datetime
print(f"[{datetime.datetime.now()}] Script start", flush=True)
from flask import Flask, request, jsonify
import os
from detect import run

print(f"[{datetime.datetime.now()}] Imports finished", flush=True)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return '''
    <html>
    <body>
    <h1>Varroa Mite Detector API</h1>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept="image/*" />
        <input type="submit" value="Upload and Detect" />
    </form>
    </body>
    </html>
    '''

@app.route('/', methods=['POST'])
def detect():
    print(f"[{datetime.datetime.now()}] Received POST request", flush=True)

    if 'file' not in request.files:
        print(f"[{datetime.datetime.now()}] ERROR: No file part in request", flush=True)
        return jsonify({"message": "Missing 'file' field in form data"}), 400

    file = request.files['file']

    if file.filename == '':
        print(f"[{datetime.datetime.now()}] ERROR: No file selected", flush=True)
        return jsonify({"message": "No file selected"}), 400

    print(f"[{datetime.datetime.now()}] File field found: filename={file.filename}", flush=True)

    image_data = file.read()
    image_size_mb = len(image_data) / (1024 * 1024)
    print(f"[{datetime.datetime.now()}] Image data read: {len(image_data)} bytes ({image_size_mb:.2f} MB)", flush=True)

    # Check if it's a valid JPEG by checking magic bytes
    if len(image_data) > 2:
        magic_bytes = image_data[:2]
        print(f"[{datetime.datetime.now()}] Image magic bytes: {magic_bytes.hex()}", flush=True)
        if magic_bytes == b'\xff\xd8':
            print(f"[{datetime.datetime.now()}] Valid JPEG magic bytes detected", flush=True)
        else:
            print(f"[{datetime.datetime.now()}] WARNING: Invalid JPEG magic bytes!", flush=True)

    weights = "/app/model/weights/best.pt"
    if os.path.exists("model/weights/best.pt"):
        weights = "model/weights/best.pt"

    print(f"[{datetime.datetime.now()}] Using weights: {weights}", flush=True)
    print(f"[{datetime.datetime.now()}] Starting detection with conf_thres=0.1, iou_thres=0.5, imgsz=6016, max_det=2000", flush=True)

    detections = run(
        weights=weights,
        image_buffer=image_data,
        conf_thres=0.1,
        iou_thres=0.5,
        imgsz=6016,
        max_det=2000
    )

    print(f"[{datetime.datetime.now()}] Detection complete: found {len(detections) if detections else 0} detections", flush=True)

    if not detections:
        print(f"[{datetime.datetime.now()}] Returning: No varroa mites detected", flush=True)
        return jsonify({"message": "No varroa mites detected", "result": [], "count": 0})

    print(f"[{datetime.datetime.now()}] Returning: {len(detections)} varroa mites detected", flush=True)
    return jsonify({
        "message": "File processed successfully",
        "result": detections,
        "count": len(detections)
    })

if __name__ == '__main__':
    print(f"[{datetime.datetime.now()}] Starting Flask server on port 8750", flush=True)
    app.run(host='0.0.0.0', port=8750, threaded=True)

