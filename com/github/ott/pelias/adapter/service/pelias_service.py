from fastapi import Request
from ott.utils import json_utils

from com.github.ott.pelias.adapter.core.errors import PeliasAdapterError
from com.github.ott.pelias.adapter.service.config import (
    pelias_autocomplete_url,
    pelias_place_url,
    SearchApiType,
)
from com.github.ott.pelias.adapter.service.config import pelias_reverse_url
from com.github.ott.pelias.adapter.service.config import pelias_search_url
from com.github.ott.pelias.adapter.service.pelias_wrapper import PeliasWrapper


def get_pelias_response(
    request: Request, service: SearchApiType = SearchApiType.autocomplete, is_rtp=False
) -> dict:
    """
    calls pellias wrapper based on specified service (autocomplete == default, search or reverse)
    :return: json data from Pelias ... after fixing up the response in ways defined by 'PeliasWrapper'
    """
    # import pdb; pdb.set_trace()

    # step 1: find the service based on pelias/{service}? ... default to autocomplete

    query = request.url.query

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
                f"unknown pelias service requested: {service}, must be one of autocomplete, search or reverse")

    # step 3: append the hostname to the response
    json_utils.append_hostname_to_json(ret_val)

    """
    TODO: WIP find and add stops / in/out / etc...
    x = object_utils.find_elements('properties', ret_val)
    for z in x:
        z["XXXX"] = 'MMMMMMMMMMM'
    import pdb; pdb.set_trace()
    """

    return ret_val
