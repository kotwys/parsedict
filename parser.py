from typing import Callable, Mapping
from lexer import Token, SpaceToken, WordToken
from model import *

LINGUA_TO_UNICODE: Mapping[str, str] = {
    '\u041a': 'ə̑',
}

def convert_lingua(symbol: str) -> str:
    if symbol in LINGUA_TO_UNICODE:
        return LINGUA_TO_UNICODE[symbol]
    else:
        code = ord(symbol)
        raise Exception(f'No Unicode symbol matching for {code:x}.')

class Parser:
    toks: list[Token]

    def __init__(self, toks: list[Token]):
        self.toks = toks

    def check_end_of_tokens(self, pos: int) -> bool:
        if pos >= len(self.toks):
            raise Error("eof")
        return True

    def skip_spaces(self, pos: int):
        while pos < len(self.toks) and isinstance(self.toks[pos], SpaceToken):
            pos += 1
        return pos

    def until_breaker(self, pos: int) -> tuple[str, int]:
        parts = []
        while pos < len(self.toks) and not (self.toks[pos].text in {';', '○'}):
            parts.append(self.toks[pos].text)
            pos += 1
        if parts:
            return ''.join(parts).strip(), pos
        else:
            return None, pos

    def parse_while_word(self, pos: int, f: Callable[[WordToken], bool]):
        buffer = []
        while pos < len(self.toks):
            if isinstance(self.toks[pos], SpaceToken):
                buffer.append(self.toks[pos].text)
                pos += 1
            elif f(self.toks[pos]):
                buffer.append(self.toks[pos].text)
                pos += 1
            else:
                break

        if buffer:
            return ''.join(buffer).strip(), pos
        else:
            return None, pos

    def parse_italicized(self, pos: int):
        return self.parse_while_word(pos, lambda t: t.italic)

    def parse_bold(self, pos: int):
        return self.parse_while_word(pos, lambda t: t.bold)

    def parse_headword(self, pos: int):
        self.check_end_of_tokens(pos)
        return self.parse_bold(pos)

    def parse_pronunciation(self, pos):
        self.check_end_of_tokens(pos)
        if self.toks[pos].text == '(':
            pos += 1
            sup = None
            buffer = []
            nodes = []

            def push_node():
                nonlocal buffer, nodes
                text = ''.join(buffer)
                node = TextNode(text)
                if sup:
                    node = Superscript([node])
                nodes.append(node)
                buffer = []

            while pos < len(self.toks) and not (self.toks[pos].text == ')'):
                if isinstance(self.toks[pos], SpaceToken):
                    buffer.append(self.toks[pos].text)
                elif isinstance(self.toks[pos], WordToken):
                    # TODO: superscripts
                    for ch in self.toks[pos].chars:
                        if ch.format.sup != sup:
                            push_node()
                            sup = ch.format.sup
                        buffer.append(
                            ch.format.font == "Lingua" and convert_lingua(ch.char)
                            or ch.char
                        )
                pos += 1
            if pos >= len(self.toks) or self.toks[pos].text != ')':
                raise Error("unclosed parenthesis")
            pos += 1
            if buffer:
                push_node()
            return Span(nodes), pos
        return None, pos

    def parse_sense(self, pos: int):
        translation, pos = self.until_breaker(pos)
        example, pos = self.parse_example(pos, marker='○')
        return Sense(
            translation=translation,
            examples=[example]
        ), pos

    def parse_example(self, pos: int, marker: str = None):
        if not marker:
            pass
        elif self.check_end_of_tokens(pos) and self.toks[pos].text == marker:
            pos += 1
        else:
            raise Exception("erur")

        # TODO: parse <...>
        # What if marker was matched but nothing more?
        source, pos = self.parse_italicized(pos)
        if source:
            translation, pos = self.until_breaker(pos)
            return Example(text=source, description=translation), pos
        else:
            return None, pos

    def parse(self) -> Entry:
        pos = 0
        headword, pos = self.parse_headword(pos)
        pronunciation, pos = self.parse_pronunciation(pos)
        sense, pos = self.parse_sense(pos)
        return Entry(
            headword,
            pronunciation,
            [sense],
        )
