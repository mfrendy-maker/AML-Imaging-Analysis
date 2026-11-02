from __future__ import annotations

import base64
import html
import io
import json
import os
import time
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from urllib.parse import urlparse

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = '127.0.0.1'
PORT = int(os.environ.get('PORT', '8003'))
ROOT = Path(__file__).resolve().parents[2]
TRAINING_UPLOAD_DIR = ROOT / 'data' / 'training_uploads'

HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AML CT Analysis</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f8fc; color: #16222d; margin: 0; padding: 24px; }
    .container { max-width: 900px; margin: 0 auto; background: white; border-radius: 18px; padding: 28px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }
    h1 { margin-top: 0; }
    .card { background: #f8fbff; border: 1px solid #dfeaf7; border-radius: 12px; padding: 18px; margin-top: 18px; }
    form { display: grid; gap: 16px; }
    input[type=file] { padding: 10px; border: 1px solid #d0deef; border-radius: 8px; background: white; }
    button { background: #1e5ea8; color: white; border: none; border-radius: 8px; padding: 12px 18px; font-size: 16px; cursor: pointer; }
    .result-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }
    .stat { background: white; border: 1px solid #dfeaf7; border-radius: 10px; padding: 12px; }
    .label { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #56759a; font-weight: bold; }
    pre { background: #0f172a; color: #e2e8f0; padding: 14px; border-radius: 10px; overflow: auto; }
  </style>
</head>
<body>
  <div class="container">
    <h1>AML CT Image Analysis</h1>
    <p>Upload a CT image to view basic image-intensity statistics. This demo does not detect or locate tumors.</p>
    <div class="card">
      <form action="/analyse" method="post" enctype="multipart/form-data">
        <label for="image">CT scan image</label>
        <input id="image" name="image" type="file" accept=".png,.jpg,.jpeg,.dcm,.nii,.nii.gz,.tif,.tiff,image/png,image/jpeg,image/tiff" required>
            <label><input name="training_consent" type="checkbox" value="yes"> Optional: I consent to this image being retained on the demo server for training use. I am authorized to share it and have removed identifying information.</label>
            <p>Without consent, the image is processed for this result and is not saved. This demo does not remove identifying information or DICOM metadata.</p>
        <button type="submit">Analyse</button>
      </form>
    </div>
  </div>
</body>
</html>
"""


def _safe_name(filename: str) -> str:
    name = os.path.basename(filename or 'upload')
    clean = ''.join(ch if ch.isalnum() or ch in {'.', '_', '-'} else '_' for ch in name)
    return clean or 'upload'


def _parse_multipart_form(raw_body: bytes, content_type: str) -> dict:
    if 'multipart/form-data' not in content_type.lower():
        return {}

    message = BytesParser(policy=default).parsebytes(
        (f'Content-Type: {content_type}\r\n\r\n').encode('utf-8') + raw_body
    )

    parsed: dict[str, object] = {}
    for part in message.iter_parts():
        name = part.get_param('name', header='content-disposition')
        if name is None:
            continue
        filename = part.get_filename()
        payload = part.get_payload(decode=True)
        if filename:
            parsed[name] = (filename, payload or b'')
        else:
            parsed[name] = payload.decode('utf-8', 'replace') if payload is not None else ''
    return parsed


def _read_image_metrics(data: bytes) -> dict:
    metrics = {
        'file_size_bytes': len(data),
        'width': None,
        'height': None,
        'mean_intensity': None,
        'std_intensity': None,
        'max_intensity': None,
        'min_intensity': None,
        'high_intensity_fraction': None,
        'notes': 'Image decoded successfully.'
    }

    if Image is None or np is None:
        metrics['notes'] = 'Image library was not available; only file-level metadata is available.'
        return metrics

    try:
        stream = io.BytesIO(data)
        with Image.open(stream) as img:
            img = img.convert('L')
            arr = np.asarray(img, dtype=np.float32)
            metrics['width'] = int(arr.shape[1])
            metrics['height'] = int(arr.shape[0])
            metrics['mean_intensity'] = float(np.mean(arr))
            metrics['std_intensity'] = float(np.std(arr))
            metrics['max_intensity'] = float(np.max(arr))
            metrics['min_intensity'] = float(np.min(arr))
            threshold = float(np.percentile(arr, 75))
            metrics['high_intensity_fraction'] = float(np.count_nonzero(arr >= threshold) / arr.size)
            return metrics
    except Exception as exc:
        metrics['notes'] = f'Image could not be decoded: {exc}'
        return metrics


def render_result_page(result: dict) -> str:
    data = json.dumps(result, indent=2)
    original_data = result.get('original_data_url', '')
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AML CT Result</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f8fc; color: #16222d; margin: 0; padding: 24px; }}
    .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 18px; padding: 28px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); }}
    h1 {{ margin-top: 0; }}
    .card {{ background: #f8fbff; border: 1px solid #dfeaf7; border-radius: 12px; padding: 18px; margin-top: 18px; }}
    .result-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }}
    .stat {{ background: white; border: 1px solid #dfeaf7; border-radius: 10px; padding: 12px; }}
    .label {{ font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #56759a; font-weight: bold; }}
    .image-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 12px; }}
    .image-box {{ background: white; border: 1px solid #dfeaf7; border-radius: 12px; padding: 12px; }}
    .image-box img {{ max-width: 100%; height: auto; display: block; border-radius: 8px; }}
    pre {{ background: #0f172a; color: #e2e8f0; padding: 14px; border-radius: 10px; overflow: auto; }}
    a {{ display: inline-block; margin-top: 14px; color: #1e5ea8; text-decoration: none; font-weight: bold; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>AML CT Analysis Output</h1>
    <div class="card">
      <div class="result-grid">
        <div class="stat"><div class="label">File</div><div>{html.escape(str(result['file_name']))}</div></div>
        <div class="stat"><div class="label">Width</div><div>{result['width'] if result['width'] is not None else 'n/a'}</div></div>
        <div class="stat"><div class="label">Height</div><div>{result['height'] if result['height'] is not None else 'n/a'}</div></div>
        <div class="stat"><div class="label">Mean intensity</div><div>{result['mean_intensity'] if result['mean_intensity'] is not None else 'n/a'}</div></div>
        <div class="stat"><div class="label">Std intensity</div><div>{result['std_intensity'] if result['std_intensity'] is not None else 'n/a'}</div></div>
            <div class="stat"><div class="label">High-intensity fraction</div><div>{result['high_intensity_fraction'] if result['high_intensity_fraction'] is not None else 'n/a'}</div></div>
      </div>
    </div>
    <div class="card">
        <div class="label">CT preview</div>
      <div class="image-grid">
        <div class="image-box">
          <div class="label">Original CT</div>
          <img src="{original_data}" alt="Original CT" />
        </div>
        <div class="image-box">
          <div class="label">Lesion localization</div>
          <p>Not available. This demo does not use a validated tumor-segmentation model, so it cannot identify a cancer location.</p>
        </div>
      </div>
    </div>
    <div class="card">
      <div class="label">Interpretation</div>
      <p>{html.escape(str(result['interpretation']))}</p>
      <p><strong>Biomarker:</strong> {html.escape(str(result['biomarker']))}</p>
      <p><strong>Clinical note:</strong> {html.escape(str(result['clinical_note']))}</p>
            <p><strong>Training retention:</strong> {('Image saved for training because you opted in.' if result.get('training_retained', False) else 'Image not saved for training.')}</p>
    </div>
    <div class="card">
      <div class="label">Raw analysis</div>
      <pre>{html.escape(data)}</pre>
    </div>
    <a href="/">Upload another image</a>
  </div>
</body>
</html>
"""


def _image_preview_data_url(data: bytes) -> str:
    if Image is None or np is None:
        return ''

    try:
        with Image.open(io.BytesIO(data)) as img:
            buf = io.BytesIO()
            img.convert('L').save(buf, format='PNG')
            preview_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
            return f'data:image/png;base64,{preview_b64}'
    except Exception:
        return ''


def analyse_uploaded_file(file_name: str, data: bytes, training_retained: bool = False) -> dict:
    metrics = _read_image_metrics(data)
    mean_i = metrics['mean_intensity']
    std_i = metrics['std_intensity']
    original_data_url = _image_preview_data_url(data)

    if mean_i is None:
        interpretation = 'The uploaded file was not readable as an image, so only file metadata could be assessed.'
        biomarker = 'Image decoding unavailable'
        clinical_note = 'Please upload a standard CT image or an image preview of the scan.'
    else:
        interpretation = 'Image intensity statistics only. This demo does not detect or locate tumors and must not be used for diagnosis.'
        biomarker = 'Image intensity summary (not a tumor biomarker)'
        clinical_note = 'No lesion segmentation was performed. Bright areas may represent normal anatomy, contrast, bone, calcification, or acquisition settings.'

    summary = {
        'file_name': file_name,
        'width': metrics['width'],
        'height': metrics['height'],
        'mean_intensity': mean_i,
        'std_intensity': std_i,
        'max_intensity': metrics['max_intensity'],
        'min_intensity': metrics['min_intensity'],
        'high_intensity_fraction': metrics['high_intensity_fraction'],
        'interpretation': interpretation,
        'biomarker': biomarker,
        'clinical_note': clinical_note,
        'source': 'AML CT upload demo',
        'analysis_type': 'CT image intensity summary; no lesion segmentation',
        'timestamp_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'training_retained': training_retained,
        'original_data_url': original_data_url,
    }
    return summary


def _store_training_upload(file_name: str, data: bytes, form: dict) -> bool:
    if form.get('training_consent') != 'yes':
        return False

    TRAINING_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = TRAINING_UPLOAD_DIR / f'{int(time.time() * 1000)}_{file_name}'
    destination.write_bytes(data)
    return True


class AMLCTUploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ('/', '/upload'):
            body = HTML_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        body = b'{"error": "not found"}'
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/analyse':
            body = b'{"error": "not found"}'
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        content_length = int(self.headers.get('Content-Length', '0'))
        raw_body = self.rfile.read(content_length)
        form = _parse_multipart_form(raw_body, self.headers.get('Content-Type', ''))
        uploaded = form.get('image')
        if uploaded is None:
            body = b'{"error": "no image uploaded"}'
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if isinstance(uploaded, tuple):
            filename, payload = uploaded
        else:
            filename = 'upload.bin'
            payload = uploaded.encode('utf-8') if isinstance(uploaded, str) else b''

        filename = _safe_name(filename)
        training_retained = _store_training_upload(filename, payload, form)
        result = analyse_uploaded_file(filename, payload, training_retained=training_retained)
        output = render_result_page(result).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(output)))
        self.end_headers()
        self.wfile.write(output)

    def log_message(self, *args, **kwargs):
        return


def run_server(host: str = HOST, port: int = PORT) -> HTTPServer:
    server = HTTPServer((host, port), AMLCTUploadHandler)
    print(f'AML CT upload server running at http://{host}:{port}/upload')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('Stopping AML CT upload server...')
    finally:
        server.server_close()
    return server


def main() -> None:
    run_server()


if __name__ == '__main__':
    main()
