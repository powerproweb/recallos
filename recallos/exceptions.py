"""
RecallOS structured exceptions.

Core library modules raise these instead of calling sys.exit().
CLI wrappers catch them and translate to user-friendly messages + exit codes.
The desktop API layer catches them and returns structured JSON error responses.
"""


class RecallOSError(Exception):
    """Base exception for all RecallOS errors."""

    pass


class VaultNotFoundError(RecallOSError):
    """Raised when the Data Vault directory or ChromaDB collection cannot be found."""

    def __init__(self, vault_path: str, detail: str = None):
        self.vault_path = vault_path
        msg = f"No Data Vault found at {vault_path}"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


class ConfigNotFoundError(RecallOSError):
    """Raised when recallos.yaml (or legacy mempal.yaml) is missing from the project directory."""

    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        super().__init__(
            f"No recallos.yaml found in {project_dir}. Run: recallos init {project_dir}"
        )


class QueryError(RecallOSError):
    """Raised when a vault query fails."""

    def __init__(self, detail: str):
        super().__init__(f"Query error: {detail}")


class IngestError(RecallOSError):
    """Raised when file ingest fails."""

    def __init__(self, detail: str):
        super().__init__(f"Ingest error: {detail}")


class DirectoryNotFoundError(RecallOSError):
    """Raised when a required directory does not exist."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Directory not found: {path}")
