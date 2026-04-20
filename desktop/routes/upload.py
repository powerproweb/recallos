"""
/api/upload — File upload + ingest endpoints.

Accepts file uploads, saves them to a staging directory, and kicks off
a background ingest job via the JobManager.  Also exposes job listing.
"""

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, Query

from recallos.config import RecallOSConfig
from recallos.ingest_engine import (
    get_collection,
    process_file,
    load_config,
    READABLE_EXTENSIONS,
)
from desktop.services.job_manager import JobManager

router = APIRouter(tags=["upload"])

_config = RecallOSConfig()
_jobs = JobManager()

# Staging area for uploaded files
_STAGING_DIR = Path(os.path.expanduser("~/.recallos/staging"))


def _ingest_staged_files(
    staging_dir: str,
    domain: str,
    vault_path: str,
) -> dict:
    """Ingest all readable files from a staging directory into the vault.

    Called inside a background thread by the JobManager.
    """
    staging = Path(staging_dir)
    vault = vault_path
    collection = get_collection(vault)

    nodes = [{"name": "general", "description": "Uploaded files"}]

    # Try loading config for node routing if available
    try:
        cfg = load_config(staging_dir)
        nodes = cfg.get("nodes", nodes)
    except Exception:
        pass

    files = [
        f for f in staging.rglob("*") if f.is_file() and f.suffix.lower() in READABLE_EXTENSIONS
    ]
    total_records = 0
    files_processed = 0

    for filepath in files:
        records = process_file(
            filepath=filepath,
            project_path=staging,
            collection=collection,
            domain=domain,
            nodes=nodes,
            agent="desktop-upload",
            dry_run=False,
        )
        if records > 0:
            files_processed += 1
            total_records += records

    # Clean up staging dir
    shutil.rmtree(staging_dir, ignore_errors=True)

    return {
        "files_processed": files_processed,
        "records_added": total_records,
        "domain": domain,
    }


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    domain: str = Form(default="uploads"),
):
    """Accept file uploads, stage them, and start a background ingest job."""
    # Create a unique staging directory
    staging = Path(tempfile.mkdtemp(dir=str(_STAGING_DIR.parent), prefix="staging_"))
    staging.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        dest = staging / f.filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as out:
            content = await f.read()
            out.write(content)
        saved.append(f.filename)

    # Create and launch background job
    job_id = _jobs.create_job(
        "ingest",
        params={"domain": domain, "files": saved, "staging_dir": str(staging)},
    )
    _jobs.run_in_background(
        job_id,
        _ingest_staged_files,
        staging_dir=str(staging),
        domain=domain,
        vault_path=_config.vault_path,
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "files_received": len(saved),
        "domain": domain,
    }


@router.get("/jobs")
def list_jobs(limit: int = Query(default=20, ge=1, le=100)):
    """List recent jobs (newest first)."""
    return {"jobs": _jobs.list_jobs(limit=limit)}


@router.get("/jobs/{job_id}")
def get_job(job_id: int):
    """Get a single job's details."""
    job = _jobs.get_job(job_id)
    if not job:
        return {"error": f"Job {job_id} not found"}
    return job
