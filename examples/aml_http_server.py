from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path

HOST = '127.0.0.1'
PORT = 8001
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
FIGURE_PATH = DATA_DIR / 'aml_publication_ready_figure.png'

PAYLOAD = {
    'collection': 'CMB-AML',
    'patient_count': 6,
    'biomarker': {
        'name': 'AML lesion intensity trajectory',
        'definition': 'A surrogate imaging biomarker based on the change in lesion intensity and tumor burden over longitudinal follow-up.',
        'measurement': 'relative lesion signal / tumor burden change between baseline and follow-up imaging',
        'interpretation': 'Higher sustained lesion intensity or tumor burden increase is treated as a progression-like signature in this demo analysis.'
    },
    'analysis': {
        'top_similarity_pair': {
            'patient_a': 'MSB-02960',
            'patient_b': 'MSB-06711',
            'similarity': 0.9999999999999999,
        },
        'clinical_focus': ['demographics', 'treatment', 'outcomes'],
        'image_focus': ['CT', 'MRI', 'PET', 'radiomics'],
        'biomarker_focus': 'lesion intensity trajectory and tumor burden change',
        'longitudinal_pattern': 'increasing biomarker intensity over follow-up',
        'interpretation': (
            'This patient-matched AML analysis integrates clinical metadata with multimodal imaging features '
            'to describe disease similarity and biomarker progression.'
        ),
        'analysis_process': [
            'align records by patient ID and timepoint',
            'compare baseline and follow-up imaging features',
            'quantify lesion intensity / tumor burden change',
            'rank patient similarity using matched clinical-imaging profiles'
        ]
    }
}


def render_html():
    analysis = PAYLOAD['analysis']
    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>AML Imaging Analysis</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background: #f5f8fc;
          color: #1d2733;
          margin: 0;
          padding: 24px;
        }}
        .container {{
          max-width: 1100px;
          margin: 0 auto;
          background: white;
          border-radius: 16px;
          box-shadow: 0 8px 28px rgba(0,0,0,0.08);
          padding: 28px;
        }}
        h1 {{ margin-top: 0; }}
        .grid {{
          display: grid;
          grid-template-columns: 1.1fr 1.4fr;
          gap: 24px;
          align-items: start;
        }}
        .card {{
          background: #f9fbff;
          border: 1px solid #dfeaf7;
          border-radius: 12px;
          padding: 16px 18px;
          margin-bottom: 14px;
        }}
        .label {{
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          font-weight: bold;
          color: #557aa6;
        }}
        ul {{ margin: 10px 0 0 20px; padding: 0; }}
        img {{ width: 100%; border-radius: 12px; border: 1px solid #dfeaf7; }}
        pre {{
          white-space: pre-wrap;
          word-break: break-word;
          background: #0f172a;
          color: #e2e8f0;
          padding: 14px;
          border-radius: 10px;
          font-size: 12px;
        }}
        @media (max-width: 800px) {{
          .grid {{ grid-template-columns: 1fr; }}
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>AML Imaging Analysis</h1>
        <div class="grid">
          <div>
            <div class="card">
              <div class="label">Collection</div>
              <p><strong>{PAYLOAD['collection']}</strong></p>
            </div>
            <div class="card">
              <div class="label">Patient count</div>
              <p><strong>{PAYLOAD['patient_count']}</strong></p>
            </div>
            <div class="card">
              <div class="label">Top similarity pair</div>
              <p><strong>{analysis['top_similarity_pair']['patient_a']}</strong> vs <strong>{analysis['top_similarity_pair']['patient_b']}</strong></p>
              <p>Similarity: <strong>{analysis['top_similarity_pair']['similarity']}</strong></p>
            </div>
            <div class="card">
              <div class="label">Biomarker</div>
              <p><strong>{PAYLOAD['biomarker']['name']}</strong></p>
              <p>{PAYLOAD['biomarker']['definition']}</p>
              <p><em>Measurement:</em> {PAYLOAD['biomarker']['measurement']}</p>
            </div>
            <div class="card">
              <div class="label">Clinical focus</div>
              <ul>
                {''.join(f'<li>{item}</li>' for item in analysis['clinical_focus'])}
              </ul>
            </div>
            <div class="card">
              <div class="label">Image focus</div>
              <ul>
                {''.join(f'<li>{item}</li>' for item in analysis['image_focus'])}
              </ul>
            </div>
          </div>
          <div>
            <div class="card">
              <div class="label">Figure</div>
              <img src="/data/aml_publication_ready_figure.png" alt="AML publication ready figure" />
            </div>
            <div class="card">
              <div class="label">Biomarker focus</div>
              <p>{analysis['biomarker_focus']}</p>
            </div>
            <div class="card">
              <div class="label">Longitudinal pattern</div>
              <p>{analysis['longitudinal_pattern']}</p>
            </div>
            <div class="card">
              <div class="label">Analysis process</div>
              <ul>
                {''.join(f'<li>{item}</li>' for item in analysis['analysis_process'])}
              </ul>
            </div>
            <div class="card">
              <div class="label">Interpretation</div>
              <p>{analysis['interpretation']}</p>
            </div>
            <div class="card">
              <div class="label">Raw JSON</div>
              <pre>{json.dumps(PAYLOAD, indent=2)}</pre>
            </div>
          </div>
        </div>
      </div>
    </body>
    </html>
    """


class AMLAnalysisHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/analysis/example':
            body = render_html().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/analysis/example.json':
            body = json.dumps(PAYLOAD).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith('/data/'):
            relative_path = self.path[len('/data/'):]
            file_path = DATA_DIR / relative_path
            if file_path.exists() and file_path.is_file():
                body = file_path.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                body = b'{"error": "not found"}'
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        else:
            body = b'{"error": "not found"}'
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), AMLAnalysisHandler)
    print(f'Serving AML example at http://{HOST}:{PORT}/analysis/example')
    server.serve_forever()
