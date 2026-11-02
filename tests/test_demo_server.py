import importlib.util
from pathlib import Path


def load_demo_server_module():
    file_path = Path(__file__).resolve().parents[1] / 'examples' / 'aml_http_server.py'
    spec = importlib.util.spec_from_file_location('aml_http_server_demo', file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_server_exposes_explicit_biomarker():
    module = load_demo_server_module()
    html = module.render_html()

    assert 'Biomarker' in html
    assert 'lesion intensity' in html.lower()
    assert 'tumor burden' in html.lower() or 'lesion intensity' in html.lower()
