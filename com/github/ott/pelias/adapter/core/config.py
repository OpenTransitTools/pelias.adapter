import os
from logging import getLogger
from zoneinfo import ZoneInfo

from ott.utils.svr.pyramid.globals import CACHE_LONG
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

logger = getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")  # default to dev

CACHE_LONG_STR = f"public, max-age={CACHE_LONG}"

logger.info(f"Environment: {ENVIRONMENT}")

ENV_FILE = f"{ENVIRONMENT}.env"

TIME_ZONE: ZoneInfo = ZoneInfo("America/Los_Angeles")

DATE_STRING_FORMAT = "%Y-%m-%d %H:%M:%S %Z%z"


class Settings(BaseSettings):
    """
    Application settings with Oracle database configuration
    """

    # Application settings
    app_name: str = "FastAPI Trimet Pelias Adapter"
    debug: bool = False

    model_config = ConfigDict(
        env_file=ENV_FILE,  # or f"{ENVIRONMENT}.env"
        case_sensitive=False,
        extra="allow",
    )


# Global settings instance
settings = Settings()

logger.info(f"Loaded settings for environment: {ENVIRONMENT}, {settings.debug}")
