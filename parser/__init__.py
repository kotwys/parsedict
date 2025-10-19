"""Parser rules.

The user should first call the `init_grammar` function that reads the
definitions from a Lissp file.  Then, the defined rules are accesible as
attributes of this module.
"""
from pathlib import Path
import sys

import hissp.compiler
import hissp.reader
from parsy import alt, eof, fail, forward_declaration, seq, success

from parser.helpers import *


def init_grammar(grammar: str):
    """Read the grammar from a Lissp file.

    Refer to the `grammar.lissp` file for details."""

    # NOTE: probably can be abused with `../`
    grammar_file = Path(sys.argv[0]).parent / 'grammars' / f'{grammar}.lissp'

    with open(grammar_file) as f:
        lissp = hissp.reader.Lissp(filename=f.name)
        hissp.compiler.execute(*(lissp.reads(f.read())))
