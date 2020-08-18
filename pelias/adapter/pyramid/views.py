from pyramid.view import view_config

from ott.utils import json_utils
from ott.utils.svr.pyramid import response_utils
from ott.utils.svr.pyramid import globals

from pelias.adapter.control.pelias_to_solr import PeliasToSolr
from pelias.adapter.control.pelias_wrapper import PeliasWrapper

import logging
log = logging.getLogger(__file__)


# urls
pelias_autocomplete_url = None
pelias_search_url = None
pelias_reverse_url = None


def config_globals(cfg):
    """ TODO: globals ???  something better? """
    global pelias_autocomplete_url
    global pelias_search_url
    global pelias_reverse_url

    pelias_autocomplete_url = cfg.registry.settings.get('pelias_autocomplete_url')
    pelias_search_url = cfg.registry.settings.get('pelias_search_url')
    pelias_reverse_url = cfg.registry.settings.get('pelias_reverse_url')


def do_view_config(cfg):
    # import pdb; pdb.set_trace()
    config_globals(cfg)

    cfg.add_route('pelias', '/pelias')
    cfg.add_route('pelias_proxy', '/proxy')
    cfg.add_route('pelias_services', '/pelias/{service}')
    cfg.add_route('solr', '/solr')
    cfg.add_route('solr_select', '/solr/select')


def call_pelias(request):
    query = request.params.get('q')
    if not query:
        query = request.params.get('text')
    solr_params = {}
    solr_params['q'] = query
    ret_val = PeliasToSolr.call_pelias(solr_params, pelias_autocomplete_url, pelias_search_url)
    return ret_val


@view_config(route_name='solr', renderer='json', http_cache=globals.CACHE_LONG)
@view_config(route_name='solr_select', renderer='json', http_cache=globals.CACHE_LONG)
def solr_json(request):
    ret_val = None
    try:
        json = call_pelias(request)
        ret_val = response_utils.dao_response(json)
    except Exception as e:
        log.warning(e)
        ret_val = response_utils.sys_error_response()
    return ret_val


@view_config(route_name='pelias_services', renderer='json', http_cache=globals.CACHE_LONG)
def pelias_services(request):
    """
    calls pellias wrapper based on specified service (autocomplete == default, search or reverse)
    :return: json data from Pelias ... after fixing up the response in ways defined by 'PeliasWrapper'
    """
    # import pdb; pdb.set_trace()

    # step 1: find the service based on pelias/{service}? ... default to autocomplete
    try:
        service = request.matchdict['service']
    except:
        service = "autocomplete"

    # step 2: call the wrapper
    if service == "autocomplete":
        ret_val = PeliasWrapper.wrapp(pelias_autocomplete_url, pelias_search_url, pelias_reverse_url, request.query_string)
    elif service == "search":
        ret_val = PeliasWrapper.wrapp(pelias_search_url, pelias_autocomplete_url, pelias_reverse_url, request.query_string)
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


@view_config(route_name='pelias', renderer='json', http_cache=globals.CACHE_LONG)
@view_config(route_name='pelias_proxy', renderer='json', http_cache=globals.CACHE_LONG)
def pelias(request):
    """ call pelias_services() above w/out specifying a service ... so will default to autocomplete """
    return pelias_services(request)
