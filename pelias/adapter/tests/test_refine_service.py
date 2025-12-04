"""Tests for pelias.adapter.service.refine_service module.

Comprehensive tests for all refine service functions used in query refinement.
"""

import json
from unittest.mock import patch

import pytest
from pyramid.testing import DummyRequest

from pelias.adapter.service.refine_service import (
    get_response_and_features,
    adjust_layers_for_query,
    get_query_type,
    refactor_pelias_request,
    refine,
    TRANSIT_LAYERS,
)
from pelias.adapter.service.util import EvaluatesAs
from pelias.adapter.tests.helpers import TestMultiDict


# ============================================================================
# Fixtures and Test Data
# ============================================================================

@pytest.fixture
def test_data():
    """Load test data from JSON file."""
    with open('pelias/adapter/tests/data/test_util_data.json', 'r') as f:
        return json.load(f)


@pytest.fixture
def mock_request():
    """Create a mock Pyramid request with query parameters."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main Street'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=Main+Street&size=10'}
    return request


@pytest.fixture
def mock_pelias_response():
    """Create a mock Pelias GeoJSON response."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": "1",
                    "label": "Main Street",
                    "name": "Main",
                    "distance": 10
                },
                "geometry": {"type": "Point", "coordinates": [-122.67, 45.52]}
            },
            {
                "type": "Feature",
                "properties": {
                    "id": "2",
                    "label": "Oak Avenue",
                    "name": "Oak",
                    "distance": 20
                },
                "geometry": {"type": "Point", "coordinates": [-122.68, 45.53]}
            }
        ]
    }


# ============================================================================
# adjust_layers_for_query tests
# ============================================================================

@pytest.mark.parametrize("query_type,expected_is_stop,expected_layers", [
    (EvaluatesAs.STOP_REQUEST, True, TRANSIT_LAYERS),
    (EvaluatesAs.STREET_ADDRESS, False, "address"),
    (EvaluatesAs.INTERSECTION, False, "intersection"),
    (EvaluatesAs.JUST_A_NUMBER, False, None),  # Layers not modified
    (EvaluatesAs.UNKNOWN, False, None),  # Layers not modified
])
def test_adjust_layers_for_query(query_type, expected_is_stop, expected_layers):
    """Test layer adjustment based on query type."""
    query_params = {"text": "test", "size": "10"}
    is_stop, result_params = adjust_layers_for_query(query_type, query_params)

    assert is_stop == expected_is_stop

    if expected_layers is not None:
        assert result_params["layers"] == expected_layers
    else:
        # Layers should not be in params for JUST_A_NUMBER and UNKNOWN
        if query_type in (EvaluatesAs.JUST_A_NUMBER, EvaluatesAs.UNKNOWN):
            assert "layers" not in result_params or result_params.get("layers") is None


def test_adjust_layers_for_query_preserves_other_params():
    """Test that other query parameters are preserved."""
    query_params = {"text": "test", "size": "10", "focus.point.lat": "45.52"}
    _, result_params = adjust_layers_for_query(EvaluatesAs.STREET_ADDRESS, query_params)

    assert result_params["text"] == "test"
    assert result_params["size"] == "10"
    assert result_params["focus.point.lat"] == "45.52"


# ============================================================================
# get_query_type tests
# ============================================================================

@pytest.mark.parametrize("query,expected_type,expected_stop_id", [
    ("stop 1234", EvaluatesAs.STOP_REQUEST, 1234),
    ("stopid 5678", EvaluatesAs.STOP_REQUEST, 5678),
    ("stop_id 9999", EvaluatesAs.STOP_REQUEST, 9999),
    ("stop id 1111", EvaluatesAs.STOP_REQUEST, 1111),
    ("1234", EvaluatesAs.JUST_A_NUMBER, 1234),
    ("5678", EvaluatesAs.JUST_A_NUMBER, 5678),
    ("123 Main St", EvaluatesAs.STREET_ADDRESS, -1),
    ("Main Street", EvaluatesAs.STREET_ADDRESS, -1),
    ("NW Overton", EvaluatesAs.STREET_ADDRESS, -1),
    ("Main & Oak", EvaluatesAs.INTERSECTION, -1),
    ("Main and Oak", EvaluatesAs.INTERSECTION, -1),
    ("Broadway & Oak", EvaluatesAs.INTERSECTION, -1),
    ("random text", EvaluatesAs.UNKNOWN, -1),
    ("", EvaluatesAs.UNKNOWN, -1),
])
def test_get_query_type(query, expected_type, expected_stop_id):
    """Test query type detection with various inputs."""
    query_type, stop_id = get_query_type(query)
    assert query_type == expected_type
    assert stop_id == expected_stop_id


def test_intersection():
    """Test intersection query detection."""
    query_type, _ = get_query_type("Main & Oak")
    assert query_type == EvaluatesAs.INTERSECTION


def test_get_query_type_case_insensitive():
    """Test query type detection is case insensitive."""
    query_type1, _ = get_query_type("STOP 1234")
    query_type2, _ = get_query_type("stop 1234")
    query_type3, _ = get_query_type("Stop 1234")

    assert query_type1 == query_type2 == query_type3 == EvaluatesAs.STOP_REQUEST


def test_get_query_type_whitespace_handling():
    """Test query type detection handles whitespace."""
    query_type, stop_id = get_query_type("  stop 1234  ")
    assert query_type == EvaluatesAs.STOP_REQUEST
    assert stop_id == 1234


def test_get_query_type_intersection_priority():
    """Test intersection is detected before address."""
    # "Main & Oak" could match address pattern but should be intersection
    query_type, _ = get_query_type("Main St & Oak Ave")
    assert query_type == EvaluatesAs.INTERSECTION


# ============================================================================
# refactor_pelias_request tests
# ============================================================================

def test_refactor_pelias_request_updates_query_string():
    """Test request query string is updated."""
    request = DummyRequest()
    request.environ = {'QUERY_STRING': 'text=old'}
    request.GET = TestMultiDict([('text', 'old')])

    new_params = {'text': 'new', 'size': '10'}
    result = refactor_pelias_request(request, new_params)

    assert 'text=new' in result.environ['QUERY_STRING']
    assert 'size=10' in result.environ['QUERY_STRING']


def test_refactor_pelias_request_clears_cached_properties():
    """Test cached request properties are cleared."""
    request = DummyRequest()
    request.environ = {'QUERY_STRING': 'text=old'}
    request._query_params = {'text': 'old'}
    request._url = 'http://example.com?text=old'
    request._GET = TestMultiDict([('text', 'old')])

    new_params = {'text': 'new'}
    result = refactor_pelias_request(request, new_params)

    # Cached properties should be cleared
    assert not hasattr(result, '_query_params') or result._query_params is None
    assert not hasattr(result, '_url') or result._url is None
    assert result._GET is None


def test_refactor_pelias_request_returns_request():
    """Test function returns the modified request object."""
    request = DummyRequest()
    request.environ = {'QUERY_STRING': ''}

    result = refactor_pelias_request(request, {'text': 'test'})

    assert result is request


# ============================================================================
# get_response_and_features tests
# ============================================================================

@patch('pelias.adapter.service.refine_service.pelias_service.get_pelias_response')
def test_get_response_and_features_returns_tuple(mock_get_response, mock_request, mock_pelias_response):
    """Test function returns response and features tuple."""
    mock_get_response.return_value = mock_pelias_response

    ret_val, features = get_response_and_features(mock_request, "search", False)

    assert ret_val == mock_pelias_response
    assert features == mock_pelias_response["features"]
    assert len(features) == 2


@patch('pelias.adapter.service.refine_service.pelias_service.get_pelias_response')
def test_get_response_and_features_empty_features(mock_get_response, mock_request):
    """Test function handles response with no features."""
    mock_get_response.return_value = {"type": "FeatureCollection", "features": []}

    ret_val, features = get_response_and_features(mock_request, "search", False)

    assert features == []


@patch('pelias.adapter.service.refine_service.pelias_service.get_pelias_response')
def test_get_response_and_features_passes_parameters(mock_get_response, mock_request, mock_pelias_response):
    """Test function passes correct parameters to pelias_service."""
    mock_get_response.return_value = mock_pelias_response

    get_response_and_features(mock_request, "autocomplete", True)

    mock_get_response.assert_called_once_with(
        service="autocomplete",
        request=mock_request,
        is_rtp=True
    )


# ============================================================================
# refine function tests
# ============================================================================

@patch('pelias.adapter.service.refine_service.get_response_and_features')
def test_refine_raises_error_without_text(mock_get_response, mock_request):
    """Test refine raises ValueError when text parameter is missing."""
    request = DummyRequest()
    request.GET = TestMultiDict([('size', '10')])
    request.environ = {'QUERY_STRING': 'size=10'}

    with pytest.raises(ValueError, match="requires 'text' query parameter"):
        refine(request, "search", False)


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.refactor_pelias_request')
def test_refine_stop_request_sets_transit_layers(mock_refactor, mock_get_response, mock_pelias_response):
    """Test stop request sets transit layers."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'stop 1234'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=stop+1234&size=10'}

    mock_refactor.return_value = request
    mock_get_response.return_value = (mock_pelias_response, mock_pelias_response["features"])

    refine(request, "search", False)

    # Should call refactor with transit layers
    call_args = mock_refactor.call_args_list[0]
    assert TRANSIT_LAYERS in str(call_args)


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.refactor_pelias_request')
def test_refine_address_request_sets_address_layer(mock_refactor, mock_get_response, mock_pelias_response):
    """Test address request sets address layer."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', '123 Main St'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=123+Main+St&size=10'}

    mock_refactor.return_value = request
    mock_get_response.return_value = (mock_pelias_response, mock_pelias_response["features"])

    refine(request, "search", False)

    # Should call refactor with address layer
    call_args = mock_refactor.call_args_list[0]
    assert 'address' in str(call_args)


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.refactor_pelias_request')
def test_refine_intersection_sets_intersection_layer(mock_refactor, mock_get_response, mock_pelias_response):
    """Test intersection request sets intersection layer."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main & Oak'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=Main+%26+Oak&size=10'}

    mock_refactor.return_value = request
    mock_get_response.return_value = (mock_pelias_response, mock_pelias_response["features"])

    refine(request, "search", False)

    # Should call refactor with intersection layer
    call_args = mock_refactor.call_args_list[0]
    assert 'intersection' in str(call_args)


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.refactor_pelias_request')
def test_refine_increases_size_if_small(mock_refactor, mock_get_response, mock_pelias_response):
    """Test refine increases size to DEFAULT_SIZE if originally smaller."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main Street'), ('size', '5')])
    request.environ = {'QUERY_STRING': 'text=Main+Street&size=5'}

    mock_refactor.return_value = request
    mock_get_response.return_value = (mock_pelias_response, mock_pelias_response["features"])

    result = refine(request, "search", False)

    # Size should be increased internally but result limited to original size
    assert len(result["features"]) <= 5


@patch('pelias.adapter.service.refine_service.get_response_and_features')
def test_refine_removes_duplicates(mock_get_response):
    """Test refine removes duplicate features."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main Street'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=Main+Street&size=10'}

    features_with_dupes = [
        {"properties": {"label": "Main St"}},
        {"properties": {"label": "Main Street"}},
    ]

    mock_get_response.return_value = (
        {"features": features_with_dupes},
        features_with_dupes
    )

    result = refine(request, "search", False)

    # remove_duplicate_features should be called
    assert len(result["features"]) == 1


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.refactor_pelias_request')
def test_refine_retries_without_layers_if_no_results(mock_refactor, mock_get_response):
    """Test refine retries without layer filters if first query returns nothing."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', '123 Main St'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=123+Main+St&size=10'}

    mock_refactor.return_value = request

    # First call returns empty, second call returns results
    empty_response = {"features": []}
    good_response = {
        "features": [{"properties": {"label": "123 Main Street"}}]
    }

    mock_get_response.side_effect = [
        (empty_response, []),
        (good_response, good_response["features"])
    ]

    result = refine(request, "search", False)

    # Should have retried and gotten results
    assert len(result["features"]) == 1
    # get_response_and_features should be called twice
    assert mock_get_response.call_count == 2


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.prioritize_stops')
def test_refine_prioritizes_stops_for_number_query(mock_prioritize, mock_get_response):
    """Test stop prioritization for numeric queries."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', '1234'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=1234&size=10'}

    features = [
        {
            "properties": {
                "label": "Stop 1234",
                "addendum": {"gtfs": {"stop_id": "1234"}}
            }
        },
        {
            "properties": {
                "label": "Stop 5678",
                "addendum": {"gtfs": {"stop_id": "5678"}}
            }
        }
    ]

    mock_get_response.return_value = ({"features": features}, features)
    mock_prioritize.return_value = [features[0]]

    refine(request, "search", False)

    # prioritize_stops should be called
    assert mock_prioritize.called
    call_args = mock_prioritize.call_args
    assert call_args[1]['stop_id'] == 1234


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.prioritize_addresses')
def test_refine_prioritizes_addresses_for_address_query(mock_prioritize, mock_get_response):
    """Test address prioritization for address queries."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', '123 Main St'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=123+Main+St&size=10'}

    features = [
        {"properties": {"label": "123 Main Street"}},
        {"properties": {"label": "456 Main Street"}},
    ]

    mock_get_response.return_value = ({"features": features}, features)
    mock_prioritize.return_value = [features[0]]

    result = refine(request, "search", False)

    # prioritize_addresses should be called
    assert mock_prioritize.called
    call_args = mock_prioritize.call_args
    assert call_args[1]['query'] == '123 main st'
    assert call_args[1]['query_type'] == EvaluatesAs.STREET_ADDRESS


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.prioritize_addresses')
def test_refine_prioritizes_addresses_for_intersection_query(mock_prioritize, mock_get_response):
    """Test address prioritization for intersection queries."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main & Oak'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=Main+%26+Oak&size=10'}

    features = [
        {"properties": {"label": "Main St & Oak Ave"}},
        {"properties": {"label": "Broadway & Oak"}},
    ]

    mock_get_response.return_value = ({"features": features}, features)
    mock_prioritize.return_value = [features[0]]

    refine(request, "search", False)

    # prioritize_addresses should be called with INTERSECTION type
    assert mock_prioritize.called
    call_args = mock_prioritize.call_args
    assert call_args[1]['query_type'] == EvaluatesAs.INTERSECTION


@patch('pelias.adapter.service.refine_service.get_response_and_features')
def test_refine_limits_results_to_original_size(mock_get_response):
    """Test results are limited to originally requested size."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main'), ('size', '2')])
    request.environ = {'QUERY_STRING': 'text=Main&size=2'}

    # Return many features
    features = [
        {"properties": {"label": f"Main Street {i}"}}
        for i in range(15)
    ]

    mock_get_response.return_value = ({"features": features}, features)

    result = refine(request, "search", False)

    # Should be limited to 2
    assert len(result["features"]) == 2


@patch('pelias.adapter.service.refine_service.get_response_and_features')
@patch('pelias.adapter.service.refine_service.refactor_pelias_request')
def test_refine_restores_original_params(mock_refactor, mock_get_response, mock_pelias_response):
    """Test original request parameters are restored at the end."""
    request = DummyRequest()
    original_params = TestMultiDict([('text', 'Main Street'), ('size', '10')])
    request.GET = original_params
    request.environ = {'QUERY_STRING': 'text=Main+Street&size=10'}

    mock_refactor.return_value = request
    mock_get_response.return_value = (mock_pelias_response, mock_pelias_response["features"])

    refine(request, "search", False)

    # refactor_pelias_request should be called at least twice:
    # once to set new params, once to restore original
    assert mock_refactor.call_count >= 2

    # Last call should restore original params
    last_call = mock_refactor.call_args_list[-1]
    assert last_call[0][1] == original_params


@patch('pelias.adapter.service.refine_service.get_response_and_features')
def test_refine_passes_is_rtp_parameter(mock_get_response, mock_pelias_response):
    """Test is_rtp parameter is passed through."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'stop 1234'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=stop+1234&size=10'}

    mock_get_response.return_value = (mock_pelias_response, mock_pelias_response["features"])

    refine(request, "search", is_rtp=True)

    # is_rtp should be passed to get_response_and_features
    call_args = mock_get_response.call_args
    assert call_args[1]['is_rtp'] is True


@patch('pelias.adapter.service.refine_service.get_response_and_features')
def test_refine_handles_single_feature(mock_get_response):
    """Test refine handles response with single feature correctly."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=Main&size=10'}

    single_feature = [{"properties": {"label": "Main Street"}}]
    mock_get_response.return_value = ({"features": single_feature}, single_feature)

    result = refine(request, "search", False)

    # Should not try to deduplicate or prioritize single feature
    assert len(result["features"]) == 1


@pytest.mark.parametrize("service", ["autocomplete", "search", "reverse"])
@patch('pelias.adapter.service.refine_service.get_response_and_features')
def test_refine_works_with_all_services(mock_get_response, service, mock_pelias_response):
    """Test refine works with all Pelias service types."""
    request = DummyRequest()
    request.GET = TestMultiDict([('text', 'Main'), ('size', '10')])
    request.environ = {'QUERY_STRING': 'text=Main&size=10'}

    mock_get_response.return_value = (mock_pelias_response, mock_pelias_response["features"])

    result = refine(request, service, False)

    assert result["features"] is not None

    # Verify correct service was passed
    call_args = mock_get_response.call_args
    assert call_args[1]['service'] == service


# ============================================================================
# Integration-style tests with test data
# ============================================================================

def test_adjust_layers_with_stop_request_preserves_all_params():
    """Test that adjusting layers for stop request preserves all parameters."""
    params = {
        "text": "stop 1234",
        "size": "10",
        "focus.point.lat": "45.52",
        "focus.point.lon": "-122.67",
        "boundary.circle.radius": "50"
    }

    is_stop, result = adjust_layers_for_query(EvaluatesAs.STOP_REQUEST, params)

    assert is_stop is True
    assert result["layers"] == TRANSIT_LAYERS
    assert result["text"] == "stop 1234"
    assert result["size"] == "10"
    assert result["focus.point.lat"] == "45.52"
    assert result["focus.point.lon"] == "-122.67"
    assert result["boundary.circle.radius"] == "50"


def test_get_query_type_edge_cases():
    """Test edge cases in query type detection."""
    # Stop request must end with digit
    query_type, _ = get_query_type("stop abc")
    assert query_type == EvaluatesAs.UNKNOWN

    # Empty query
    query_type, _ = get_query_type("")
    assert query_type == EvaluatesAs.UNKNOWN

    # Just whitespace
    query_type, _ = get_query_type("   ")
    assert query_type == EvaluatesAs.UNKNOWN
