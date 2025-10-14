import os
import urllib.parse
from time import sleep

import pytest
import requests
from starlette.testclient import TestClient

from main import app
from tests.comparison_testing.util import assert_builtins

OUTPUT_DIR = "pelias_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = True

LOCAL_URL = "http://localhost:8000/pelias"
STAGE_URL = "https://ws-st.trimet.org/pelias"

# List of full endpoint URLs to query (autocomplete and search for Portland)
queries = [
    "/v1/autocomplete?text=1600%20penn",
    "/v1/autocomplete?text=main%20st&focus.point.lat=45.5152&focus.point.lon=-122.6784",
    "/v1/autocomplete?text=broadway&boundary.circle.lat=45.5152&boundary.circle.lon=-122.6784&boundary.circle.radius=50",
    "/v1/autocomplete?text=market&boundary.rect.min_lat=45.2&boundary.rect.max_lat=45.7&boundary.rect.min_lon=-123.1&boundary.rect.max_lon=-122.3",
    "/v1/autocomplete?text=salmon%20st&boundary.country=US",
    "/v1/autocomplete?text=oswego&layers=locality",
    "/v1/autocomplete?text=taylor&layers=venue,address,street",
    "/v1/autocomplete?text=powell&sources=wof",
    "/v1/autocomplete?text=central%20library&layers=venue&sources=openstreetmap",
    "/v1/autocomplete?text=king&focus.point.lat=45.5152&focus.point.lon=-122.6784&boundary.country=US&layers=street",
    "/v1/search?text=1600%20pennsylvania%20ave%20nw",
    "/v1/search?text=soup%20st&focus.point.lat=45.5152&focus.point.lon=-122.6784",
    "/v1/search?text=portland&boundary.country=US",
    "/v1/search?text=station&boundary.circle.lat=45.5152&boundary.circle.lon=-122.6784&boundary.circle.radius=50",
    "/v1/search?text=overton%20st&boundary.rect.min_lat=45.2&boundary.rect.max_lat=45.7&boundary.rect.min_lon=-123.1&boundary.rect.max_lon=-122.3",
    "/v1/search?text=beaverton&layers=locality",
    "/v1/search?text=oregon%20zoo&layers=venue,address&sources=openstreetmap,wof",
    "/v1/search?text=hawthorne&focus.point.lat=45.5152&focus.point.lon=-122.6784&boundary.country=US",
    "/v1/search?text=97209",
    "/v1/search?text=1120%20SW%205th%20Ave&boundary.country=US&layers=address&sources=openstreetmap"
]


def get_query_text(q):
    parsed = urllib.parse.urlparse(q)
    params = urllib.parse.parse_qs(parsed.query)
    text_value = params.get("text", [None])[0]
    return text_value


QUERY_MAP = {get_query_text(q): q for q in queries}



@pytest.mark.parametrize(
    "query_id, query",
    list(QUERY_MAP.items()),
    ids=list(QUERY_MAP.keys())
)
#@pytest.mark.skip(reason="This compares the current api with the staging api, not meant for regular CI runs")
def test_compare_with_stage(query_id, query):
    print(f"Running {query_id} query against {LOCAL_URL} and {STAGE_URL}")
    # Run through all queries and save results
    stage_url = f"{STAGE_URL}{query}"
    local_url = f"/pelias{query}"

    stage_response = requests.get(stage_url, timeout=10)
    stage_response.raise_for_status()
    stage_data = stage_response.json()

    local_data = None

    with TestClient(app) as client:
        local_response = client.get(local_url)
        local_data = local_response.json()
        client.close()


    loca_attr, stage_attr = local_data["geocoding"].get("attribution"), stage_data["geocoding"].get("attribution")

    assert loca_attr == stage_attr, f"attribution mismatch: {loca_attr} != {stage_attr}"

    for local_feature in local_data["features"]:
        local_props = local_feature.get("properties", {})
        local_id = local_props.get("id")
        stage_props = next((f.get("properties", {}) for f in stage_data["features"] if f.get("properties", {}).get("id") == local_id), None)
        if stage_props:
            # todo label varies here. Not sure why. attribution is the same
            l1, l2 = local_props.get("label", "").split("(")[0], stage_props.get("label", "").split("(")[0]
            assert l1 in l2, f"label mismatch for {local_id}: {l1} not in {l2}"

            assert_builtins(local_data=local_props, stage_data=stage_props, skip=["label"])

        else:
            print(f"no stage props for {local_id}")




sleep(0.2)  # Slight delay to be kind to the server

print("✅ All done.")
