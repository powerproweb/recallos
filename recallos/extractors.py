"""
recallos/extractors.py — Pluggable document text extraction.

Provides a registry of extractors that convert binary file formats
(PDF, DOCX, etc.) into plain text for ingest into the Data Vault.

Usage:
    from recallos.extractors import extract_text, can_extract
    if can_extract(path):
        text = extract_text(path)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger("extractors")


class BaseExtractor(ABC):
    """Interface for document text extractors."""

    @abstractmethod
    def extensions(self) -> set[str]:
        """Return the file extensions this extractor handles (e.g. {'.pdf'})."""
        ...

    @abstractmethod
    def extract(self, path: Path) -> str:
        """Extract plain text from the file at *path*."""
        ...


class PDFExtractor(BaseExtractor):
    """Extract text from PDF files using pdfplumber."""

    def extensions(self) -> set[str]:
        return {".pdf"}

    def extract(self, path: Path) -> str:
        try:
            import pdfplumber
        except ImportError:
            logger.warning("pdfplumber not installed — skipping %s", path.name)
            return ""

        pages = []
        try:
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
        except Exception as e:
            logger.warning("PDF extraction failed for %s: %s", path.name, e)
            return ""

        return "\n\n".join(pages)


class DOCXExtractor(BaseExtractor):
    """Extract text from DOCX files using python-docx."""

    def extensions(self) -> set[str]:
        return {".docx"}

    def extract(self, path: Path) -> str:
        try:
            import docx
        except ImportError:
            logger.warning("python-docx not installed — skipping %s", path.name)
            return ""

        try:
            doc = docx.Document(str(path))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            logger.warning("DOCX extraction failed for %s: %s", path.name, e)
            return ""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_EXTRACTORS: list[BaseExtractor] = [
    PDFExtractor(),
    DOCXExtractor(),
]

_EXT_MAP: dict[str, BaseExtractor] = {}
for _ex in _EXTRACTORS:
    for _ext in _ex.extensions():
        _EXT_MAP[_ext] = _ex


def register_extractor(extractor: BaseExtractor) -> None:
    """Register a custom extractor at runtime."""
    _EXTRACTORS.append(extractor)
    for ext in extractor.extensions():
        _EXT_MAP[ext] = extractor


def can_extract(path: str | Path) -> bool:
    """Return True if an extractor exists for this file type."""
    return Path(path).suffix.lower() in _EXT_MAP


def extract_text(path: str | Path) -> str:
    """Extract text from a file using the appropriate extractor.

    Returns empty string if no extractor is available or extraction fails.
    """
    p = Path(path)
    ext = p.suffix.lower()
    extractor = _EXT_MAP.get(ext)
    if not extractor:
        return ""
    return extractor.extract(p)


# Extensions that extractors handle (for adding to READABLE_EXTENSIONS)
EXTRACTABLE_EXTENSIONS = set(_EXT_MAP.keys())
