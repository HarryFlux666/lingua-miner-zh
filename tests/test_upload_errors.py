import errno
import tempfile
from unittest.mock import patch

import starlette.formparsers
from fastapi.testclient import TestClient

from app import main


def test_large_upload_spools_on_app_data_drive():
    assert tempfile.gettempdir() == str(main.config.TEMP_DIR)
    with tempfile.SpooledTemporaryFile(max_size=1024) as f:
        f.write(b'x' * 2048)
        assert f._rolled


def test_spool_failure_is_reported_without_creating_a_job():
    client = TestClient(main.app)
    before = set(main.jobs.JOBS)
    spool = starlette.formparsers.SpooledTemporaryFile

    def no_space(*args, **kwargs):
        f = spool(*args, **kwargs)
        def fail_rollover():
            raise OSError(errno.ENOSPC, 'No space left on device')
        f.rollover = fail_rollover
        return f

    with patch.object(starlette.formparsers, 'SpooledTemporaryFile', no_space):
        response = client.post('/api/sessions/upload', files={'file': ('large.mp4', b'x' * (2 * 1024 * 1024))})
    assert response.status_code == 507
    assert response.json()['error_key'] == 'err.upload_space'
    assert set(main.jobs.JOBS) == before


def test_invalid_multipart_returns_upload_error():
    client = TestClient(main.app)
    response = client.post('/api/sessions/upload', content=b'bad body', headers={'Content-Type':'multipart/form-data'})
    assert response.status_code == 400
    assert response.json()['error_key'] == 'err.upload_body'


def test_other_404_stays_unchanged():
    response = TestClient(main.app).get('/api/jobs/does-not-exist')
    assert response.status_code == 404
    assert response.json() == {'error':'not found'}
