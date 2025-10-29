import os
from enum import Enum
from logging import getLogger

logger = getLogger(__name__)

PELIAS = os.getenv("PELIAS_URL", "https://ws-st.trimet.org")
MAPS_URL = os.getenv("MAPS_URL", "https://maps.trimet.org")

pelias_search_url = f"{PELIAS}/pelias/v1/search"
pelias_autocomplete_url = f"{PELIAS}/pelias/v1/autocomplete"
pelias_reverse_url = f"{PELIAS}/pelias/v1/reverse"
pelias_place_url = f"{PELIAS}/pelias/v1/place"
route_stop_str_url = f"{MAPS_URL}/ti/index/stops"


class SearchApiType(str, Enum):
    autocomplete = "autocomplete"
    search = "search"
    reverse = "reverse"
    place = "place"


class SolrApiType(str, Enum):
    select = "select"
    search = "search"
    autocomplete = "autocomplete"


logger.debug(f"Pelias URL: {PELIAS}")
logger.debug(f"Pelias Search URL: {pelias_search_url}")
logger.debug(f"Pelias Autocomplete URL: {pelias_autocomplete_url}")
logger.debug(f"Pelias Reverse URL: {pelias_reverse_url}")
logger.debug(f"Pelias Place URL: {pelias_place_url}")
