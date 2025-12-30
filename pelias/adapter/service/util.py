"""Utility functions for processing and refining Pelias geocoding results.

This module provides helper functions for:
- Query type detection (stops, addresses, intersections)
- Feature deduplication and normalization
- Stop and address prioritization
- Text normalization and matching
"""

import enum
import re
from logging import getLogger
from typing import Optional, Any, Literal

logger = getLogger(__name__)


def remove_non_digits(text: Optional[str], to_int: bool = False):
    """Extract only digits from a string.
    
    Args:
        text: Input string that may contain digits and other characters
        to_int: If True, convert result to int; if False, return as string
        
    Returns:
        str | int: Digits as string, or as int if to_int=True, or -1 if conversion fails
        
    Examples:
        >>> remove_non_digits("stop 1234")
        "1234"
        >>> remove_non_digits("stop 1234", to_int=True)
        1234
        >>> remove_non_digits("", to_int=True)
        -1
    """
    if not text:
        return "" if not to_int else -1
    
    result = re.sub(r"\D+", "", text)
    
    if to_int:
        try:
            return int(result) if result else -1
        except ValueError:
            return -1
    
    return result


def normalize_address(addr: str) -> str:
    """Normalize common street abbreviations and directions in a U.S. address.
    
    Converts abbreviated street types and directions to their full names,
    removes extra whitespace, and applies title case formatting.
    
    Args:
        addr: Address string to normalize
        
    Returns:
        str: Normalized address with expanded abbreviations and title case
        
    Examples:
        >>> normalize_address("123 SW Main St.")
        "123 Southwest Main Street"
        >>> normalize_address("NE 42nd Ave")
        "Northeast 42Nd Avenue"
    """
    if not addr:
        return ""

    addr = addr.lower().strip()

    # Directional abbreviations to full names (word boundaries ensure exact matches)
    directions = {
        r"\bn\b": "north",
        r"\bs\b": "south",
        r"\be\b": "east",
        r"\bw\b": "west",
        r"\bnw\b": "northwest",
        r"\bne\b": "northeast",
        r"\bsw\b": "southwest",
        r"\bse\b": "southeast",
    }

    # Street type abbreviations to full names
    streets = {
        r"\bst\b": "street",
        r"\bstreet\b": "street",
        r"\bave\b": "avenue",
        r"\bav\b": "avenue",
        r"\baven\b": "avenue",
        r"\bavenue\b": "avenue",
        r"\bblvd\b": "boulevard",
        r"\brd\b": "road",
        r"\bdr\b": "drive",
        r"\bln\b": "lane",
        r"\bct\b": "court",
        r"\bcir\b": "circle",
        r"\bhwy\b": "highway",
        r"\bpl\b": "place",
        r"\bter\b": "terrace",
        r"\bpkwy\b": "parkway",
    }

    # Merge both dictionaries and apply all replacements
    # Also handles optional periods after abbreviations (e.g., "St." -> "street")
    for pattern, repl in {**directions, **streets}.items():
        addr = re.sub(pattern + r"\.?", repl, addr)

    # Collapse multiple spaces into one and apply title case
    addr = re.sub(r"\s+", " ", addr).strip().title()
    
    return addr

def intersection_parts(query: str):
    """Extract the two street names from an intersection query.
    
    Looks for separators like '&' or 'and' to split the query into two parts.
    
    Args:
        query: Query string like "Main St & 1st Ave" or "Broadway and Oak"
        
    Returns:
        tuple: Two street names if found, or (None, None) if not an intersection
        
    Examples:
        >>> intersection_parts("Main St & 1st Ave")
        ("Main St", "1st Ave")
        >>> intersection_parts("Broadway and Oak")
        ("Broadway", "Oak")
        >>> intersection_parts("Main Street")
        (None, None)
    """
    # Search for intersection separators: & or 'and' (case-insensitive)
    match = re.search(r"\s*&\s*|\s+and\s+", query, re.IGNORECASE)
    
    if match:
        # Split into exactly two parts at the first separator
        parts = re.split(r"\s*&\s*|\s+and\s+", query, maxsplit=1, flags=re.IGNORECASE)
        
        if len(parts) == 2:
            left, right = parts
            logger.debug(f"found intersection parts: {left} / {right}")
            return left.strip(), right.strip()
    
    return None, None


def is_intersection(text: str):
    """Detect if the query represents a street intersection.
    
    Args:
        text: Query string to analyze
        
    Returns:
        tuple: (True, (street1, street2)) if intersection found, 
               (False, ()) otherwise
               
    Examples:
        >>> is_intersection("Main St & 1st Ave")
        (True, ("Main St", "1st Ave"))
        >>> is_intersection("123 Main Street")
        (False, ())
    """
    if " and " in text or "&" in text:
        left, right = intersection_parts(text.strip())

        if left and right:
            return True, (left, right)
    else:
        return False, ()


def is_address(text: str) -> bool:
    """Detect if the query appears to be a street address.
    
    Checks for common address patterns:
    1. House number + street name (e.g., "123 Main St")
    2. Street name + street type suffix (e.g., "Main Street")
    3. Directional prefix + street name (e.g., "NW Overton")
    
    Args:
        text: Query string to analyze
        
    Returns:
        bool: True if query matches address patterns, False otherwise
        
    Examples:
        >>> is_address("123 Main St")
        True
        >>> is_address("Main Street")
        True
        >>> is_address("NW Overton")
        True
        >>> is_address("364")
        False
    """
    text = text.strip().lower()

    # Reject bare numbers without street names (e.g., "364" is just a stop ID)
    if re.fullmatch(r"\d{1,6}", text):
        return False

    # Pattern 1: House number followed by street name(s)
    # Matches: "123 Main", "456 Main Street", "789 NW Oak Ave"
    pattern_number_first = re.search(
        r"\b\d{1,6}\s+\w+(?:\s+\w+)*\b", text
    )

    # Pattern 2: Street name followed by common street type suffix
    # Matches: "Main Street", "Oak Avenue", "Broadway Blvd"
    pattern_name_suffix = re.search(
        r"\b\w+(?:\s+\w+)*\s+(st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|ct|court)\b",
        text
    )

    # Pattern 3: Directional prefix followed by street name
    # Matches: "NW Overton", "SE Powell", "N Interstate"
    pattern_directional = re.fullmatch(
        r"(n|s|e|w|ne|nw|se|sw)\s+\w+(?:\s+\w+)*", text
    )

    return bool(pattern_number_first or pattern_name_suffix or pattern_directional)
def gtfs_addendum(feature: dict[str, Any]) -> dict[str, Any]:
    """Extract GTFS data from a Pelias feature's addendum.
    
    Args:
        feature: Pelias GeoJSON feature object
        
    Returns:
        dict: GTFS data dictionary, or empty dict if not present
    """
    return (
        feature.get("properties", {})
        .get("addendum", {})
        .get("gtfs", {})
    )


def get_stop_id_and_stop_code(feature: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """Extract stop_id and stop_code from a transit stop feature.
    
    Args:
        feature: Pelias GeoJSON feature with GTFS data
        
    Returns:
        tuple: (stop_id, stop_code) or (None, None) if not present
    """
    data = gtfs_addendum(feature)
    return data.get("stop_id", None), data.get("stop_code", None)


def order_by_distance(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort features by their distance property in ascending order.
    
    Pelias includes a 'distance' property in search results indicating
    proximity to a focus point or bounding box.
    
    Args:
        features: List of Pelias GeoJSON features
        
    Returns:
        list: Features sorted by distance (closest first)
        
    Note:
        Assumes all features have a valid 'distance' property.
        Will raise ValueError if distance cannot be converted to float.
    """
    def _distance_key(feature: dict[str, Any]) -> float:
        return float(feature.get("properties", {}).get("distance", float('inf')))

    return sorted(features, key=_distance_key)


def just_chars(text: str) -> str:
    """Normalize text to lowercase letters only, no spaces or punctuation.
    
    Used for fuzzy matching where you want to ignore case, whitespace,
    and punctuation differences.
    
    Args:
        text: Text to normalize
        
    Returns:
        str: Lowercase text with spaces removed
        
    Examples:
        >>> just_chars("Main Street")
        "mainstreet"
        >>> just_chars("NW 23rd Ave")
        "nw23rdave"
    """
    return text.lower().strip().replace(" ", "")


def find_close_matches(features: list[dict[str, Any]], text: str) -> list[dict[str, Any]]:
    """Find and prioritize features whose names contain the search text.
    
    Performs substring matching ignoring case and whitespace, then sorts
    matches by distance and places them before non-matching features.
    
    Args:
        features: List of Pelias GeoJSON features to search
        text: Search text to match against feature names
        
    Returns:
        list: Features reordered with matches first (sorted by distance), 
              then remaining features in original order
    """
    # Find features where normalized text appears in normalized name
    partial_matches = [
        x for x in features 
        if just_chars(text) in just_chars(x.get("properties", {}).get("name", ""))
    ]
    
    if partial_matches:
        # Sort matches by distance (closest first)
        partial_matches = order_by_distance(partial_matches)
        # Preserve remaining features in original order
        remaining = [x for x in features if x not in partial_matches]
        return partial_matches + remaining
    
    return features


def find_exact_matches(features: list[dict[str, Any]], text: str) -> list[dict[str, Any]]:
    """Find and prioritize features whose names exactly match the search text.
    
    NOTE: Despite the name, this currently performs substring matching,
    not exact matching. Consider renaming or fixing the logic.
    
    Args:
        features: List of Pelias GeoJSON features to search
        text: Search text to match against feature names
        
    Returns:
        list: Features reordered with matches first (sorted by distance),
              then remaining features in original order
              
    TODO: This function is identical to find_close_matches. Either:
          1. Implement true exact matching logic, or
          2. Remove this function and use find_close_matches
    """
    # NOTE: This is currently doing substring matching, not exact matching
    partial_matches = [
        x for x in features 
        if just_chars(text) in just_chars(x.get("properties", {}).get("name", ""))
    ]
    
    if partial_matches:
        partial_matches = order_by_distance(partial_matches)
        remaining = [x for x in features if x not in partial_matches]
        return partial_matches + remaining
    
    return features






def prioritize_stops(
    features: list[dict[str, Any]], 
    service: str, 
    is_rtp: bool = False, 
    stop_id: int = -1, 
    text: str = ""
) -> list[dict[str, Any]]:
    """Prioritize and reorder transit stop results based on matching criteria.
    
    Prioritization order:
    1. Stops matching the exact stop_id or stop_code (sorted by distance)
    2. Stops with names containing the search text (sorted by distance if service='search')
    3. All other stops in original order
    
    Args:
        features: List of Pelias GeoJSON features
        service: Pelias service used ("autocomplete", "search", or "reverse")
        is_rtp: If True, disables TriMet-specific prioritization (currently unused)
        stop_id: Stop ID to match against stop_id and stop_code fields
        text: Search text for name matching
        
    Returns:
        list: Reordered features with best matches first
        
    Note:
        The is_rtp parameter is not currently used in the logic.
    """
    # Separate features into exact ID/code matches and everything else
    code_or_id_matches = []
    remaining_stops = []

    for feature in features:
        stop_id_value, stop_code_value = get_stop_id_and_stop_code(feature)
        
        # Check if stop_id or stop_code matches the search ID
        if stop_id_value == str(stop_id) or stop_code_value == str(stop_id):
            code_or_id_matches.append(feature)
        else:
            remaining_stops.append(feature)

    # If we found exact ID/code matches, return them sorted by distance
    if len(code_or_id_matches) > 0:
        logger.debug(
            f"found stop_id/stop_code matches: "
            f"{[get_stop_id_and_stop_code(f) for f in code_or_id_matches]}"
        )
        result = order_by_distance(code_or_id_matches)
        return result
    
    # No exact matches - try fuzzy name matching on remaining stops
    remaining_stops = find_close_matches(remaining_stops, text)

    # For search service, sort all remaining stops by distance
    if service == "search":
        remaining_stops = order_by_distance(remaining_stops)

    return remaining_stops


class EvaluatesAs(enum.Enum):
    """Query type classification for Pelias refinement.
    
    Used to determine how to adjust Pelias parameters and prioritize results.
    """
    STREET_ADDRESS = "street_address"  # Queries like "123 Main St"
    JUST_A_NUMBER = "just_a_number"    # Bare numbers like "1234" (likely stop IDs)
    STOP_REQUEST = "stop_request"      # Explicit stop queries like "stop 1234"
    INTERSECTION = "intersection"       # Queries like "Main & 1st"
    UNKNOWN = "unknown"                 # Unclassified queries


def remove_duplicate_features(
    features: list[dict[str, Any]], 
    query_type: Optional[EvaluatesAs] = None
) -> list[dict[str, Any]]:
    """Remove duplicate features from Pelias results using label normalization.
    
    Deduplication strategy:
    1. Normalize each feature's label (expand abbreviations, lowercase)
    2. Remove duplicate normalized labels (keeps last occurrence)
    3. Further deduplicate by removing all whitespace from labels
    
    Args:
        features: List of Pelias GeoJSON features
        query_type: Type of query (currently unused but reserved for future logic)
        
    Returns:
        list: Deduplicated features
        
    Note:
        - Keeps the LAST occurrence of each duplicate (dict insertion order)
        - May lose some features if normalization makes them identical
        - The query_type parameter is currently unused
        
    Examples:
        Features with labels "Main St" and "Main Street" would be considered
        duplicates after normalization.
    """
    # First pass: normalize addresses and deduplicate by normalized label
    # This creates a dict where keys are normalized addresses
    # If duplicates exist, the last one wins (dict insertion order)
    name_dict = {
        normalize_address(x["properties"]["label"].lower().strip()): x 
        for x in features 
        if "properties" in x and "label" in x["properties"]
    }
    
    # Second pass: remove all whitespace from keys for even more aggressive deduplication
    # This catches cases like "Main Street" vs "MainStreet"
    final_dict = {
        x.strip().lower().replace(" ", ""): v 
        for x, v in name_dict.items()
    }

    return list(final_dict.values())


def prioritize_addresses(
    features: list[dict[str, Any]], 
    query: str, 
    query_type: EvaluatesAs,
    service: Literal["autocomplete", "search", "reverse"] = "autocomplete"
) -> list[dict[str, Any]]:
    """Prioritize and filter address results based on query matching.
    
    For intersections: Filters to features containing both street names.
    For street addresses: Filters to features containing the query text.
    
    Args:
        features: List of Pelias GeoJSON features
        query: The original search query
        query_type: Classified query type (INTERSECTION or STREET_ADDRESS)
        service: Pelias service used ("autocomplete", "search", or "reverse")
        
    Returns:
        list: Filtered and optionally sorted features. If no matches found,
              returns all original features.
              
    Note:
        For search service, results are sorted by distance when multiple matches exist.
    """
    results = []
    query = query.lower().strip()
    
    # Handle intersection queries: both street names must appear in the label
    if query_type is EvaluatesAs.INTERSECTION:
        left, right = intersection_parts(query=query)
        logger.debug(f"intersection of: {left} / {right}")

        if left and right:
            logger.debug('FOUND LEFT AND RIGHT FOR INTERSECTION')
            # Normalize both query parts for better matching
            left_norm = normalize_address(left).lower().strip()
            right_norm = normalize_address(right).lower().strip()
            
            for feature in features:
                label = feature["properties"].get("label", "").lower()
                label_norm = normalize_address(label).lower().strip()
                
                # Both street names must be present in the label
                if left_norm in label_norm and right_norm in label_norm:
                    logger.debug(
                        f"found intersection match! label: {label_norm}, "
                        f"parts: {left_norm} / {right_norm}"
                    )
                    results.append(feature)
    
    # Handle street address queries: query text must appear in label
    elif query_type is EvaluatesAs.STREET_ADDRESS:
        query_lower = query.lower().strip()
        
        for feature in features:
            label = feature["properties"].get("label", "").lower().strip()
            
            # Simple substring match
            if query_lower in label:
                results.append(feature)
    
    # Fallback: if no matches found, return all original features
    if not results:
        results = features
    
    # For search service, sort filtered results by distance
    if service == "search" and len(results) > 1:
        results = order_by_distance(results)

    return results
