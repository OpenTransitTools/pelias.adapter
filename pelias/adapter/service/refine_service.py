from logging import getLogger
from typing import Literal, Any

from pyramid.encode import urlencode
from pyramid.interfaces import IMultiDict, IRequest
from pyramid.request import Request

from pelias.adapter.service import pelias_service
from pelias.adapter.service.util import is_address, remove_non_digits, prioritize_stops, \
    is_intersection, remove_duplicate_features, prioritize_addresses, EvaluatesAs

logger = getLogger(__name__)

TRANSIT_LAYERS = (
    "trimet:stops,ctran:stops,sam:stops,smart:stops,mult:stops,wapark:stops,ctran_flex:stops"
)

DEFAULT_SIZE = 10


def get_response_and_features(request: Request,
                              service: Literal["autocomplete", "search", "reverse"] = "autocomplete",
                              is_rtp: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ret_val = pelias_service.get_pelias_response(service=service, request=request, is_rtp=is_rtp)
    _features = ret_val.get("features", [])
    return ret_val, _features


def adjust_layers_for_query(query_type: EvaluatesAs, query_params: dict) -> tuple[bool, dict]:
    """Adjust Pelias query layers based on the detected query type.
    
    Args:
        query_type: The evaluated type of the query (from EvaluatesAs enum)
        query_params: Dictionary of query parameters to modify
        
    Returns:
        tuple[bool, dict]: A tuple containing:
            - bool: True if this is a stop request, False otherwise
            - dict: Modified query parameters with appropriate layers set
            
    Notes:
        - STOP_REQUEST: Sets layers to all transit stop layers
        - STREET_ADDRESS: Sets layers to 'address'
        - INTERSECTION: Sets layers to 'intersection'
        - JUST_A_NUMBER: Returns early without modifying layers
    """
    if query_type is EvaluatesAs.STOP_REQUEST:
        query_params["layers"] = TRANSIT_LAYERS
        return True, query_params
    elif query_type is EvaluatesAs.STREET_ADDRESS:
        query_params["layers"] = "address"
    elif query_type is EvaluatesAs.JUST_A_NUMBER:
        return False, query_params
    elif query_type is EvaluatesAs.INTERSECTION:
        query_params["layers"] = "intersection"
    return False, query_params


def get_query_type(query: str) -> tuple[EvaluatesAs, int]:
    """Analyze a query string and determine its type.
    
    Args:
        query: The raw query string to analyze
        
    Returns:
        tuple[EvaluatesAs, int]: A tuple containing:
            - EvaluatesAs: The evaluated query type (STOP_REQUEST, STREET_ADDRESS, 
              INTERSECTION, JUST_A_NUMBER, or UNKNOWN)
            - int: The extracted stop_id if query is a number or stop request, 
              otherwise -1
              
    Examples:
        >>> get_query_type("stop 1234")
        (EvaluatesAs.STOP_REQUEST, 1234)
        >>> get_query_type("123 Main St")
        (EvaluatesAs.STREET_ADDRESS, -1)
        >>> get_query_type("5678")
        (EvaluatesAs.JUST_A_NUMBER, 5678)
    """
    query = query.lower().strip()
    stop_id = -1
    query_type = EvaluatesAs.UNKNOWN
    try:
        stop_id = int(query)
        query_type = EvaluatesAs.JUST_A_NUMBER
    except ValueError:
        # If parsing fails, stop_id remains -1, indicating the query is not a number.
        pass
    if query and query.startswith(("stop", "stopid", "stop_id", "stop id")) and query[-1].isdigit():
        query_type = EvaluatesAs.STOP_REQUEST
        stop_id = remove_non_digits(text=query, to_int=True)
    elif query_type is EvaluatesAs.UNKNOWN and is_intersection(query)[0]:
        query_type = EvaluatesAs.INTERSECTION
    elif is_address(query):
        query_type = EvaluatesAs.STREET_ADDRESS
    return query_type, stop_id


def refactor_pelias_request(request: Request, new_params: dict) -> Request:
    """Update Pyramid request object with new query parameters.
    
    Updates the request's query string, clears cached properties, and ensures
    the request reflects the new parameters for downstream processing.
    
    Args:
        request: The Pyramid Request object to modify
        new_params: Dictionary of new query parameters to apply
        
    Returns:
        Request: The modified request object with updated query parameters
        
    Notes:
        - Updates QUERY_STRING in request.environ
        - Clears cached _query_params, _url, and _GET properties
        - This ensures request.url and request.GET reflect the new parameters
    """

    request.environ["QUERY_STRING"] = urlencode(new_params, doseq=True)

    if hasattr(request, "_query_params"):
        del request._query_params

    if hasattr(request, "_url"):
        # noinspection PyProtectedMember
        del request._url

    request._GET = None

    return request


def refine(request: Request | IRequest,
           service: Literal["autocomplete", "search", "reverse"] = "autocomplete",
           is_rtp: bool = False) -> dict[str, Any]:
    """Refine and enhance Pelias geocoding results based on query analysis.
    
    This function analyzes the query, adjusts Pelias parameters for better results,
    removes duplicates, and prioritizes relevant features based on query type.
    
    Args:
        request: Pyramid Request object containing query parameters
        service: Pelias service endpoint to use ("autocomplete", "search", or "reverse")
        is_rtp: If True, disables TriMet-specific prioritization for RTP requests
        
    Returns:
        dict[str, Any]: Pelias GeoJSON response with refined and prioritized features
        
    Process:
        1. Analyzes query to determine type (stop, address, intersection, number)
        2. Adjusts Pelias layers parameter based on query type
        3. Fetches results from Pelias service
        4. Removes duplicate features
        5. Prioritizes results (stops or addresses) based on query type
        6. Limits results to originally requested size
        7. Restores original request parameters
        
    Notes:
        - Temporarily increases size to 10 if original request was smaller
        - If refined query returns no results, retries without refinement
        - Stop requests prioritize matching stop_id/stop_code
        - Address/intersection queries prioritize best matches
    """

    original_params: IMultiDict = request.GET

    new_params: IMultiDict = request.GET.copy()

    original_size = size = int(new_params.get("size", DEFAULT_SIZE))

    text: str = (new_params.get("text") or "").lower().strip()

    if not text:
        raise ValueError("Refine service requires 'text' query parameter")

    query_type, stop_id = get_query_type(text)

    logger.debug(f"determined query_type: {query_type.value} for query: {text}")

    # pelias will just return first, so we'll get 10 and try to get a better first
    if size < DEFAULT_SIZE:
        new_params["size"] = str(DEFAULT_SIZE)

    is_stop_request, new_params = adjust_layers_for_query(query_type, new_params)

    # if layers have been adjusted, we need to update the request object
    if query_type is EvaluatesAs.STREET_ADDRESS or is_stop_request or query_type is EvaluatesAs.INTERSECTION:
        request = refactor_pelias_request(request=request, new_params=new_params)

    ret_val, _features = get_response_and_features(service=service, request=request, is_rtp=is_rtp)

    # after the first request, we'll use feature.property.name to normalize
    # and remove dupes
    if _features and len(_features) >1:
        features = remove_duplicate_features(_features, query_type)
    else:
        features = _features
    # if the custom layers query resulted in none, try again without the layers filter

    if not features:
        # no features returned WITH refinement, let's try again WITHOUT refinement

        request = refactor_pelias_request(request, original_params)

        ret_val, _features = get_response_and_features(service=service, request=request, is_rtp=is_rtp)

        features = remove_duplicate_features(_features, query_type)

        ret_val["features"] = features

    if len(features) > 1 and (query_type is EvaluatesAs.JUST_A_NUMBER or is_stop_request):
        # sort and return
        features = prioritize_stops(features=features, is_rtp=is_rtp, stop_id=stop_id, service=service, text=text)

    elif len(features) > 1 and (query_type is EvaluatesAs.STREET_ADDRESS or query_type is EvaluatesAs.INTERSECTION):
        features = prioritize_addresses(features=features, query=text, query_type=query_type, service=service)

    if len(features) > original_size:
        ret_val["features"] = features[:original_size]
    else:
        ret_val["features"] = features

    # restore original params before returning
    refactor_pelias_request(request, original_params)

    return ret_val
