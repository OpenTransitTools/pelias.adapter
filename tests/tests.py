import pytest
from ott.utils import file_utils
from ott.utils import json_utils

from com.github.ott.pelias.adapter.models.solr.solr_stop_record import SolrStopRecord
from com.github.ott.pelias.adapter.service.pelias_to_solr import PeliasToSolr

PORT = "45554"


@pytest.fixture(scope="module")
def base_path():
    return file_utils.get_file_dir(__file__)


@pytest.fixture
def urls():
    return {
        "auto": "https://ws-st.trimet.org/pelias/v1/autocomplete",
        "search": "https://ws-st.trimet.org/pelias/v1/search",
    }


def parse(file_name, base_path):
    file_path = file_utils.path_join(base_path, file_name)
    json_data = json_utils.file_to_json(file_path)
    return PeliasToSolr.parse_json(json_data)


def test_pelias_to_solr(base_path):
    p = parse("data/search13135.json", base_path)
    assert len(p.response.docs) > 0


@pytest.mark.skip(
    reason="this is looking for properties.addendum.gtfs which is not in the passed json at all"
)
def test_stops(base_path):
    p = parse("data/search13135.json", base_path)
    num_stops = 0
    for d in p.response.docs:
        if isinstance(d, SolrStopRecord):
            num_stops += 1
            assert len(d.stop_id) > 0
            assert len(d.agency_id) > 0
    assert num_stops > 0


def test_unique_coords(base_path):
    p = parse("data/autocomplete-hop-fastpass.json", base_path)
    coords = set()
    for d in p.response.docs:
        assert d.lat != 0.0
        assert d.lon != 0.0
        assert d.lon not in coords
        assert d.lat not in coords
        coords.add(d.lat)
        coords.add(d.lon)


def test_names_labels(base_path):
    p = parse("data/autocomplete-hop-fastpass.json", base_path)
    for d in p.response.docs:
        assert "HOP Fastpass" in d.name


def test_solr_to_pelias_params():
    solr_params = {"q": "val", "rows": "6"}
    pelias_params_str = PeliasToSolr.solr_to_pelias_param_str(solr_params)
    assert "text=val" in pelias_params_str
    assert "size=6" in pelias_params_str


def test_call_live_pelias_server():
    """
    https://ws-st.trimet.org/pelias/v1/autocomplete?text=888%20SE%20Lambert%20St
    """
    solr_params = {"q": "val", "rows": "6"}
    pelias_params_str = PeliasToSolr.solr_to_pelias_param_str(solr_params)
    assert "text=val" in pelias_params_str
    assert "size=6" in pelias_params_str


def test_switch_autocomplete_to_search_service(urls):
    """
    send an interpolated address to the query, and expect that:
    https://ws-st.trimet.org/pelias/v1/autocomplete?text=888%20SE%20Lambert%20St
    https://ws-st.trimet.org/pelias/v1/search?text=888%20SE%20Lambert%20St
    """
    solr_params = {"q": "888 SE Lambert St"}
    res = PeliasToSolr.call_pelias(solr_params, urls["auto"], urls["search"])
    assert res.num_records() > 0
    assert "888 SE Lambert" in res.response.docs[0].name


def test_no_results(base_path):
    p = parse("data/autocomplete_no_results.json", base_path)
    assert len(p.response.docs) == 0
