import logging
import os


def get_logger(name):  # pragma: no cover
    logger = logging.getLogger(name)
    # don't attach any more handlers if we already have them
    if not len(logger.handlers):
        if is_debug():
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def is_debug():  # pragma: no cover
    debug = os.getenv('DEBUG')
    if not debug:
        return False
    return True if debug.lower() in ('yes', 'true') else False
