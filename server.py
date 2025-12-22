import datetime
print(f"[{datetime.datetime.now()}] Script start", flush=True)
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import os
from email import message_from_binary_file
from io import BytesIO
from detect import run
print(f"[{datetime.datetime.now()}] Imports finished", flush=True)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        form_html = """
        <html>
        <body>
        <h1>Varroa Mite Detector API</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" />
            <input type="submit" value="Upload and Detect" />
        </form>
        </body>
        </html>
        """
        self.wfile.write(form_html.encode("utf-8"))

    def do_POST(self):
        print(f"[{datetime.datetime.now()}] Received POST request", flush=True)
        content_type = self.headers.get("Content-Type", "")
        print(f"[{datetime.datetime.now()}] Content-Type: {content_type}", flush=True)

        if not content_type.startswith("multipart/form-data"):
            print(f"[{datetime.datetime.now()}] ERROR: Unsupported content type: {content_type}", flush=True)
            self.send_response(415)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"message": "Unsupported content type. Please use multipart/form-data."}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        print(f"[{datetime.datetime.now()}] Processing multipart/form-data", flush=True)

        # Extract boundary from content type
        boundary = None
        for part in content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                boundary = part.split('=', 1)[1].strip()
                break

        if not boundary:
            print(f"[{datetime.datetime.now()}] ERROR: No boundary found in content-type", flush=True)
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"message": "Missing boundary in multipart/form-data"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        print(f"[{datetime.datetime.now()}] Boundary: {boundary}", flush=True)

        # Read the entire request body
        content_length = int(self.headers.get('Content-Length', 0))
        print(f"[{datetime.datetime.now()}] Content-Length header: {content_length}", flush=True)

        if content_length == 0:
            print(f"[{datetime.datetime.now()}] ERROR: Content-Length is 0", flush=True)
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"message": "Empty request body"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        body = self.rfile.read(content_length)
        print(f"[{datetime.datetime.now()}] Read {len(body)} bytes from request body", flush=True)

        # Parse multipart data manually
        boundary_bytes = ('--' + boundary).encode()
        parts = body.split(boundary_bytes)

        image_data = None
        filename = None

        for part in parts:
            if len(part) < 10:
                continue

            # Find the double CRLF that separates headers from data
            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue

            headers = part[:header_end].decode('utf-8', errors='ignore')
            data = part[header_end + 4:]  # Skip the \r\n\r\n

            # Check if this part contains a file upload
            # Look for Content-Disposition header with name="file" or name=file
            is_file_field = False
            for line in headers.split('\r\n'):
                if 'Content-Disposition' in line and 'name=' in line:
                    # Extract the name attribute
                    if 'name="file"' in line or "name='file'" in line or 'name=file' in line:
                        is_file_field = True
                        # Extract filename if present
                        if 'filename=' in line:
                            if 'filename="' in line:
                                filename = line.split('filename="')[1].split('"')[0]
                            elif "filename='" in line:
                                filename = line.split("filename='")[1].split("'")[0]
                        break

            if is_file_field:
                # Remove trailing CRLF or -- if present
                if data.endswith(b'--\r\n'):
                    data = data[:-4]
                elif data.endswith(b'\r\n'):
                    data = data[:-2]
                elif data.endswith(b'--'):
                    data = data[:-2]

                image_data = data
                print(f"[{datetime.datetime.now()}] Found file field: filename={filename}, size={len(image_data)}", flush=True)
                break

        if image_data is None:
            print(f"[{datetime.datetime.now()}] ERROR: No file data found in request", flush=True)
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"message": "Missing 'file' field in form data"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        image_size_mb = len(image_data) / (1024 * 1024)
        print(f"[{datetime.datetime.now()}] Image data extracted: {len(image_data)} bytes ({image_size_mb:.2f} MB)", flush=True)

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
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"message": "No varroa mites detected", "result": [], "count": 0}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        print(f"[{datetime.datetime.now()}] Returning: {len(detections)} varroa mites detected", flush=True)
        response = {
            "message": "File processed successfully",
            "result": detections,
            "count": len(detections)
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

server_address = ("", 8750)
httpd = ThreadingHTTPServer(server_address, SimpleHTTPRequestHandler)

print(f"[{datetime.datetime.now()}] Starting server...", flush=True)
print("Server running on port 8750", flush=True)
httpd.serve_forever()

