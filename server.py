import datetime
print(f"[{datetime.datetime.now()}] Script start", flush=True)
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import os
import cgi
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
        content_type = self.headers["Content-Type"]

        if content_type.startswith("multipart/form-data"):
            form_data = cgi.FieldStorage(
                fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"}
            )

            if "file" not in form_data:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"message": "Missing 'file' field in form data"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            file_field = form_data["file"]

            if not isinstance(file_field, cgi.FieldStorage) or not file_field.filename:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"message": "'file' field is not a valid file upload"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            image_data = file_field.file.read()

            weights = "/app/model/weights/best.pt"
            if os.path.exists("model/weights/best.pt"):
                weights = "model/weights/best.pt"

            detections = run(
                weights=weights,
                image_buffer=image_data,
                conf_thres=0.1,
                iou_thres=0.5,
                imgsz=6016,
                max_det=2000
            )

            if not detections:
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"message": "No varroa mites detected", "result": []}
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

            response = {
                "message": "File processed successfully",
                "result": detections,
                "count": len(detections)
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(415)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"message": "Unsupported content type. Please use multipart/form-data."}
            self.wfile.write(json.dumps(response).encode("utf-8"))

server_address = ("", 8750)
httpd = ThreadingHTTPServer(server_address, SimpleHTTPRequestHandler)

print(f"[{datetime.datetime.now()}] Starting server...", flush=True)
print("Server running on port 8750", flush=True)
httpd.serve_forever()

