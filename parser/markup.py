"""This module contains some utilities for working with markup."""
from dataclasses import dataclass
import html
from typing import Mapping

from lexer import Character, Format


type MarkupNode = str | tuple[str, dict, *tuple[MarkupNode, ...]]


TAGS: Mapping[str, dict] = {
    'italic': {
        'tag': 'i',
    },
    'bold': {
        'tag': 'b',
    },
    'sup': {
        'tag': 'sup',
    },
    'sub': {
        'tag': 'sub',
    },
    'color': {
        'tag': 'font',
        'attrs': {
            'color': {
                'name': 'color',
                'transform': lambda c: f'#{c[0]:02x}{c[1]:02x}{c[2]:02x}',
            },
        },
    },
}


def markup_to_html(node: MarkupNode) -> str:
    if isinstance(node, str):
        return html.escape(node)
    elif isinstance(node, tuple):
        tag_name, attrs, *children = node
        tag = TAGS[tag_name]
        html_tag = tag['tag']
        html_attrs = ''
        if 'attrs' in tag:
            for attr, spec in tag['attrs'].items():
                value = attrs[attr]
                if 'transform' in spec:
                    value = spec['transform'](value)
                escaped = html.escape(value, quote=True)
                html_attrs += f' {spec['name']}="{escaped}"'
        inner_html = ''.join(markup_to_html(child)
                             for child in children)
        return f'<{html_tag}{html_attrs}>{inner_html}</{html_tag}>'
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

    def __bool__(self) -> bool:
        return bool(self.content)
