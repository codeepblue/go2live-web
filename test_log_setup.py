import logging

from log_setup import get_logger
from config import Configuration


def test_get_logger():
    logger = get_logger(Configuration())
    assert isinstance(logger, logging.Logger)


def test_logger_can_log_debug_messages(caplog):
    logger = get_logger(Configuration())
    logger.debug("foo")
    assert "foo" == caplog.messages[0]


def test_logger_can_log_info_messages(caplog):
    logger = get_logger(Configuration())
    logger.info("foo")
    assert "foo" == caplog.messages[0]


def test_logger_can_log_warning_messages(caplog):
    logger = get_logger(Configuration())
    logger.warning("foo")
    assert "foo" == caplog.messages[0]


def test_logger_can_log_error_messages(caplog):
    logger = get_logger(Configuration())
    logger.error("foo")
    assert "foo" == caplog.messages[0]


def test_logger_can_log_critical_messages(caplog):
    logger = get_logger(Configuration())
    logger.critical("foo")
    assert "foo" == caplog.messages[0]
