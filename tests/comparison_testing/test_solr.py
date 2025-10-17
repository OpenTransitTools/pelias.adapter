import logging
import urllib.parse
from time import sleep

import pytest
import requests
from starlette.testclient import TestClient

from main import app
from tests.comparison_testing.util import assert_builtins

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = True

STAGE_URL = "https://ws-st.trimet.org/solrwrap"

# List of full endpoint URLs to query (autocomplete and search for Portland)
queries = [
    "/v1/autocomplete?q=1600&rows=11",
    "/v1/autocomplete?q=main&rows=11",
    "/v1/autocomplete?q=broadway&rows=11",
    "/v1/autocomplete?q=market&rows=11",
    "/v1/autocomplete?q=salmon&rows=11",
    "/v1/autocomplete?q=oswego&rows=11",
    "/v1/autocomplete?q=taylor&rows=11",
    "/v1/autocomplete?q=powell&rows=11",
    "/v1/autocomplete?q=central&rows=11",
    "/v1/autocomplete?q=king&rows=11",
    "/v1/search?q=1600&rows=11",
    "/v1/search?q=soup&rows=11",
    "/v1/search?q=portland&rows=11",
    "/v1/search?q=station&rows=11",
    "/v1/search?q=overton&rows=11",
    "/v1/search?q=beaverton&rows=11",
    "/v1/search?q=oregon&rows=11",
    "/v1/search?q=hawthorne&rows=11",
    "/v1/search?q=97209&rows=11",
    "/v1/search?q=1120&rows=11",
    "/v1/search?q=1600&rows=11",
    "/v1?q=soup&rows=11",
    "/v1?q=portland&rows=11",
    "/v1?q=station&rows=11",
    "/v1?q=overton&rows=11",
    "/v1?q=beaverton&rows=11",
    "/v1?q=oregon&rows=11",
    "/v1?q=hawthorne&rows=11",
    "/v1?q=97209&rows=11",
    "/v1?q=1120&rows=11",
    "/v1/select?q=1600&rows=11",
    "/v1/select?q=soup&rows=11",
    "/v1/select?q=portland&rows=11",
    "/v1/select?q=station&rows=11",
    "/v1/select?q=overton&rows=11",
    "/v1/select?q=beaverton&rows=11",
    "/v1/select?q=oregon&rows=11",
    "/v1/select?q=hawthorne&rows=11",
    "/v1/select?q=97209&rows=11",
    "/v1/select?q=1120&rows=11",
]


def get_query_text(q):
    parsed = urllib.parse.urlparse(q)
    params = urllib.parse.parse_qs(parsed.query)
    text_value = params.get("q", [None])[0]
    return text_value


QUERY_MAP = {get_query_text(q): q for q in queries}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_id, query", list(QUERY_MAP.items()), ids=list(QUERY_MAP.keys())
)
@pytest.mark.skip(
    "Run these to compare with stage. Ensure the results attributes are the same"
)
async def test_compare_with_stage(query_id, query):
    print(f"Running {query_id} query against local solr/{query} and {STAGE_URL}")
    stage_url = f"{STAGE_URL}{query}"
    local_url = f"/solr{query}"  # Needs to be a full path for ASGI client

    stage_response = requests.get(stage_url, timeout=10)
    stage_response.raise_for_status()
    stage_data = stage_response.json()

    with TestClient(app) as client:
        local_response = client.get(local_url)
        local_data = local_response.json()
        client.close()

    assert_builtins(local_data=local_data, stage_data=stage_data)

    local_response_data = local_data.get("response", {})
    stage_response_data = stage_data.get("response", {})
    local_docs = local_response_data.get("docs", [])
    stage_docs = stage_response_data.get("docs", [])

    docs_map = {}
    for doc in local_docs:
        doc_id = doc.get("id")
        if doc_id:
            stage_doc = next(
                (item for item in stage_docs if item.get("id") == doc_id), None
            )
            docs_map[doc_id] = {"local": doc, "stage": stage_doc}

    for doc_id, doc_pair in docs_map.items():
        local_doc = doc_pair["local"]
        stage_doc = doc_pair["stage"]
        if stage_doc:
            assert_builtins(
                local_data=local_doc, stage_data=stage_doc, skip=["timestamp"]
            )
        else:
            print(f"Warning: Document with id {doc_id} not found in stage response.")

    sleep(0.2)
    print("✅ All done.")
