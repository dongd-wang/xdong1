import functools
from pathlib import Path

__VERSION__ = "SEARCH.SNAPSHOT"

__COMMIT__ = "UNKNOWN"

BASE_DIR = Path(__file__).parent.absolute()


try:
    from src import version
    __VERSION__ = version.__VERSION__
except:
    pass

try:
    from src import version
    if not version.__COMMIT__.startswith('fatal'):
        __COMMIT__ = version.__COMMIT__
except:
    pass