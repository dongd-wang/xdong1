from fastapi import FastAPI
from loguru import logger

from src import __VERSION__
from src import config
from src.core.events import (create_start_app_handler,
                                create_stop_app_handler)
from src.core.routes import (api_v1_routes)

def create_app():
    docs_url = '/docs' if config.ENABLE_DOC else None
    redoc_url = '/redoc' if config.ENABLE_DOC else None
    app = FastAPI(title=config.PROJECT_NAME, debug=config.DEBUG, version=__VERSION__, docs_url=docs_url, redoc_url=redoc_url)
    
    app.add_event_handler("startup", create_start_app_handler())
    app.add_event_handler("shutdown", create_stop_app_handler())

    # router
    # app.include_router(service_routes, prefix=config.PAGE_PREFIX)
    app.include_router(api_v1_routes, prefix=config.API_PREFIX)


    return app

app = create_app()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app="src.main:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)