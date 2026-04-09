import os
import json
import tempfile
from recallos.config import RecallOSConfig


def test_default_config():
    cfg = RecallOSConfig(config_dir=tempfile.mkdtemp())
    assert "vault" in cfg.vault_path
    assert cfg.collection_name == "recallos_records"


def test_config_from_file():
    tmpdir = tempfile.mkdtemp()
    with open(os.path.join(tmpdir, "config.json"), "w") as f:
        json.dump({"vault_path": "/custom/vault"}, f)
    cfg = RecallOSConfig(config_dir=tmpdir)
    assert cfg.vault_path == "/custom/vault"


def test_env_override():
    os.environ["RECALLOS_VAULT_PATH"] = "/env/vault"
    cfg = RecallOSConfig(config_dir=tempfile.mkdtemp())
    assert cfg.vault_path == "/env/vault"
    del os.environ["RECALLOS_VAULT_PATH"]


def test_init():
    tmpdir = tempfile.mkdtemp()
    cfg = RecallOSConfig(config_dir=tmpdir)
    cfg.init()
    assert os.path.exists(os.path.join(tmpdir, "config.json"))
