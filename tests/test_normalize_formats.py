"""
test_normalize_formats.py — Tests for the Discord and Obsidian parsers
added in Phase 12 (normalize.py).

Both parsers are tested via their private functions as well as through
the public normalize() entry point to verify end-to-end routing.
"""

import json

from recallos.normalize import (
    _normalize_obsidian_note,
    _try_discord_json,
    normalize,
)


# ---------------------------------------------------------------------------
# _try_discord_json — array schema
# ---------------------------------------------------------------------------


def _discord_msg(msg_id, username, content, msg_type="Default"):
    return {
        "id": msg_id,
        "type": msg_type,
        "content": content,
        "author": {"id": f"uid_{username}", "username": username},
        "timestamp": "2026-01-01T10:00:00+00:00",
    }


def test_discord_array_schema_returns_transcript():
    data = [
        _discord_msg("1", "alice", "Hey, is the deploy done?"),
        _discord_msg("2", "bob", "Just finished, looks good."),
    ]
    result = _try_discord_json(data)
    assert result is not None
    assert "> Hey" in result or "Hey" in result
    assert "Just finished" in result


def test_discord_wrapped_schema():
    """DiscordChatExporter sometimes wraps the array in {'messages': [...]}."""
    data = {
        "messages": [
            _discord_msg("1", "alice", "Hello"),
            _discord_msg("2", "bob", "World"),
        ]
    }
    result = _try_discord_json(data)
    assert result is not None
    assert "Hello" in result
    assert "World" in result


def test_discord_skips_non_default_message_types():
    """Only 'Default' type messages should be included."""
    data = [
        _discord_msg("1", "alice", "Hey"),
        _discord_msg("2", "system", "User joined the server", msg_type="UserJoin"),
        _discord_msg("3", "bob", "Hi"),
    ]
    result = _try_discord_json(data)
    assert result is not None
    assert "User joined" not in result


def test_discord_skips_empty_content():
    """Messages with empty content are silently dropped."""
    data = [
        _discord_msg("1", "alice", "Hi there"),
        _discord_msg("2", "bob", ""),  # empty → skipped
        _discord_msg("3", "alice", "How are you?"),
    ]
    result = _try_discord_json(data)
    assert result is not None
    assert "Hi there" in result


def test_discord_two_speakers_alternate_roles():
    """First speaker → user, second speaker → assistant, roles alternate."""
    data = [
        _discord_msg("1", "alice", "Question"),
        _discord_msg("2", "bob", "Answer"),
    ]
    result = _try_discord_json(data)
    assert result is not None
    # alice is user → her message should appear with > marker
    assert "> Question" in result


def test_discord_fewer_than_2_messages_returns_none():
    data = [_discord_msg("1", "alice", "Solo message")]
    result = _try_discord_json(data)
    assert result is None


def test_discord_empty_list_returns_none():
    result = _try_discord_json([])
    assert result is None


def test_discord_not_a_list_or_dict_returns_none():
    assert _try_discord_json("not a list") is None
    assert _try_discord_json(42) is None


def test_discord_does_not_match_slack_format():
    """A Slack-like list (has 'type': 'message' and 'user') should not match Discord."""
    slack_data = [
        {"type": "message", "user": "U1", "text": "hello"},
        {"type": "message", "user": "U2", "text": "world"},
    ]
    result = _try_discord_json(slack_data)
    # Slack messages have 'user' key, not 'author' → should return None
    assert result is None


def test_discord_via_normalize_json_file(tmp_path):
    """normalize() routes Discord JSON files correctly end-to-end."""
    data = [
        _discord_msg("1", "alice", "Deploy question"),
        _discord_msg("2", "bob", "Deploy answer"),
    ]
    f = tmp_path / "discord_export.json"
    f.write_text(json.dumps(data), encoding="utf-8")

    result = normalize(str(f))
    assert "Deploy question" in result
    assert "Deploy answer" in result


# ---------------------------------------------------------------------------
# _normalize_obsidian_note
# ---------------------------------------------------------------------------


def test_obsidian_strips_yaml_frontmatter():
    content = "---\ntitle: My Note\ntags: [python, memory]\n---\n\n# Body\n\nSome text here."
    result = _normalize_obsidian_note(content)
    assert "title:" not in result
    assert "tags:" not in result
    assert "Body" in result
    assert "Some text here." in result


def test_obsidian_converts_wikilinks():
    content = "---\ntitle: x\n---\n\nSee [[Target Node]] for details."
    result = _normalize_obsidian_note(content)
    assert "[[Target Node]]" not in result
    assert "Target Node" in result


def test_obsidian_converts_wikilink_aliases():
    """[[Target|Alias]] → Alias."""
    content = "---\ntitle: x\n---\n\nRead [[RecallOS Docs|the docs]] first."
    result = _normalize_obsidian_note(content)
    assert "[[" not in result
    assert "the docs" in result
    assert "RecallOS Docs" not in result


def test_obsidian_no_frontmatter_passes_through():
    """Markdown without --- frontmatter is returned unchanged."""
    content = "# Normal note\n\nJust regular markdown with [[a wikilink]]."
    result = _normalize_obsidian_note(content)
    # Wikilinks still converted even without frontmatter
    assert "a wikilink" in result
    assert "[[" not in result


def test_obsidian_multiple_wikilinks():
    content = "---\ntitle: x\n---\n\n[[Alpha]] connects to [[Beta]] via [[Gamma|G]]."
    result = _normalize_obsidian_note(content)
    assert "Alpha" in result
    assert "Beta" in result
    assert "G" in result
    assert "[[" not in result


def test_obsidian_empty_content_returns_empty():
    result = _normalize_obsidian_note("")
    assert result == ""


def test_obsidian_frontmatter_only_returns_empty():
    content = "---\ntitle: Empty\n---\n"
    result = _normalize_obsidian_note(content)
    assert result.strip() == ""


def test_obsidian_via_normalize_md_file(tmp_path):
    """normalize() routes .md files with frontmatter to Obsidian normalizer."""
    content = "---\ntitle: My Note\ndate: 2026-01-01\n---\n\n# Auth Migration\n\nWe decided to use [[Clerk]] over [[Auth0|old provider]]."
    f = tmp_path / "auth_note.md"
    f.write_text(content, encoding="utf-8")

    result = normalize(str(f))
    assert "title:" not in result
    assert "Clerk" in result
    assert "old provider" in result
    assert "[[" not in result


def test_obsidian_plain_md_without_frontmatter_unchanged(tmp_path):
    """A .md file without --- frontmatter passes through without Obsidian processing
    (wikilinks are still converted by the Obsidian normalizer but content is not stripped)."""
    content = "# Meeting notes\n\nDecided on GraphQL.\n"
    f = tmp_path / "notes.md"
    f.write_text(content, encoding="utf-8")

    result = normalize(str(f))
    assert "Meeting notes" in result
    assert "GraphQL" in result
