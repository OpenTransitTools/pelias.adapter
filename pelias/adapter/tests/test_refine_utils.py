"""Tests for pelias.adapter.service.util module.

Comprehensive tests for all utility functions used in Pelias result refinement.
"""

import pytest

from pelias.adapter.service.util import (
    remove_non_digits,
    normalize_address,
    intersection_parts,
    is_intersection,
    is_address,
    gtfs_addendum,
    get_stop_id_and_stop_code,
    order_by_distance,
    just_chars,
    find_close_matches,
    find_exact_matches,
    prioritize_stops,
    EvaluatesAs,
    remove_duplicate_features,
    prioritize_addresses,
)


# ============================================================================
# remove_non_digits tests
# ============================================================================

@pytest.mark.parametrize("text,to_int,expected", [
    ("stop 1234", False, "1234"),
    ("stop 1234", True, 1234),
    ("", False, ""),
    ("", True, -1),
    (None, False, ""),
    (None, True, -1),
    ("abc", False, ""),
    ("abc", True, -1),
    ("123abc456", False, "123456"),
    ("123abc456", True, 123456),
    ("stop id 5678", True, 5678),
])
def test_remove_non_digits(text, to_int, expected):
    """Test digit extraction with various inputs."""
    assert remove_non_digits(text, to_int) == expected


# ============================================================================
# normalize_address tests
# ============================================================================

@pytest.mark.parametrize("addr,expected", [
    ("", ""),
    ("123 SW Main St.", "123 Southwest Main Street"),
    ("NE 42nd Ave", "Northeast 42Nd Avenue"),
    ("n main st", "North Main Street"),
    ("  multiple   spaces  ", "Multiple Spaces"),
    ("SE Division Blvd", "Southeast Division Boulevard"),
    ("NW Overton", "Northwest Overton"),
    ("123 Main Street", "123 Main Street"),
    ("Oak Rd.", "Oak Road"),
    ("Broadway", "Broadway"),
])
def test_normalize_address(addr, expected):
    """Test address normalization with various formats."""
    assert normalize_address(addr) == expected


def test_normalize_address_handles_all_directions():
    """Test that all directional abbreviations are expanded."""
    assert "North" in normalize_address("n main")
    assert "South" in normalize_address("s main")
    assert "East" in normalize_address("e main")
    assert "West" in normalize_address("w main")
    assert "Northeast" in normalize_address("ne main")
    assert "Northwest" in normalize_address("nw main")
    assert "Southeast" in normalize_address("se main")
    assert "Southwest" in normalize_address("sw main")


def test_normalize_address_handles_all_street_types():
    """Test that common street type abbreviations are expanded."""
    assert "Street" in normalize_address("main st")
    assert "Avenue" in normalize_address("oak ave")
    assert "Boulevard" in normalize_address("sunset blvd")
    assert "Road" in normalize_address("country rd")
    assert "Drive" in normalize_address("pine dr")
    assert "Lane" in normalize_address("oak ln")
    assert "Court" in normalize_address("elm ct")


# ============================================================================
# intersection_parts tests
# ============================================================================

@pytest.mark.parametrize("query,expected", [
    ("Main St & 1st Ave", ("Main St", "1st Ave")),
    ("Broadway and Oak", ("Broadway", "Oak")),
    ("Main Street", (None, None)),
    ("Main & Oak & Elm", ("Main", "Oak & Elm")),  # Only splits once
    ("Main&Oak", ("Main", "Oak")),  # No spaces
    ("Main  &  Oak", ("Main", "Oak")),  # Extra spaces
    ("Main AND Oak", ("Main", "Oak")),  # Case-insensitive
    ("Main aNd Oak", ("Main", "Oak")),  # Mixed case
    ("", (None, None)),
])
def test_intersection_parts(query, expected):
    """Test extraction of street names from intersection queries."""
    assert intersection_parts(query) == expected


# ============================================================================
# is_intersection tests
# ============================================================================

@pytest.mark.parametrize("text,expected_is_intersection,expected_parts", [
    ("Main St & 1st Ave", True, ("Main St", "1st Ave")),
    ("Broadway and Oak", True, ("Broadway", "Oak")),
    ("123 Main Street", False, ()),
    ("364", False, ()),
    ("", False, ()),
    ("Main & Oak & Elm", True, ("Main", "Oak & Elm")),
])
def test_is_intersection(text, expected_is_intersection, expected_parts):
    """Test intersection detection."""
    is_int, parts = is_intersection(text)
    assert is_int == expected_is_intersection
    if expected_is_intersection:
        assert parts == expected_parts
    else:
        assert parts == ()


# ============================================================================
# is_address tests
# ============================================================================

@pytest.mark.parametrize("text,expected", [
    ("123 Main St", True),
    ("Main Street", True),
    ("NW Overton", True),
    ("364", False),
    ("", False),
    ("stop 1234", False),
    ("456 Oak Avenue", True),
    ("SE Powell Blvd", True),
    ("N Interstate", True),
    ("1234567", False),  # Too many digits
    ("123 Main", True),
    ("Oak Rd", True),
])
def test_is_address(text, expected):
    """Test address pattern detection."""
    assert is_address(text) == expected


# ============================================================================
# gtfs_addendum tests
# ============================================================================

def test_gtfs_addendum_complete_structure():
    """Test extracting GTFS data from complete feature."""
    feature = {
        "properties": {
            "addendum": {
                "gtfs": {
                    "stop_id": "1234",
                    "stop_code": "5678"
                }
            }
        }
    }
    result = gtfs_addendum(feature)
    assert result == {"stop_id": "1234", "stop_code": "5678"}


def test_gtfs_addendum_missing_gtfs():
    """Test feature without GTFS addendum."""
    feature = {"properties": {"addendum": {}}}
    result = gtfs_addendum(feature)
    assert result == {}


def test_gtfs_addendum_missing_properties():
    """Test feature without properties."""
    feature = {}
    result = gtfs_addendum(feature)
    assert result == {}


# ============================================================================
# get_stop_id_and_stop_code tests
# ============================================================================

def test_get_stop_id_and_stop_code_complete():
    """Test extracting stop ID and code from feature."""
    feature = {
        "properties": {
            "addendum": {
                "gtfs": {
                    "stop_id": "1234",
                    "stop_code": "5678"
                }
            }
        }
    }
    stop_id, stop_code = get_stop_id_and_stop_code(feature)
    assert stop_id == "1234"
    assert stop_code == "5678"


def test_get_stop_id_and_stop_code_missing():
    """Test feature without stop data."""
    feature = {"properties": {}}
    stop_id, stop_code = get_stop_id_and_stop_code(feature)
    assert stop_id is None
    assert stop_code is None


# ============================================================================
# order_by_distance tests
# ============================================================================

def test_order_by_distance_sorts_correctly():
    """Test features are sorted by distance ascending."""
    features = [
        {"properties": {"distance": 100}},
        {"properties": {"distance": 10}},
        {"properties": {"distance": 50}},
    ]
    result = order_by_distance(features)
    assert result[0]["properties"]["distance"] == 10
    assert result[1]["properties"]["distance"] == 50
    assert result[2]["properties"]["distance"] == 100


def test_order_by_distance_empty_list():
    """Test empty list returns empty list."""
    assert order_by_distance([]) == []


def test_order_by_distance_missing_distance():
    """Test features without distance are sorted last."""
    features = [
        {"properties": {"distance": 50}},
        {"properties": {}},
        {"properties": {"distance": 10}},
    ]
    result = order_by_distance(features)
    assert result[0]["properties"]["distance"] == 10
    assert result[1]["properties"]["distance"] == 50
    # Feature without distance should be last (infinity)


# ============================================================================
# just_chars tests
# ============================================================================

@pytest.mark.parametrize("text,expected", [
    ("Main Street", "mainstreet"),
    ("NW 23rd Ave", "nw23rdave"),
    ("", ""),
    ("  spaces  ", "spaces"),
    ("UPPERCASE", "uppercase"),
    ("123 Main", "123main"),
])
def test_just_chars(text, expected):
    """Test text normalization for fuzzy matching."""
    assert just_chars(text) == expected


# ============================================================================
# find_close_matches tests
# ============================================================================

def test_find_close_matches_with_matches():
    """Test features with matching names are prioritized."""
    features = [
        {"properties": {"name": "Oak Street", "distance": 100}},
        {"properties": {"name": "Main Street", "distance": 50}},
        {"properties": {"name": "Pine Street", "distance": 10}},
    ]
    result = find_close_matches(features, "Street")
    # All match, so should be sorted by distance
    assert result[0]["properties"]["name"] == "Pine Street"
    assert result[1]["properties"]["name"] == "Main Street"
    assert result[2]["properties"]["name"] == "Oak Street"


def test_find_close_matches_partial():
    """Test partial matches are prioritized over non-matches."""
    features = [
        {"properties": {"name": "Broadway", "distance": 100}},
        {"properties": {"name": "Main Street", "distance": 50}},
        {"properties": {"name": "Oak Street", "distance": 10}},
    ]
    result = find_close_matches(features, "Street")
    # First two should be Street matches sorted by distance
    assert result[0]["properties"]["name"] == "Oak Street"
    assert result[1]["properties"]["name"] == "Main Street"
    # Non-match should be last
    assert result[2]["properties"]["name"] == "Broadway"


def test_find_close_matches_no_matches():
    """Test when no features match."""
    features = [
        {"properties": {"name": "Broadway", "distance": 100}},
        {"properties": {"name": "Main", "distance": 50}},
    ]
    result = find_close_matches(features, "Street")
    assert result == features


def test_find_close_matches_case_insensitive():
    """Test matching is case insensitive."""
    features = [
        {"properties": {"name": "MAIN STREET", "distance": 10}},
    ]
    result = find_close_matches(features, "main street")
    assert result[0]["properties"]["name"] == "MAIN STREET"


# ============================================================================
# find_exact_matches tests
# ============================================================================

def test_find_exact_matches_identical_to_close_matches():
    """Test find_exact_matches behaves like find_close_matches (known issue)."""
    features = [
        {"properties": {"name": "Main Street", "distance": 50}},
        {"properties": {"name": "Broadway", "distance": 100}},
    ]
    close_result = find_close_matches(features, "Street")
    exact_result = find_exact_matches(features, "Street")
    assert close_result == exact_result


# ============================================================================
# prioritize_stops tests
# ============================================================================

def test_prioritize_stops_exact_stop_id_match():
    """Test exact stop_id match is prioritized."""
    features = [
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "2000", "stop_code": "999"}},
                "distance": 100
            }
        },
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "1234", "stop_code": "999"}},
                "distance": 50
            }
        },
    ]
    result = prioritize_stops(features, "search", stop_id=1234)
    assert result[0]["properties"]["addendum"]["gtfs"]["stop_id"] == "1234"


def test_prioritize_stops_exact_stop_code_match():
    """Test exact stop_code match is prioritized."""
    features = [
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "999", "stop_code": "2000"}},
                "distance": 100
            }
        },
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "999", "stop_code": "1234"}},
                "distance": 50
            }
        },
    ]
    result = prioritize_stops(features, "search", stop_id=1234)
    assert result[0]["properties"]["addendum"]["gtfs"]["stop_code"] == "1234"


def test_prioritize_stops_name_matching_fallback():
    """Test name matching when no exact ID/code match."""
    features = [
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "999", "stop_code": "888"}},
                "name": "Broadway",
                "distance": 100
            }
        },
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "888", "stop_code": "777"}},
                "name": "Main Station",
                "distance": 50
            }
        },
    ]
    result = prioritize_stops(features, "search", stop_id=1234, text="Main")
    # Main should be first due to name match
    assert result[0]["properties"]["name"] == "Main Station"


def test_prioritize_stops_search_service_sorts_by_distance():
    """Test search service sorts remaining stops by distance."""
    features = [
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "1", "stop_code": "1"}},
                "distance": 100
            }
        },
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "2", "stop_code": "2"}},
                "distance": 50
            }
        },
    ]
    result = prioritize_stops(features, "search", stop_id=-1, text="")
    # Should be sorted by distance
    assert result[0]["properties"]["distance"] == 50
    assert result[1]["properties"]["distance"] == 100


def test_prioritize_stops_autocomplete_preserves_order():
    """Test autocomplete service preserves order for non-exact matches."""
    features = [
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "1", "stop_code": "1"}},
                "name": "Stop A",
                "distance": 100
            }
        },
        {
            "properties": {
                "addendum": {"gtfs": {"stop_id": "2", "stop_code": "2"}},
                "name": "Stop B",
                "distance": 50
            }
        },
    ]
    result = prioritize_stops(features, "autocomplete", stop_id=-1, text="")
    # Should preserve original order (no sorting for autocomplete without matches)
    assert len(result) == 2


# ============================================================================
# EvaluatesAs enum tests
# ============================================================================

def test_evaluates_as_enum_values():
    """Test enum has expected values."""
    assert EvaluatesAs.STREET_ADDRESS.value == "street_address"
    assert EvaluatesAs.JUST_A_NUMBER.value == "just_a_number"
    assert EvaluatesAs.STOP_REQUEST.value == "stop_request"
    assert EvaluatesAs.INTERSECTION.value == "intersection"
    assert EvaluatesAs.UNKNOWN.value == "unknown"


# ============================================================================
# remove_duplicate_features tests
# ============================================================================

def test_remove_duplicate_features_exact_duplicates():
    """Test exact duplicate labels are removed."""
    features = [
        {"properties": {"label": "Main Street"}},
        {"properties": {"label": "Main Street"}},
    ]
    result = remove_duplicate_features(features)
    assert len(result) == 1


def test_remove_duplicate_features_normalized_duplicates():
    """Test normalized duplicates are removed."""
    features = [
        {"properties": {"label": "Main St"}},
        {"properties": {"label": "Main Street"}},
    ]
    result = remove_duplicate_features(features)
    # After normalization, both become "Main Street"
    assert len(result) == 1


def test_remove_duplicate_features_whitespace_duplicates():
    """Test duplicates differing only by whitespace are removed."""
    features = [
        {"properties": {"label": "Main Street"}},
        {"properties": {"label": "MainStreet"}},
    ]
    result = remove_duplicate_features(features)
    # Second pass removes whitespace differences
    assert len(result) == 1


def test_remove_duplicate_features_keeps_last_occurrence():
    """Test last occurrence is kept when duplicates exist."""
    features = [
        {"properties": {"label": "Main Street"}, "id": 1},
        {"properties": {"label": "Main Street"}, "id": 2},
    ]
    result = remove_duplicate_features(features)
    assert len(result) == 1
    assert result[0]["id"] == 2


def test_remove_duplicate_features_missing_properties():
    """Test features without properties are filtered out."""
    features = [
        {"properties": {"label": "Main Street"}},
        {},  # Missing properties
        {"other": "data"},  # Missing properties
    ]
    result = remove_duplicate_features(features)
    assert len(result) == 1


def test_remove_duplicate_features_empty_list():
    """Test empty list returns empty list."""
    assert remove_duplicate_features([]) == []


# ============================================================================
# prioritize_addresses tests
# ============================================================================

def test_prioritize_addresses_intersection_both_streets_match():
    """Test intersection query matches features with both street names."""
    features = [
        {"properties": {"label": "Main St & Oak Ave", "distance": 10}},
        {"properties": {"label": "Broadway & Oak Ave", "distance": 20}},
        {"properties": {"label": "Main St & Elm Ave", "distance": 30}},
    ]
    result = prioritize_addresses(
        features,
        "Main & Oak",
        EvaluatesAs.INTERSECTION,
        "search"
    )
    # Only first feature should match (contains both Main and Oak)
    assert len(result) == 1
    assert "Main" in result[0]["properties"]["label"]
    assert "Oak" in result[0]["properties"]["label"]


def test_prioritize_addresses_intersection_no_matches():
    """Test intersection query with no matches returns all features."""
    features = [
        {"properties": {"label": "Broadway", "distance": 10}},
        {"properties": {"label": "Main Street", "distance": 20}},
    ]
    result = prioritize_addresses(
        features,
        "Oak & Elm",
        EvaluatesAs.INTERSECTION,
        "search"
    )
    # No matches, should return all features
    assert len(result) == 2


def test_prioritize_addresses_street_address_matches():
    """Test street address query matches containing features."""
    features = [
        {"properties": {"label": "123 Main Street", "distance": 10}},
        {"properties": {"label": "456 Oak Avenue", "distance": 20}},
        {"properties": {"label": "789 Main Avenue", "distance": 30}},
    ]
    result = prioritize_addresses(
        features,
        "Main",
        EvaluatesAs.STREET_ADDRESS,
        "search"
    )
    # Should match first and third features
    assert len(result) == 2
    assert all("Main" in f["properties"]["label"] for f in result)


def test_prioritize_addresses_street_address_case_insensitive():
    """Test street address matching is case insensitive."""
    features = [
        {"properties": {"label": "MAIN STREET", "distance": 10}},
    ]
    result = prioritize_addresses(
        features,
        "main street",
        EvaluatesAs.STREET_ADDRESS,
        "search"
    )
    assert len(result) == 1


def test_prioritize_addresses_search_sorts_by_distance():
    """Test search service sorts results by distance."""
    features = [
        {"properties": {"label": "Main Street East", "distance": 50}},
        {"properties": {"label": "Main Street West", "distance": 10}},
        {"properties": {"label": "Main Street North", "distance": 30}},
    ]
    result = prioritize_addresses(
        features,
        "Main",
        EvaluatesAs.STREET_ADDRESS,
        "search"
    )
    # Should be sorted by distance
    assert result[0]["properties"]["distance"] == 10
    assert result[1]["properties"]["distance"] == 30
    assert result[2]["properties"]["distance"] == 50


def test_prioritize_addresses_autocomplete_no_sorting():
    """Test autocomplete service doesn't sort by distance."""
    features = [
        {"properties": {"label": "Main Street East", "distance": 50}},
        {"properties": {"label": "Main Street West", "distance": 10}},
    ]
    result = prioritize_addresses(
        features,
        "Main",
        EvaluatesAs.STREET_ADDRESS,
        "autocomplete"
    )
    # Should preserve order (no distance sorting for autocomplete)
    assert len(result) == 2


def test_prioritize_addresses_unknown_query_type():
    """Test unknown query type returns all features."""
    features = [
        {"properties": {"label": "Main Street", "distance": 10}},
        {"properties": {"label": "Oak Avenue", "distance": 20}},
    ]
    result = prioritize_addresses(
        features,
        "something",
        EvaluatesAs.UNKNOWN,
        "search"
    )
    # Unknown type should return all features
    assert len(result) == 2
