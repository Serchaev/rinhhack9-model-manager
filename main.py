import uvicorn
from uvicorn.config import LOGGING_CONFIG

from app.config import settings

# TODO: Gunicorn?
if __name__ == "__main__":
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = settings.LOGGING.formatters.access.format
    LOGGING_CONFIG["formatters"]["default"]["fmt"] = settings.LOGGING.formatters.default.format
    uvicorn.run(
        settings.FAST_API_PATH,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOADED,
        workers=settings.WORKERS,
        log_level=settings.LOG_LEVEL,
        lifespan="on",
    )
