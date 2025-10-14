import logging
import logging.config

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from com.github.ott.pelias.adapter.core.errors import PeliasAdapterError
from com.github.ott.pelias.adapter.core.config import settings

from com.github.ott.pelias.adapter.routers import core, pelias, solr

# Configure logging
logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
logger = logging.getLogger(__name__)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="FastAPI template with Oracle database using Instant Client 21 and SQLAlchemy 2.x",
    version="1.0.0",
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(pelias.router, prefix="/pelias/v1", tags=["pelias"])
app.include_router(solr.router, prefix="/solr/v1", tags=["solr"])
app.include_router(core.router, prefix="/core/v1", tags=["core"])


def add_exception_handlers(app):
    @app.exception_handler(PeliasAdapterError)
    async def pelias_wrapper_error_handler(request: Request, exc: PeliasAdapterError):
        return JSONResponse(status_code=400, content={"error": exc.message})


add_exception_handlers(app)
