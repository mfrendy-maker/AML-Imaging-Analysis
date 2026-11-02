import io

from PIL import Image

from aml_imaging_analysis import ct_upload_demo


def _png_image() -> bytes:
    image = Image.new('L', (16, 16), 40)
    image.putpixel((12, 12), 255)
    output = io.BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()


def test_analysis_does_not_present_intensity_as_tumor_localization():
    result = ct_upload_demo.analyse_uploaded_file('sample.png', _png_image())
    page = ct_upload_demo.render_result_page(result)

    assert 'overlay_data_url' not in result
    assert result['high_intensity_fraction'] is not None
    assert 'does not detect or locate tumors' in page
    assert 'severity map' not in page.lower()
    assert 'lesion proxy' not in page.lower()


def test_training_consent_is_optional_and_unchecked_by_default():
    assert 'name="training_consent" type="checkbox" value="yes"' in ct_upload_demo.HTML_PAGE
    assert 'name="training_consent" type="checkbox" value="yes" checked' not in ct_upload_demo.HTML_PAGE


def test_training_upload_requires_explicit_consent(tmp_path, monkeypatch):
    training_dir = tmp_path / 'training_uploads'
    monkeypatch.setattr(ct_upload_demo, 'TRAINING_UPLOAD_DIR', training_dir)

    assert not ct_upload_demo._store_training_upload('sample.png', b'image', {})
    assert not training_dir.exists()

    assert ct_upload_demo._store_training_upload(
        'sample.png', b'image', {'training_consent': 'yes'}
    )
    saved_files = list(training_dir.iterdir())
    assert len(saved_files) == 1
    assert saved_files[0].read_bytes() == b'image'