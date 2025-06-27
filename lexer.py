from collections.abc import Iterable
from dataclasses import dataclass
from typing import NamedTuple
from docx.text.paragraph import Paragraph

@dataclass(slots=True, frozen=True)
class Format:
    font: str | None = None
    bold: bool = False
    italic: bool = False
    sup: bool = False


class Character(NamedTuple):
    char: str
    format: Format


def extract_characters(par: Paragraph) -> Iterable[Character]:
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
