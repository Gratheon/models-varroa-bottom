import os
import time
import uuid

from flask import Flask, g, jsonify, request
from gratheon_log_lib import bind_context, clear_context, configure, error_enriched, info, warn
from detect import run

app = Flask(__name__)
configure()


def _weights_path() -> str:
    weights = "/app/model/weights/best.pt"
    if os.path.exists("model/weights/best.pt"):
        weights = "model/weights/best.pt"
    return weights


@app.before_request
def before_request() -> None:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    g.request_started_at = time.perf_counter()
    g.request_id = request_id
    bind_context(request_id=request_id)
    info(
        "request started",
        {
            "path": request.path,
            "method": request.method,
            "remote_addr": request.remote_addr,
            "content_length": request.content_length,
            "content_type": request.content_type,
            "user_agent": request.user_agent.string,
        },
    )


@app.after_request
def after_request(response):
    started_at = getattr(g, "request_started_at", None)
    duration_ms = None
    if started_at is not None:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

    info(
        "request finished",
        {
            "path": request.path,
            "method": request.method,
            "status_code": response.status_code,
            "content_length": response.calculate_content_length(),
            "duration_ms": duration_ms,
        },
    )
    clear_context()
    return response


@app.teardown_request
def teardown_request(_exc):
    clear_context()

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
    if 'file' not in request.files:
        warn("rejecting request, missing file part")
        return jsonify({"message": "Missing 'file' field in form data"}), 400

    file = request.files['file']

    if file.filename == '':
        warn("rejecting request, no file selected")
        return jsonify({"message": "No file selected"}), 400

    info("file field found", {"filename": file.filename, "mimetype": file.mimetype})

    image_data = file.read()
    image_size_mb = len(image_data) / (1024 * 1024)
    info(
        "image data read",
        {
            "filename": file.filename,
            "image_bytes": len(image_data),
            "image_size_mb": round(image_size_mb, 2),
        },
    )

    # Check if it's a valid JPEG by checking magic bytes
    if len(image_data) > 2:
        magic_bytes = image_data[:2]
        info("image magic bytes", {"magic_bytes": magic_bytes.hex()})
        if magic_bytes == b'\xff\xd8':
            info("valid JPEG magic bytes detected")
        else:
            warn("invalid JPEG magic bytes detected", {"magic_bytes": magic_bytes.hex()})

    weights = _weights_path()
    info(
        "starting detection",
        {
            "weights": weights,
            "conf_thres": 0.1,
            "iou_thres": 0.5,
            "imgsz": 6016,
            "max_det": 2000,
        },
    )

    try:
        detections = run(
            weights=weights,
            image_buffer=image_data,
            conf_thres=0.1,
            iou_thres=0.5,
            imgsz=6016,
            max_det=2000
        )
    except Exception as exc:
        error_enriched("varroa bottom detection failed", exc, {"filename": file.filename})
        return jsonify({"message": "Error processing image", "result": [], "count": 0}), 500

    info("detection complete", {"detections": len(detections) if detections else 0})

    if not detections:
        info("returning no varroa mites detected")
        return jsonify({"message": "No varroa mites detected", "result": [], "count": 0})

    info("returning detections", {"count": len(detections)})
    return jsonify({
        "message": "File processed successfully",
        "result": detections,
        "count": len(detections)
    })

if __name__ == '__main__':
    info("starting Flask server on port 8750", {"port": 8750, "weights": _weights_path()})
    app.run(host='0.0.0.0', port=8750, threaded=True, debug=False, use_reloader=False)
