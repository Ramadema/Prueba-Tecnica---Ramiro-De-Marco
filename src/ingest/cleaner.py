"""Text cleaning and normalization utilities."""

import re
import unicodedata

import ftfy

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_NEWLINES = re.compile(r"\n{3,}")
_MULTI_SPACES = re.compile(r"[^\S\n]+")


class TextCleaner:
    """Normalizes and cleans raw document text."""

    def clean(self, text: str) -> str:
        """Apply full cleaning pipeline to raw text."""
        text = ftfy.fix_text(text)
        text = unicodedata.normalize("NFC", text)
        text = _CONTROL_CHARS.sub("", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = _MULTI_SPACES.sub(" ", text)
        text = _MULTI_NEWLINES.sub("\n\n", text)
        text = re.sub(r" *\n *", "\n", text)
        return text.strip()
