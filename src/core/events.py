
from typing import Callable

def create_start_app_handler() -> Callable:
    async def startup():
        pass
    return startup


def create_stop_app_handler() -> Callable:
    async def shutdown():
        pass
    return shutdown