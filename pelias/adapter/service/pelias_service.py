from logging import getLogger
from typing import Literal, Any

from ott.utils import json_utils
from ott.utils.svr.pyramid import response_utils
from pelias.adapter.control.pelias_wrapper import PeliasWrapper
from pyramid.request import Request
logger = getLogger(__name__)



def get_pelias_response(service:Literal["autocomplete", "search", "reverse"], request:Request, is_rtp:bool=False) -> dict[str, Any]:
    from pelias.adapter.pyramid.views import pelias_autocomplete_url, pelias_reverse_url, pelias_search_url
    logger.debug(f"query: {request.query_string} ")

    # step 2: call the wrapper
    if service == "autocomplete":
        ret_val = PeliasWrapper.wrapp(pelias_autocomplete_url, pelias_search_url, pelias_reverse_url, request.query_string, is_rtp=is_rtp)
    elif service == "search":
        ret_val = PeliasWrapper.wrapp(pelias_search_url, pelias_autocomplete_url, pelias_reverse_url, request.query_string, is_rtp=is_rtp)
    elif service == "reverse":
        ret_val = PeliasWrapper.reverse(pelias_reverse_url, request.query_string)
    else:
        ret_val = response_utils.sys_error_response()

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