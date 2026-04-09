import os
import tempfile
import shutil
import yaml
import chromadb
from recallos.ingest_engine import mine


def test_project_ingest():
    tmpdir = tempfile.mkdtemp()
    # Create a mini project
    os.makedirs(os.path.join(tmpdir, "backend"))
    with open(os.path.join(tmpdir, "backend", "app.py"), "w") as f:
        f.write("def main():\n    print('hello world')\n" * 20)
    # Create config
    with open(os.path.join(tmpdir, "recallos.yaml"), "w") as f:
        yaml.dump(
            {
                "domain": "test_project",
                "nodes": [
                    {"name": "backend", "description": "Backend code"},
                    {"name": "general", "description": "General"},
                ],
            },
            f,
        )

    vault_path = os.path.join(tmpdir, "vault")
    mine(tmpdir, vault_path)

    # Verify
    client = chromadb.PersistentClient(path=vault_path)
    col = client.get_collection("recallos_records")
    assert col.count() > 0

    # Release ChromaDB handles before cleanup (required on Windows)
    del col, client
    shutil.rmtree(tmpdir, ignore_errors=True)
