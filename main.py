from docx import Document
from pprint import pprint
import sys
from lexer import tokenize
from parser import Parser

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    doc = Document(sys.argv[1])
    par = doc.paragraphs[0]
    toks = list(tokenize(par))
    parser = Parser(toks)
    pprint(parser.parse())
