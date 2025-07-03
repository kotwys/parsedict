from pprint import pprint
import sys
import time

from docx import Document
from parsy import ParseError
import yaml

from lexer import extract_characters
from logger import log
import parser
from output import prepare_for_output

LINE_WIDTH = 72

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)

    doc = Document(sys.argv[1])
    parno = int(sys.argv[2])
    par = doc.paragraphs[parno]
    toks = list(extract_characters(par))
    parser.init_grammar()
    try:
        start_ns = time.perf_counter_ns()
        result = parser.entry.parse(toks)
        clean = prepare_for_output(result)
        yaml.dump(clean, stream=sys.stdout, allow_unicode=True, sort_keys=False)
    except ParseError as ex:
        total_length = len(ex.stream)
        left = max(
            min(ex.index - LINE_WIDTH//2, total_length - LINE_WIDTH),
            0)
        right = min(
            max(left+LINE_WIDTH, ex.index + LINE_WIDTH//2),
            total_length)
        text = ''.join(map(lambda c: c.char, ex.stream[left:right]))
        log.error('Expected %s\n  %s\n  %s^',
                  ex.expected, text, ' '*(ex.index-left))
    finally:
        end_ns = time.perf_counter_ns()
        log.info('%.6fms elapsed', (end_ns - start_ns) / 1e6)
