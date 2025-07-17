"""This module contains some utilities for working with markup."""
from dataclasses import dataclass
import html
from typing import Mapping

from lexer import Character, Format


type MarkupNode = str | tuple[str, *tuple[MarkupNode, ...]]


HTML_TAG_NAME: Mapping[str, str] = {
    'italic': 'em',
    'bold': 'strong',
    'sup': 'sup',
    'sub': 'sub',
}


def markup_to_html(node: MarkupNode) -> str:
    if isinstance(node, str):
        return html.escape(node)
    elif isinstance(node, tuple):
        tag, *children = node
        html_tag = HTML_TAG_NAME[tag]
        inner_html = ''.join(markup_to_html(child)
                             for child in children)
        return f'<{html_tag}>{inner_html}</{html_tag}>'
    else:
        raise TypeError('Node should be either a str or a tuple')



@dataclass(slots=True)
class Markup:
    """A block of marked up text.

    A block consist of markup nodes, each being either a plain string,
    or a tuple of form `(tag, child1, child2, ...)`, where `tag` is a
    string denoting the type of the node (italic, superscript, etc.) and
    the following elements are child nodes of the current node.
    """
    content: list[MarkupNode]

    def to_html(self) -> str:
        """Transform the markup into a HTML string."""
        return ''.join(markup_to_html(n) for n in self.content)
