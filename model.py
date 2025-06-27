from abc import ABC
from dataclasses import dataclass
from typing import Mapping, Optional

@dataclass
class MarkupNode(ABC):
    pass

@dataclass
class TextNode(MarkupNode):
    content: str

@dataclass
class Superscript(MarkupNode):
    children: list[MarkupNode]

@dataclass
class Italic(MarkupNode):
    """Italic markup.

    Corresponds to the HTML element `em`."""
    children: list[MarkupNode]

@dataclass
class Example:
    text: list[MarkupNode]
    description: list[MarkupNode]

@dataclass
class Sense:
    label: Optional[str]
    translation: list[MarkupNode]
    examples: Mapping[str, list[Example]]

@dataclass
class Entry:
    headword: str
    pronunciation: Optional[list[MarkupNode]]
    senses: list[Sense]
    commentary: Optional[list[MarkupNode]]
