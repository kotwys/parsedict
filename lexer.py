from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from docx.text.paragraph import Paragraph

@dataclass
class Format:
    font: str | None
    bold: bool
    italic: bool
    sup: bool
    sub: bool


@dataclass
class Character:
    char: str
    format: Format


class Token(ABC):
    @property
    @abstractmethod
    def text(self):
        pass

@dataclass
class SpaceToken(Token):
    @property
    def text(self):
        return ' '

@dataclass
class WordToken(Token):
    chars: list[Character]
    punctuation: bool = False

    @property
    def text(self):
        return ''.join(map(lambda c: c.char, self.chars))

    @property
    def bold(self):
        return self.chars[0].format.bold

    @property
    def italic(self):
        return self.chars[0].format.italic


def extract_characters(par: Paragraph) -> Iterable[Character]:
    for run in par.runs:
        if not run.text:
            continue

        format = Format(
            font=run.font.name,
            bold=run.bold,
            italic=run.italic,
            sup=run.font.superscript,
            sub=run.font.subscript,
        )
        for c in run.text:
            yield Character(c, format)


LETTER_LIKE = {'-', '′'}

def tokenize(par: Paragraph) -> Iterable[Token]:
    buffer = []
    had_space = False

    def flush_buffer() -> Token:
        nonlocal buffer
        token = WordToken(buffer)
        buffer = []
        return token

    for char in extract_characters(par):
        c = char.char
        if c.isspace():
            if buffer:
                yield flush_buffer()
            if not had_space:
                yield SpaceToken()
            had_space = True
            continue

        had_space = False
        if c.isalpha() or c in LETTER_LIKE or char.format.font == "Lingua":
            buffer.append(char)
        else:
            if buffer:
                yield flush_buffer()
            yield WordToken([char], punctuation=True)

    if buffer:
        yield flush_buffer()
