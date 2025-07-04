import logging
from logging.handlers import QueueHandler, QueueListener
import sys


log = logging.getLogger()

entry_prefix = ''

class EntryFilter(logging.Filter):
    def filter(self, record):
        record.prefix = entry_prefix
        return True


def init_logging(queue, level):
    """Initialises the logging for a worker thread."""
    log.setLevel(level)
    log.handlers.clear()
    log.addFilter(EntryFilter())
    log.addHandler(QueueHandler(queue))


def init_main_logging(queue) -> QueueListener:
    """Initialises the centralised logging"""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(
        '%(levelname)s:[%(prefix)s] %(message)s'))
    listener = QueueListener(queue, handler)
    listener.start()
    return listener
