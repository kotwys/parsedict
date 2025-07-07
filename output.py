"""Functions for outputting parsing results."""
from collections import OrderedDict

import yaml

from parser.markup import Markup


FIELD_ORDER = {
    # entry
    'headword': 0,
    'derivation': 1,
    'label': 2,
    'senses': 3,

    # sense
    'type': 0,
    'translation': 50,

    # example
    'source': 0,
    'text': 30,

    # headword
    'value': 10,
    'homonym_id': 20,
    'assumed': 30,
}

DEFAULT_ORDER = 100


def prepare_for_output(obj):
    """Prepares the parser result for output.

    Keys that begin with an underscore and keys with falsy values are
    removed.  Keys are sorted for the user's convenience.
    """
    if isinstance(obj, dict):
        pairs = [
            (k, prepare_for_output(v))
            for k, v in obj.items()
            if not k.startswith('_') and v
        ]
        pairs.sort(key=lambda kv: FIELD_ORDER.get(kv[0], DEFAULT_ORDER))
        return dict(pairs)
    elif isinstance(obj, list):
        return [prepare_for_output(x) for x in obj]
    else:
        return obj


def markup_representer(dumper: yaml.Dumper, markup: Markup):
    return dumper.represent_str(markup.to_html())

yaml.add_representer(Markup, markup_representer)
