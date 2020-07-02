import logging


def get_logger(config):
    # create formatter
    default_formatter = logging.Formatter(
        "%(asctime)s|%(filename)s::%(funcName)s:%(lineno)s|%(levelno)s|%(message)s")

    logger = logging.getLogger(config.app_name.lower())
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(default_formatter)

        # add console handler to logger
        logger.addHandler(ch)

    return logger
