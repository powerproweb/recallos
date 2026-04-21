"""
test_phase3.py — Tests for Phase 3: document extraction, ranking, saved searches.
"""

from desktop.services.search_service import highlight_snippet, rank_results
from recallos.extractors import (
    BaseExtractor,
    can_extract,
    extract_text,
    register_extractor,
    EXTRACTABLE_EXTENSIONS,
)


# ---------------------------------------------------------------------------
# 3.1 Document extractors
# ---------------------------------------------------------------------------


def test_extractable_extensions_include_pdf_docx():
    assert ".pdf" in EXTRACTABLE_EXTENSIONS
    assert ".docx" in EXTRACTABLE_EXTENSIONS


def test_can_extract_pdf():
    assert can_extract("file.pdf") is True


def test_can_extract_docx():
    assert can_extract("document.docx") is True


def test_can_extract_txt_false():
    assert can_extract("readme.txt") is False


def test_extract_text_missing_file():
    result = extract_text("/nonexistent/file.pdf")
    assert result == ""


def test_extract_text_unsupported_extension():
    result = extract_text("file.xyz")
    assert result == ""


def test_register_custom_extractor():
    class FakeExtractor(BaseExtractor):
        def extensions(self):
            return {".fake"}

        def extract(self, path):
            return "fake content"

    register_extractor(FakeExtractor())
    assert can_extract("file.fake") is True


# ---------------------------------------------------------------------------
# 3.2 Advanced ranking
# ---------------------------------------------------------------------------


def test_rank_results_deduplication():
    results = [
        {"text": "same content here", "similarity": 0.9, "domain": "a", "node": "b"},
        {"text": "same content here", "similarity": 0.85, "domain": "a", "node": "c"},
        {"text": "different content", "similarity": 0.8, "domain": "a", "node": "b"},
    ]
    ranked = rank_results(results, query="test")
    # Should have removed the duplicate
    assert len(ranked) == 2


def test_rank_results_domain_boost():
    results = [
        {"text": "alpha content", "similarity": 0.8, "domain": "target", "node": "x"},
        {"text": "beta content", "similarity": 0.82, "domain": "other", "node": "y"},
    ]
    ranked = rank_results(results, query="test", domain_filter="target")
    # Domain match should boost "alpha" above "beta" despite lower base similarity
    assert ranked[0]["domain"] == "target"


def test_rank_results_adds_ranked_score():
    results = [{"text": "hello world", "similarity": 0.9, "domain": "d", "node": "n"}]
    ranked = rank_results(results, query="hello")
    assert "ranked_score" in ranked[0]
    assert "snippet" in ranked[0]


def test_highlight_snippet_finds_match():
    text = "The quick brown fox jumps over the lazy dog in a beautiful meadow"
    snippet = highlight_snippet(text, "fox")
    assert "fox" in snippet


def test_highlight_snippet_no_match():
    text = "The quick brown fox"
    snippet = highlight_snippet(text, "elephant")
    # Should return the beginning of the text
    assert "quick" in snippet


def test_highlight_snippet_empty():
    assert highlight_snippet("", "test") == ""


# ---------------------------------------------------------------------------
# 3.3 Saved searches
# ---------------------------------------------------------------------------


def test_save_and_list_searches():
    from desktop.routes.search import save_search, list_saved_searches, SaveSearchRequest

    body = SaveSearchRequest(query="auth decisions", domain="myapp", name="auth test")
    result = save_search(body)
    assert result["status"] == "saved"

    searches = list_saved_searches(limit=5)
    assert len(searches["searches"]) >= 1
    found = any(s["query"] == "auth decisions" for s in searches["searches"])
    assert found


def test_delete_saved_search():
    from desktop.routes.search import (
        save_search,
        list_saved_searches,
        delete_saved_search,
        SaveSearchRequest,
    )

    body = SaveSearchRequest(query="delete-me-test-xyz")
    save_search(body)

    searches = list_saved_searches(limit=10)
    target = next(s for s in searches["searches"] if s["query"] == "delete-me-test-xyz")

    result = delete_saved_search(target["id"])
    assert result["status"] == "deleted"
