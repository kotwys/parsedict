"""Helper functions that form the grammar for parsing."""
from functools import reduce
from operator import iconcat
from typing import Callable, Mapping, Sequence
import unicodedata

from parsy import Parser, Result, test_item
import regex

from lexer import Character, Format
from logger import log
from parser.markup import Markup, MarkupNode


def regex_opt(strings: Sequence[str]) -> str:
    """Return a regular expression matching any of the given strings.

    Works similarly to the Emacs Lisp's `regexp-opt` function."""
    strings = sorted(
        set(strings),
        key=lambda s: (-len(s), s))
    escaped = map(regex.escape, strings)
    return r'(?:' + '|'.join(escaped) + r')'


# The keys should be in \uXXXX form for readability.
FONT_CONV: Mapping[str, Mapping[str, str]] = {
    'Lingua': {
        '\u0026': 'u̯',
        '\u0032': 'i̮',
        '\u0038': 'u̇',
        '\u0040': 'i̯',
        '\u041a': 'ə̑',
        '\u042b': 'o̭',
        '\u0446': 'e̮',
        '\u045c': 'č́',
    },
    '1 FU': {
        '\u00b9': 'i̯',
    },
}

SCRIPT_CONV: Mapping[str, Mapping[str, str]] = {
    'Latn': {
        '\u0430': '\u0061',  # a
        '\u0438': '\u0075',  # u
        '\u043f': '\u006e',  # n
        '\u0445': '\u0078',  # x
        '\u0448': '\u026f',  # ɯ
        '\u04e8': '\u019f',  # Ɵ
        '\u04e9': '\u0275',  # ɵ
    },
    'Cyrl': {
        '\u00e1': '\u0430\u0301',  # а́
        '\u00e9': '\u0435\u0301',  # е́
        '\u00f3': '\u043e\u0301',  # о́
        '\u00ff': '\u04f1',  # ӱ
        '\u0275': '\u04e9',  # ө
        '\u0063': '\u0441',
    },
}

ALWAYS_CONV: Mapping[str, str] = {
    '\u0473': '\u04e9',  # ө
}


def warn_replacement(c: Character):
    log.info('Replaced possibly erroneous symbol %s (U+%04x)',
             c.char, ord(c.char))


def normalize_char(c: Character, **kwargs) -> str:
    """Convert a character to its normal form.

    When the character is a whitespace, it is normalized to one regular space.

    When the character is typeset with a known phonetic font (e.g. Lingua), it
    is normalized to the corresponding standard Unicode representation.

    If `script` kwarg is given (either `Latn` or `Cyrl`), the character is also
    checked against a substitution table corresonding to the script.

    In other cases, the character is returned as-is.
    """
    if c.char.isspace():
        return ' '
    elif c.format.font in FONT_CONV:
        table = FONT_CONV[c.format.font]
        if c.char in table:
            return table[c.char]

        code = ord(c.char)
        raise Exception(f'No Unicode symbol matching U+{code:04x} '
                        + f'from font {c.format.font}.')
    elif 'script' in kwargs and c.char in SCRIPT_CONV[kwargs['script']]:
        warn_replacement(c)
        return SCRIPT_CONV[kwargs['script']][c.char]
    elif c.char in ALWAYS_CONV:
        warn_replacement(c)
        return ALWAYS_CONV[c.char]
    else:
        # Check for Unicode consistency just in case
        if 'script' in kwargs:
            name = unicodedata.name(c.char, '')
            no = ['LATIN', 'CYRILLIC']
            match kwargs['script']:
                case 'Latn': no.remove('LATIN')
                case 'Cyrl': no.remove('CYRILLIC')
            if any(p in name for p in no):
                log.debug('Unexpected %s in script %s',
                          name, kwargs['script'])

        return c.char


def detect_script(chars: list[Character]) -> str:
    """Try to heuristically guess the writing script of the text."""
    ignore = {'\u0275', '\u0448', '\u0473', '\u04e8', '\u04e9'}
    total, latin, cyrillic = 0, 0, 0
    for c in chars:
        if c.format.font in FONT_CONV or c.char in ignore:
            continue
        total += 1
        name = unicodedata.name(c.char, '')
        if 'LATIN' in name:
            latin += 1
        elif 'CYRILLIC' in name:
            cyrillic += 1

    if cyrillic > latin and cyrillic >= 0.2 * total:
        return 'Cyrl'
    else:
        return 'Latn'


def strip_characters(
        chars: list[Character],
        strip: str | None = None) -> list[Character]:
    """Strips characters from both ends of the text like `str.strip`."""
    while chars:
        if not chars[0].char.strip(strip):
            chars = chars[1:]
        else:
            break
    while chars:
        if not chars[-1].char.strip(strip):
            chars = chars[:-1]
        else:
            break
    return chars


def plain_text(chars: list[Character], normalize=True, **kwargs) -> str:
    """Collect a list of characters into a plain text string.

    This function effectively strips any formatting.

    If `normalize` is `True` (the default), then output is also
    normalized according to the Unicode's canonical composition.  Be
    aware that normalization may change the length of the string, even
    if visually it remains the same.
    """
    text = ''.join(map(
        lambda c: normalize_char(c, **kwargs),
        chars))
    if normalize:
        return unicodedata.normalize('NFC', text)
    else:
        return text


def node_matches_format(node: MarkupNode, format: Format) -> bool:
    if not getattr(format, node[0]):
        return False
    elif node[0] == 'color':
        return node[1]['color'] == format.color
    return True


def formatted_text(chars: list[Character], **kwargs) -> Markup:
    """Transform a list of characters to a list of HTML-like markup nodes.

    In the `markup` kwarg, a tuple of `Format` attribute names should be passed
    (eg. ``("italic", "sup")``).  Only these attributes are accounted when
    constructing a node tree.
    """
    if 'markup' not in kwargs:
        raise Exception('markup= should be passed.')

    attrs = kwargs['markup']
    format = None
    i, j = 0, 0
    stack: list[list] = [[]]

    def push_node(going_down: bool = True):
        nonlocal i, j, stack
        if j == i:
            return
        text = plain_text(chars[i:j], normalize=False, **kwargs)
        # Exclude trailing spaces from formatted nodes
        if going_down and len(stripped := text.rstrip()) != len(text):
            strip_width = len(text) - len(stripped)
            i = j - strip_width
            text = stripped
        else:
            i = j
        stack[-1].append(unicodedata.normalize('NFC', text))

    def collapse_stack(lowest: int):
        nonlocal stack
        push_node()
        while len(stack) > lowest:
            node = tuple(stack.pop())
            stack[-1].append(node)

    while j < len(chars):
        char = chars[j]
        if not char.char.isspace():
            new_format = tuple(map(
                lambda a: getattr(char.format, a),
                attrs))
            if not format or new_format != format:
                lowest_collapse = None
                for l in range(len(stack)-1, 0, -1):
                    if not node_matches_format(stack[l], char.format):
                        lowest_collapse = l

                if lowest_collapse:
                    collapse_stack(lowest_collapse)

                for at, v in zip(attrs, new_format):
                    if not v:
                        continue
                    if any(level[0] == at for level in stack[1:]):
                        continue
                    push_node(False)
                    data = {}
                    if at == 'color':
                        data['color'] = char.format.color
                    stack.append([at, data])

                format = new_format
        j += 1

    if j > i:
        collapse_stack(1)

    return Markup(stack[0])


def collect(**kwargs):
    """Return a function collecting a sequence of characters into either a
    string or a markup.

    The following keyword arguments are accepted:

    - `markup` -- if present and truthy, the function returns markup after
      processing the input sequence as with `formatted_text`

    - `script` -- if present, the input text is normalized according to the
      given script (refer to `normalize_text` for more details).  If `detect` is
      provided as the value, try to heuristically detect the writing script

    - `strip` -- if `True` or a string, strip whitespace or given characters
      from both the beginning and the end of the text.
    """
    def preprocess_kwargs(chars: list[Character]) -> dict:
        if 'script' in kwargs and kwargs['script'] == 'detect':
            script = detect_script(chars)
            log.debug('Detected script %s', script)
            return {**kwargs, 'script': script}
        else:
            return kwargs

    if 'markup' in kwargs and kwargs['markup']:
        def executor(chars: list[Character]) -> list:
            kwargs_x = preprocess_kwargs(chars)
            if 'strip' in kwargs_x:
                if isinstance(kwargs_x['strip'], str):
                    chars = strip_characters(chars, kwargs_x['strip'])
                else:
                    chars = strip_characters(chars)
            return formatted_text(chars, **kwargs_x)
        return executor
    else:
        def executor(chars: list[Character]) -> str:
            kwargs_x = preprocess_kwargs(chars)
            result = plain_text(chars, **kwargs_x)
            if 'strip' in kwargs_x:
                if isinstance(kwargs_x['strip'], str):
                    result = result.strip(kwargs_x['strip'])
                else:
                    result = result.strip()
            return result
        return executor


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

    if 'color' in kwargs:
        if isinstance(kwargs['color'], tuple):
            preds.append(lambda c: c.format.color == kwargs['color'])
        elif kwargs['color']:
            preds.append(lambda c: c.format.color)
        else:
            preds.append(lambda c: not c.format.color)

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


any_char = test_item(lambda _: True, "any character")


def match_char(char: str) -> Parser:
    """Return a parser that matches a single character regardless of formatting"""
    return test_item(lambda c: c.char == char, char)


def flatten[T](cols: list[list[T]]) -> list[T]:
    """Flattens a list of lists."""
    return reduce(iconcat, cols, [])

def split_on(chars: list[Character], sep: str) -> list[list[Character]]:
    """Splits the character sequence on the given separator character."""
    result = []
    start = 0
    for i, char in enumerate(chars):
        if char.char == sep:
            if i > start:
                result.append(chars[start:i])
            start = i+1
    if start != len(chars):
        result.append(chars[start:])
    return result
