from urllib.parse import urlencode

from fastapi import Request
from ott.utils import json_utils
from starlette.datastructures import QueryParams

from com.github.ott.pelias.adapter.core.errors import PeliasAdapterError
from com.github.ott.pelias.adapter.service.config import (
    pelias_autocomplete_url,
    pelias_place_url,
    SearchApiType,
)
from com.github.ott.pelias.adapter.service.config import pelias_reverse_url
from com.github.ott.pelias.adapter.service.config import pelias_search_url
from com.github.ott.pelias.adapter.service.pelias_wrapper import PeliasWrapper
from com.github.ott.pelias.adapter.service.util import (
    get_query_type,
    QueryType,
    normalize_address,
    remove_non_digits,
)

TRANSIT_LAYERS = (
    "trimet:stops,ctran:stops,sam:stops,smart:stops,mult:stops,wapark:stops"
)


def _get_pelias_response(
    request: Request, service: SearchApiType = SearchApiType.autocomplete, is_rtp=False
) -> dict:
    """
    calls pellias wrapper based on specified service (autocomplete == default, search or reverse)
    :return: json data from Pelias ... after fixing up the response in ways defined by 'PeliasWrapper'
    """
    # import pdb; pdb.set_trace()

    # step 1: find the service based on pelias/{service}? ... default to autocomplete

    query = request.url.query
    ret_val = {}

    match service:
        case SearchApiType.autocomplete:
            ret_val = PeliasWrapper.wrapp(
                pelias_autocomplete_url,
                pelias_search_url,
                pelias_reverse_url,
                query,
                is_rtp=is_rtp,
            )
        case SearchApiType.search:
            ret_val = PeliasWrapper.wrapp(
                pelias_search_url,
                pelias_autocomplete_url,
                pelias_reverse_url,
                query,
                is_rtp=is_rtp,
            )
        case SearchApiType.reverse:
            ret_val = PeliasWrapper.reverse(pelias_reverse_url, query)
        case SearchApiType.place:
            ret_val = PeliasWrapper.reverse(pelias_place_url, query)
        case _:
            raise PeliasAdapterError(
                f"unknown pelias service requested: {service}, must be one of autocomplete, search or reverse"
            )

    # step 3: append the hostname to the response
    json_utils.append_hostname_to_json(ret_val)

    # step 4: remove duplicate features if any
    features = ret_val.get("features", [])
    if features and len(features) > 0:
        revised_features = remove_duplicate_features(ret_val.get("features", []))
        ret_val["features"] = revised_features

    """
    TODO: WIP find and add stops / in/out / etc...
    x = object_utils.find_elements('properties', ret_val)
    for z in x:
        z["XXXX"] = 'MMMMMMMMMMM'
    import pdb; pdb.set_trace()
    """

    return ret_val


def remove_duplicate_features(features):
    """
    Best shot at normalizing and removing duplicate features from pelias response
    """
    refined = {
        f["properties"]["name"].strip().lower(): f
        for f in features
        if isinstance(f, dict)
        and "properties" in f
        and isinstance(f["properties"], dict)
        and "name" in f["properties"]
        and isinstance(f["properties"]["name"], str)
    }
    normalized_addresses = {normalize_address(key): v for key, v in refined.items()}

    return list(normalized_addresses.values())


def get_best_match(ret_val, text: str, is_stop_request=False):
    """
    from a pelias response, find the best match (first in list) and return it
    :param ret_val: pelias response json
    :param text: original query text
    :param is_stop_request: whether this is a stop request
    :return: first match from pelias response
    """
    features = ret_val.get("features", [])
    if not features or len(features) == 1:
        return ret_val
    else:
        features = remove_duplicate_features(features)
        if is_stop_request:
            # for stop requests, we expect exactly one match
            stop_id = remove_non_digits(text)
            if stop_id:
                matches = [
                    feat
                    for feat in features
                    if isinstance(feat.get("id"), str)
                    and feat["id"].endswith(f":{stop_id}")
                ]
                ret_val["features"] = matches
        else:
            matches = [
                f
                for f in features
                if text == f.get("properties", {}).get("name", "").lower().strip()
            ]
            if not matches:
                matches = [
                    f
                    for f in features
                    if text in f.get("properties", {}).get("name", "").lower().strip()
                ]
            if matches:
                ret_val["features"] = matches
    return ret_val


def adjust_layers_for_query(query_type, query_params) -> tuple[bool, dict]:
    if query_type in (QueryType.STOP_REQUEST, QueryType.JUST_A_NUMBER):
        query_params["layers"] = TRANSIT_LAYERS
        return True, query_params
    elif query_type is QueryType.STREET_ADDRESS:
        query_params["layers"] = "address"
    return False, query_params


def refactor_pelias_request(request: Request, new_params: dict) -> Request:
    """update both request._query_params and the ASGI scope query_string,
    and clear cached URL so request.url reflects the new params
    """
    request._query_params = QueryParams(**new_params)
    request.scope["query_string"] = urlencode(new_params, doseq=True).encode()
    if hasattr(request, "_url"):
        # noinspection PyProtectedMember
        del request._url
    return request


def get_pelias_response(
    request: Request,
    service: SearchApiType = SearchApiType.autocomplete,
    is_rtp: bool = False,
    refine: bool = False,
):
    """
    Get a response from Pelias, with optional refinement

    if refine is true, the method will try to get a better match (maybe a single match)
    for stop requests or single result requests

    However, if the request is truly ambiguous (for example text="big"), the method will probably return a number of results...
    Unless there is an item whose exact name matches the ambiguous value

    """

    if not refine:
        return _get_pelias_response(request=request, service=service, is_rtp=is_rtp)
    else:
        """
        Do some data normalization here to eliminate duplicates and normalize addresses.
        Try to get to a single result.
        If query was ambiguous and we still end up with more than one result, return the first IF the query's size = 1

        """

        new_params = dict(request.query_params)
        original_params = new_params.copy()

        size, text = (
            int(new_params.get("size", 10)),
            (new_params.get("text") or "").lower().strip(),
        )
        query_type, stop_id = get_query_type(text)

        # pelias will just return first, so we'll get 10 and try to get a better first
        if size == 1:
            new_params["size"] = "10"

        # determine if this is a stop request and apply reset layers to STOPS_LAYERS
        # or if determined an address "address", for request
        is_stop_request, new_params = adjust_layers_for_query(query_type, new_params)

        # required to ensure new params and layers stick
        request = refactor_pelias_request(request=request, new_params=new_params)

        ret_val = _get_pelias_response(service=service, request=request, is_rtp=is_rtp)

        _features = ret_val.get("features", [])

        # after the first request, we'll use feature.property.name to normalize
        # and remove dupes
        features = (
            remove_duplicate_features(_features)
            if _features and len(_features) > 1
            else _features
        )

        # if the custom layers query resulted in none, try again without the layers filter
        if (
            query_type
            in (
                QueryType.STOP_REQUEST,
                QueryType.JUST_A_NUMBER,
                QueryType.STREET_ADDRESS,
            )
            and not features
        ):
            # restore original params in scope and cached attrs
            request = refactor_pelias_request(request, original_params)

            ret_val = _get_pelias_response(
                service=service, request=request, is_rtp=is_rtp
            )
            features = ret_val.get("features", [])

        if len(features) > 1:
            ret_val = get_best_match(
                ret_val, text=text, is_stop_request=is_stop_request
            )
            if size == 1:
                # if size=1, give them 1
                features = ret_val.get("features", [])
                if len(features) > 1:
                    ret_val["features"] = features[0:1]
        else:
            ret_val["features"] = features

        # restore original params before returning
        refactor_pelias_request(request, original_params)

        return ret_val
