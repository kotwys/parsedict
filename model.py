from abc import ABC
from dataclasses import dataclass

@dataclass
class MarkupNode(ABC):
    pass

@dataclass
class TextNode(MarkupNode):
    content: str

@dataclass
class Span(MarkupNode):
    children: list[MarkupNode]

@dataclass
class Superscript(MarkupNode):
    children: list[MarkupNode]

@dataclass
class Example:
    text: str
    description: str

@dataclass
class Sense:
    translation: str
    examples: list[Example]

@dataclass
class Entry:
    headword: str
    pronunciation: Span
    senses: list[Sense]
