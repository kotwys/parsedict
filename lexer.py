from collections.abc import Iterator
from dataclasses import dataclass
from typing import NamedTuple

from docx import Document
from docx.text.paragraph import Paragraph


@dataclass(slots=True, frozen=True)
class Format:
    """Represents the formatting style of a character."""
    font: str | None = None
    bold: bool = False
    italic: bool = False
    sup: bool = False


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
        )
        for c in run.text:
            yield Character(c, format)


CONTINUATORS = {'♦', '●', '○'}

def extract_entries(doc: Document) -> Iterator[list[Character]]:
    """Extract groups of characters representing individual entries."""
    buf = []
    for par in doc.paragraphs:
        chars = list(extract_characters(par))
        is_continuation = (not chars[0].format.bold
                           or chars[0].char in CONTINUATORS)
        # doubtedly would be an entry
        if len(chars) < 3:
            if buf:
                yield buf
            buf = []
        elif not is_continuation:
            if buf:
                yield buf
            buf = chars
        else:
            buf.append(Character('\n', Format()))
            buf.extend(chars)
    if buf:
        yield buf
