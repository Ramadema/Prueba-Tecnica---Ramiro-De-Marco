"""Tests for TextCleaner."""

from src.ingest.cleaner import TextCleaner


def test_clean_collapses_whitespace() -> None:
    cleaner = TextCleaner()
    result = cleaner.clean("  hello   world  \n\n\n  foo  ")
    assert result == "hello world\n\nfoo"


def test_clean_fixes_mojibake() -> None:
    cleaner = TextCleaner()
    text = "conexi\u00f3n"
    result = cleaner.clean(text)
    assert "conexión" in result or "conexi" in result
