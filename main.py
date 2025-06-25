from docx import Document
from pprint import pprint
import sys
import time
from lexer import extract_characters
from parser import entry

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    doc = Document(sys.argv[1])
    par = doc.paragraphs[0]
    start_ns = time.perf_counter_ns()
    toks = list(extract_characters(par))
    result = entry.parse(toks)
    end_ns = time.perf_counter_ns()
    pprint(result)
    print(f'{(end_ns - start_ns) / 1e6}ms elapsed')
