from typing import Callable, Mapping, cast

from parsy import Parser, Result, seq, test_item
import regex

from lexer import Character
from model import *


# The keys should be in \uXXXX form for readability.
LINGUA_TO_UNICODE: Mapping[str, str] = {
    '\u041a': 'ə̑',
}


def normalize_char(c: Character) -> str:
    """Convert a character to its normal form.

    When the character is typeset with the Lingua font, it is normalized to the
    corresponding standard Unicode representation.

    When the character is a whitespace, it is normalized to one regular space.

    In other cases, the character is returned as-is.
    """
    if c.format.font == 'Lingua':
        if c.char in LINGUA_TO_UNICODE:
            return LINGUA_TO_UNICODE[c.char]

        code = ord(c.char)
        raise Exception(f'No Unicode symbol matching for {code:x}.')
    if c.char.isspace():
        return ' '
    return c.char


def plain_text(chars: list[Character]) -> str:
    """Collect a list of characters into a plain text string.

    This function effectively strips any formatting.
    """
    return ''.join(map(normalize_char, chars))


def formatted_text(chars: list[Character]) -> list[MarkupNode]:
    """Transform a list of characters to a list of HTML-like markup nodes.

    Currently, only superscripts are accounted.
    """
    sup = False
    i, j = 0, 0
    nodes: list[MarkupNode] = []

    def push_node():
        nonlocal i, j, nodes
        text = plain_text(chars[i:j])
        node = TextNode(text)
        if sup:
            node = Superscript([node])
        nodes.append(node)
        i = j

    while j < len(chars):
        char = chars[j]
        if char.format.sup != sup:
            push_node()
            sup = char.format.sup
        j += 1

    if j > i:
        push_node()

    return nodes


def format_pred(**kwargs) -> Callable[[Character], bool]:
    """Return a predicate matching a character with specific formatting.

    The formatting is checked in accordance with the following keyword
    arguments:
    - `bold` -- if `True`, the character should be in bold, otherwise in normal
      weight.
    - `italic` -- if `True`, the character should be in italics, otherwise
      upright.

    If any of the mentioned keyword arguments is not present, the corresponding
    feature is ignored.  The formatting style of whitespace is always ignored
    and the predicate in that case always returns `True`.
    """
    preds = []

    if 'bold' in kwargs:
        if kwargs['bold']:
            preds.append(lambda c: c.format.bold)
        else:
            preds.append(lambda c: not c.format.bold)

    if 'italic' in kwargs:
        if kwargs['italic']:
            preds.append(lambda c: c.format.italic)
        else:
            preds.append(lambda c: not c.format.italic)

    return lambda c: c.char.isspace() or all(f(c) for f in preds)


def chars(pattern: str | regex.Pattern = ".+", **kwargs):
    """Return a parser expecting the given `pattern` matching the formatting.

    The parser returns a list of matched characters as a successful result.

    `pattern` can be a regular expression compiled with the `regex` library (the
    standard `re` will not work) or a string representing the said regular
    expression.

    Additional keyword arguments may be passed to specify expected formatting.
    They are interpreted by `format_pred`, which see.
    """
    pred = format_pred(**kwargs)
    if isinstance(pattern, str):
        pattern = regex.compile(pattern)
    elif not isinstance(pattern, regex.Pattern):
        raise Exception('pattern should be a string or a regex.Pattern')

    @Parser
    def consumer(stream: list[Character], index: int) -> Result:
        chars = []
        last_good_match: regex.Match | None = None

        for char in stream[index:]:
            if not pred(char):
                break
            chars.append(char)
            text = ''.join(c.char for c in chars)
            match = pattern.fullmatch(text, partial=True)
            if match is None:
                break
            if not match.partial:
                last_good_match = match

        if last_good_match:
            n = last_good_match.end()
            return Result.success(index + n, chars[:n])
        else:
            return Result.failure(index, pattern.pattern)

    return consumer


def match_char(char: str) -> Parser:
    """Return a parser that matches a single character regardless of formatting"""
    return test_item(lambda c: c.char == char, char)


pronunciation = (
    match_char('(') >>                     \
      chars(r"[^\)]+").map(formatted_text) \
      << match_char(')')
).map(Span)

example = match_char('○') >> \
    seq(
        text=chars(italic=True).map(plain_text).map(str.strip),
        description=chars(r"[^;]+").map(plain_text).map(str.strip),
    ).combine_dict(Example)

sense = seq(
    translation=chars(r"[^;○]+").map(plain_text).map(str.strip),
    examples=example.many(),
).combine_dict(Sense)

entry = seq(
    headword=chars(r"[-а-яӵӧӝӥӟўө\s]+", bold=True).map(plain_text).map(str.strip),
    pronunciation=pronunciation,
    senses=sense*1,
).combine_dict(Entry)
