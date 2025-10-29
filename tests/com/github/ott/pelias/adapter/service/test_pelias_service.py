import pytest
from fastapi.testclient import TestClient

from com.github.ott.pelias.adapter.service.util import QueryType
from main import app

queries = {
    "one": [
        ("949 NW ", "949 NW Overton Street", QueryType.STREET_ADDRESS),
        (
            "5960",
            "NE M L King & Weidler (TriMet Stop ID 5960)",
            QueryType.JUST_A_NUMBER,
        ),
        (
            "stop 5955",
            "NE M L King & Tillamook (TriMet Stop ID 5955)",
            QueryType.STOP_REQUEST,
        ),
        ("moo", "tbd", QueryType.UNKNOWN),
    ]
}


@pytest.mark.parametrize("query, expected_name, query_type", queries.get("one"))
def test_get_pelias_response_success_one(query, expected_name, query_type):
    with TestClient(app) as client:
        result = client.get(f"/pelias/v1/refine/autocomplete?text={query}")
        assert result.status_code == 200
        data = result.json()
        assert "features" in data
        features = data.get("features", [])
        if query != "moo":
            name = features[0].get("properties", {}).get("name", "")
            assert name == expected_name
        else:
            assert len(features) > 1
