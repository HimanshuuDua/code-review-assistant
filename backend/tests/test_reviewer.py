from backend.schemas import CommentType, ReviewComment, Severity
from backend.services.reviewer import _parse_comments


def test_parse_json_array():
    raw = '[{"type": "bug", "severity": "high", "message": "Fix this", "line": 3}]'
    comments = _parse_comments(raw)
    assert len(comments) == 1
    assert comments[0].type == CommentType.BUG
    assert comments[0].severity == Severity.HIGH
    assert comments[0].line == 3


def test_parse_markdown_fenced_json():
    raw = '```json\n[{"type": "style", "severity": "low", "message": "Rename var"}]\n```'
    comments = _parse_comments(raw)
    assert comments[0].type == CommentType.STYLE


def test_parse_fallback_on_invalid_json():
    raw = "This code needs improvement."
    comments = _parse_comments(raw)
    assert len(comments) == 1
    assert comments[0].message == raw
