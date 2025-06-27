"""Parser rules.

The user should first call the `init_grammar` function that reads the
definitions from a Lissp file.  Then, the defined rules are accesible as
attributes of this module.
"""
import hissp.compiler
import hissp.reader
from parsy import alt, eof, fail, forward_declaration, seq, success

from model import Example, Sense, Entry
from parser.helpers import *


def init_grammar():
    """Read the grammar from a Lissp file.

    Refer to the `grammar.lissp` file for details."""
    with open('grammar.lissp') as f:
        lissp = hissp.reader.Lissp(filename=f.name)
        hissp.compiler.execute(*(lissp.reads(f.read())))
