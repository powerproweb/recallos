"""
test_upload.py — Tests for job manager and upload/ingest API.
"""

import time

from desktop.services.job_manager import JobManager


def test_job_manager_create_job():
    """Creating a job returns an integer ID."""
    jm = JobManager()
    job_id = jm.create_job("test", params={"foo": "bar"})
    assert isinstance(job_id, int)
    assert job_id > 0


def test_job_manager_get_job():
    jm = JobManager()
    job_id = jm.create_job("test")
    job = jm.get_job(job_id)
    assert job is not None
    assert job["type"] == "test"
    assert job["status"] == "pending"


def test_job_manager_list_jobs():
    jm = JobManager()
    jm.create_job("list_test_a")
    jm.create_job("list_test_b")
    jobs = jm.list_jobs(limit=2)
    assert len(jobs) >= 2


def test_job_manager_get_nonexistent():
    jm = JobManager()
    assert jm.get_job(999999) is None


def test_job_manager_run_in_background_success():
    """A successful background job transitions to 'done'."""
    jm = JobManager()
    job_id = jm.create_job("bg_test")

    def _task():
        return {"result": "ok"}

    jm.run_in_background(job_id, _task)
    time.sleep(0.5)  # give thread time to complete

    job = jm.get_job(job_id)
    assert job["status"] == "done"


def test_job_manager_run_in_background_failure():
    """A failing background job transitions to 'failed'."""
    jm = JobManager()
    job_id = jm.create_job("bg_fail")

    def _task():
        raise RuntimeError("intentional test failure")

    jm.run_in_background(job_id, _task)
    time.sleep(0.5)

    job = jm.get_job(job_id)
    assert job["status"] == "failed"
    assert "intentional" in (job["result"] or "")


def test_ingest_staged_files_function_exists():
    """The ingest worker function is importable."""
    from desktop.routes.upload import _ingest_staged_files

    assert callable(_ingest_staged_files)
