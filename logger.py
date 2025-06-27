import logging
import sys


log = logging.getLogger()

logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging.DEBUG,
    stream=sys.stderr)
