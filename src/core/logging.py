import logging
import sys

from gunicorn.app.base import BaseApplication
from gunicorn.glogging import Logger
from loguru import _defaults, logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class StubbedGunicornLogger(Logger):
    def setup(self, cfg):
        handler = logging.NullHandler()
        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)
        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)
        self.error_logger.setLevel(logging.INFO)
        self.access_logger.setLevel(logging.INFO)


class StandaloneApplication(BaseApplication):
    """Our Gunicorn application."""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def init_logger():
    intercept_handler = InterceptHandler()
    logging.root.setLevel(logging.INFO)

    seen = set()
    seen.add('pysolr')
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "uvicorn.access",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]
    logger.remove()
    
    logger.add(sys.stdout, backtrace=True, diagnose=True, enqueue=True, filter=lambda x: not (x['name'].startswith('uvicorn')))
    logger.add('logs/server.log', rotation="00:00",  retention="10 days", enqueue=True, 
                encoding='UTF-8', backtrace=True, diagnose=True, filter=lambda x: not x['name'].startswith('uvicorn'))

    logger.add('logs/access.log', rotation="00:00",  retention="15 days", enqueue=True, encoding='UTF-8',
                backtrace=True, diagnose=True, filter=lambda x: x['name'].startswith('uvicorn'))

    logger.add('logs/error.log', enqueue=True, encoding='UTF-8', backtrace=True, diagnose=True,
                filter=lambda x: 40==x['level'].no)