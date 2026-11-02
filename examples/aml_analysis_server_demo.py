import json
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8001

PAYLOAD = {
    "collection": "CMB-AML",
    "patient_count": 6,
    "analysis": {
        "top_similarity_pair": {
            "patient_a": "MSB-02960",
            "patient_b": "MSB-06711",
            "similarity": 0.9999999999999999,
        },
        "clinical_focus": ["demographics", "treatment", "outcomes"],
        "image_focus": ["CT", "MRI", "PET", "radiomics"],
        "longitudinal_pattern": "increasing biomarker intensity over follow-up",
        "interpretation": (
            "This patient-matched AML analysis integrates clinical metadata with "
            "multimodal imaging features to describe disease similarity and biomarker progression."
        ),
    },
}


class AMLAnalysisHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/analysis/example":
            body = json.dumps(PAYLOAD).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "not found"}')

    def log_message(self, format, *args):
        return


def run_demo():
    server = HTTPServer((HOST, PORT), AMLAnalysisHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print("CLIENT REQUEST -> http://127.0.0.1:8001/analysis/example")
    with urllib.request.urlopen(f"http://{HOST}:{PORT}/analysis/example", timeout=5) as response:
        data = response.read().decode("utf-8")
        print("SERVER RESPONSE:")
        print(data)
    server.shutdown()
    server.server_close()
    print("\nThis is a simple client-server AML analysis example using the Python standard library.")


if __name__ == "__main__":
    run_demo()
