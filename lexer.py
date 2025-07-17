"""This module describes basic units that are processed while parsing.

The unit of the text is a single character (corresponding to a single Unicode
codepoint) supplied with a formatting information.
"""
from collections.abc import Iterator
from dataclasses import dataclass
from typing import NamedTuple

from docx import Document
from docx.text.paragraph import Paragraph


@dataclass(slots=True, frozen=True)
class Format:
    """Represents the formatting style of a character."""

    font: str | None = None
    """The font name of the character (`None` if not specified.)."""
    bold: bool = False
    """Whether the character is bold."""
    italic: bool = False
    """Whether the character is italic."""
    sup: bool = False
    """Whether the character is a superscript."""
    sub: bool = False
    """Whether the character is a subscript."""


class Character(NamedTuple):
    """Represents a single character inside a paragraph.

    Always represents a single Unicode codepoint, so compound graphemes get
    split into different `Character` instances.
    """
    char: str
    format: Format


def extract_characters(par: Paragraph) -> Iterator[Character]:
    """Get visible characters from the paragraph."""
    for run in par.runs:
        if not run.text:
            continue

        format = Format(
            font=run.font.name,
            bold=bool(run.bold),
            italic=bool(run.italic),
            sup=bool(run.font.superscript),
            sub=bool(run.font.subscript),
        )
        for c in run.text:
            yield Character(c, format)


CONTINUATORS = {'♦', '●', '○'}

def extract_entries(doc: Document) -> Iterator[list[Character]]:
    """Extract groups of characters representing individual entries.

    A separate paragraph is considered to be a part of an entry if it is not
    shorter than three characters.

    If a paragraph begins with a bold character that isn't one of the section
    begin markers, then it is considered to be a beginning of a new entry.
    Otherwise, the paragraph is considered to be a continuation of the previous
    entry. Several paragraphs that constitute a single entry get joined by a
    newline character.
    """
    buf = []
    for par in doc.paragraphs:
        chars = list(extract_characters(par))
        # doubtedly would be an entry
        if len(chars) < 3:
            if buf:
                yield buf
            buf = []
        elif chars[0].format.bold and chars[0].char not in CONTINUATORS:
            if buf:
                yield buf
            buf = chars
        else:
            buf.append(Character('\n', Format()))
            buf.extend(chars)
    if buf:
        yield buf
