import os
import tempfile
import shutil
import chromadb
from recallos.conversation_ingest import mine_convos


def test_convo_ingest():
    tmpdir = tempfile.mkdtemp()
    with open(os.path.join(tmpdir, "chat.txt"), "w") as f:
        f.write(
            "> What is memory?\nMemory is persistence.\n\n> Why does it matter?\nIt enables continuity.\n\n> How do we build it?\nWith structured storage.\n"
        )

    vault_path = os.path.join(tmpdir, "vault")
    mine_convos(tmpdir, vault_path, domain="test_convos")

    client = chromadb.PersistentClient(path=vault_path)
    col = client.get_collection("recallos_records")
    assert col.count() >= 2

    # Verify search works
    results = col.query(query_texts=["memory persistence"], n_results=1)
    assert len(results["documents"][0]) > 0

    # Release ChromaDB handles before cleanup (required on Windows)
    del col, client
    shutil.rmtree(tmpdir, ignore_errors=True)
