import logging
from queue import Queue  # For UI integration

log_queue = Queue()  # Global queue for UI log callbacks

class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
    
    def error(self, msg, *args, **kwargs):
        super().error(msg, *args, **kwargs)
        log_queue.put(('error', msg % args))  # Queue for UI
    
    def warning(self, msg, *args, **kwargs):
        super().warning(msg, *args, **kwargs)
        log_queue.put(('warning', msg % args))

# Set up the logger with the custom class
logging.setLoggerClass(CustomLogger)

import ofscraper.utils.logs.utils.level as log_helpers
from ofscraper.utils.logs.stdout import add_stdout_handler
from ofscraper.utils.logs.other import add_other_handler, getstreamHandlers
from ofscraper.utils.logs.classes.handlers.text import TextHandler
import ofscraper.utils.dates as dates
from ofscraper.core.observers import log_observer


def add_widget(widget):
    [
        setattr(ele, "widget", widget)
        for ele in list(
            filter(
                lambda x: isinstance(x, TextHandler),
                logging.getLogger("shared").handlers,
            )
        )
    ]


def get_shared_logger(name=None):
    # Create a logger with custom class
    logger = logging.getLogger(name or "shared")  # Now uses CustomLogger
    clearHandlers(name)
    log_helpers.addtraceback()
    log_helpers.addtrace()
    add_stdout_handler(logger, clear=False)
    add_other_handler(logger, clear=False)
    logger.setLevel(1)
    logger.propagate = False  # Don't propagate to root

    class ObserverHandler(logging.Handler):
        def emit(self, record):
            try:
                msg = self.format(record)
                log_observer.notify(msg=msg, level=record.levelname)
            except Exception as e:
                logging.error(f"Error in ObserverHandler: {str(e)}")  # Basic error handling

    observer_handler = ObserverHandler()
    observer_handler.setLevel(logging.INFO)
    observer_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(observer_handler)

    return logger  # Ensure this returns the custom logger instance


def clearHandlers(name=None):
    log = logging.getLogger(name or "shared")
    for handler in log.handlers[:]:  # Iterate over a copy of the list
        try:
            log.removeHandler(handler)
            handler.close()  # Release resources (critical for file handlers)
        except Exception as e:
            # Basic error handling (optional)
            print(f"Error closing handler: {str(e)}")
    log = log.parent


def resetLogger():
    dates.resetLogDateVManager()
    get_shared_logger()


def flushlogs():
    for handler in getstreamHandlers():
        handler.flush()
