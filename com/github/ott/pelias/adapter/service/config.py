import os
from enum import Enum
from logging import getLogger

logger = getLogger(__name__)

PELIAS = os.getenv("PELIAS_URL", "https://ws-st.trimet.org/")

pelias_search_url = f"{PELIAS}/pelias/v1/search"
pelias_autocomplete_url = f"{PELIAS}/pelias/v1/autocomplete"
pelias_reverse_url = f"{PELIAS}/pelias/v1/reverse"
pelias_place_url = f"{PELIAS}/pelias/v1/place"


class SearchApiType(str, Enum):
    autocomplete = "autocomplete"
    search = "search"
    reverse = "reverse"
    place = "place"


class SolrApiType(str, Enum):
    select = "select"
    search = "search"
    autocomplete = "autocomplete"


logger.info(f"Pelias URL: {PELIAS}")
logger.info(f"Pelias Search URL: {pelias_search_url}")
logger.info(f"Pelias Autocomplete URL: {pelias_autocomplete_url}")
logger.info(f"Pelias Reverse URL: {pelias_reverse_url}")
logger.info(f"Pelias Place URL: {pelias_place_url}")
