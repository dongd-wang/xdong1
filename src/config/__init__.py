import hashlib
import logging
import os
import platform
from typing import List

from src import __VERSION__
from src.config import config_parser
from starlette.config import Config
from starlette.datastructures import URL, CommaSeparatedStrings, Secret

VERSION = __VERSION__
API_PREFIX = "/api"
PAGE_PREFIX = "/service"

#
config = Config(".env")

config_from_configfile = config_parser.read_config_file()

DEBUG: bool = os.environ.get('DEBUG', '') or config("DEBUG", cast=bool, default=False)


MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)

#SOLR
SOLR_ZOOKEEPER_ADDRESS: str = config("SOLR_ZOOKEEPER_ADDRESS", default=config_from_configfile.get('zookeeper'))
SOLR_COLLECTION: str = config("SOLR_COLLECTION", default=config_from_configfile.get('collection') or 'ckchina')
SOLR_DOCUMENTS_BATCH_SIZE : int = config("SOLR_DOCUMENTS_BATCH_SIZE", default=100, cast=int)

SOLR_HOST: str = config("SOLR_HOST", default=config_from_configfile.get('solr_host') or 'localhost')
SOLR_PORT: str = config("SOLR_PORT", default=config_from_configfile.get('solr_port') or 8983, cast=str)

WEB_DOMAIN_URL: URL = config("WEB_DOMAIN", default=config_from_configfile.get('web_domain'), cast=URL)
WEB_DOMAIN = str(WEB_DOMAIN_URL)

SECRET_KEY: Secret = config("SECRET_KEY", default="you never know", cast=Secret)

PROJECT_NAME: str = config("PROJECT_NAME", default="CK China Search Service")
ALLOWED_HOSTS: List[str] = config(
    "ALLOWED_HOSTS", cast=CommaSeparatedStrings, default="",
)

# logging configuration
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
LOGURU_LEVEL = "DEBUG" if DEBUG else "INFO"
JSON_LOGS = True if config("JSON_LOGS", default="0") == "1" else False
ENABLE_DOC = True if config("ENABLE_DOC", default="0") == "1" else False

HOSTNAME_HASH = hashlib.md5(platform.node().encode()).hexdigest()[:8] or ''