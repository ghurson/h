# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import logging
from requests.exceptions import ReadTimeout
from h.util.logging_filters import ExceptionFilter


class TestExceptionFilter(object):

    def test_raises_if_invalid_level_name(self):
        with pytest.raises(ValueError):
            ExceptionFilter((("ReadTimeout", "WARNI"),))

    def test_specify_level_as_int(self, logger):
        ExceptionFilter((("ReadTimeout", logging.WARNING),))

    def test_does_not_log_specified_exceptions(self, logger):
        try:
            raise ReadTimeout("this is a test read timeout error")
        except ReadTimeout:
            logger.warning("warning", exc_info=True)
        assert not logger.handlers[0].handler_called, "Didn't filter out log message when it should have!!"

    def test_does_log_if_log_level_mismatch(self, logger):
        try:
            raise ReadTimeout("this is a test read timeout error")
        except ReadTimeout:
            logger.critical("critical", exc_info=True)
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_does_log_if_exception_mismatch(self, logger):
        try:
            raise Exception("this is a test read timeout error")
        except Exception:
            logger.warning("warning", exc_info=True)
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"

    def test_does_log_if_no_exc_info_is_recorded(self, logger):
        try:
            raise ReadTimeout("this is a test read timeout error")
        except ReadTimeout:
            logger.warning("warning")
        assert logger.handlers[0].handler_called, "Filtered out log message when it shouldn't have!!"


@pytest.fixture
def logger():
    class TestHandler(logging.Handler):
        handler_called = False

        def emit(self, record):
            self.handler_called = True

    log = logging.Logger('test_logger')
    log.addHandler(TestHandler())
    log.addFilter(ExceptionFilter((("ReadTimeout", "WARNING"),)))
    return log
