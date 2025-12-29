import ast
import logging

from ott.utils import object_utils, json_utils
from ott.utils.svr.pyramid import globals
from ott.utils.svr.pyramid import response_utils
from pelias.adapter.control.pelias_to_solr import PeliasToSolr
from pelias.adapter.control.pelias_wrapper import PeliasWrapper
from pelias.adapter.service import refine_service, pelias_service
from pyramid.view import view_config

log = logging.getLogger(__file__)

# urls
pelias_autocomplete_url = None
pelias_search_url = None
pelias_reverse_url = None
route_stop_str_url = None


def config_globals(cfg):
    """
    :see: config/base.ini for configured url strings
    """
    #import pdb; pdb.set_trace()
    global pelias_autocomplete_url
    global pelias_search_url
    global pelias_reverse_url
    global route_stop_str_url

    PeliasWrapper.rtp_agencies = ast.literal_eval(cfg.registry.settings.get('agencies'))
    pelias_autocomplete_url = cfg.registry.settings.get('pelias_autocomplete_url')
    pelias_search_url = cfg.registry.settings.get('pelias_search_url')
    pelias_reverse_url = cfg.registry.settings.get('pelias_reverse_url')
    route_stop_str_url = cfg.registry.settings.get('route_stop_str_url')


def do_view_config(cfg):
    config_globals(cfg)
    cfg.add_route('pelias', '/pelias')
    cfg.add_route('pelias_proxy', '/proxy')
    cfg.add_route('pelias_services', '/pelias/{service}')
    cfg.add_route('pelias_rtp', '/pelias/rtp/{service}')
    cfg.add_route('solr', '/solr')
    cfg.add_route('solr_select', '/solr/{select}')
    cfg.add_route('pelias_refine', '/pelias/refine/{service}')


@view_config(route_name='solr', renderer='json', http_cache=globals.CACHE_LONG)
def solr_json(request):
    """
    SOLR response wrapper...

    SOLR Queries:
    https://trimet.org/solr/select?q=12&rows=6&wt=xml&fq=type%3Astop

    :param request:
    :return:
    """

    def solr_api(request, def_rows=10):
        """ will handle SOLR api params, then call pelias """
        solr_params = {}

        # step 1: SOLR params
        query = request.params.get('q')
        if not query:
            query = request.params.get('text')
        solr_params['q'] = query

        rows = request.params.get('rows')
        solr_params['rows'] = object_utils.safe_int(rows, def_rows)

        fq = request.params.get('fq')
        if fq:
            solr_params['fq'] = fq

        wt = request.params.get('wt', 'json')
        solr_params['wt'] = wt

        # step 2: wrap call to Pelias and get SOLR response
        ret_val = PeliasToSolr.call_pelias(solr_params, pelias_autocomplete_url, pelias_search_url)
        return ret_val

    ret_val = None

    try:
        json = solr_api(request)
        ret_val = response_utils.dao_response(json)
    except Exception as e:
        log.warning(e)
        ret_val = response_utils.sys_error_response()
    return ret_val


@view_config(route_name='solr_select', renderer='json', http_cache=globals.CACHE_LONG)
def solr_select(request):
    """ catches ../solr/select (or ../solr/search, ../solr/autocomplete, ../solr/etc...) paths """
    return solr_json(request)


@view_config(route_name='pelias_services', renderer='json', http_cache=globals.CACHE_LONG)
def pelias_services(request, is_rtp=False, refine=False):
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
    if refine:
        ret_val = refine_service.refine(request, service=service, is_rtp=is_rtp)
    elif service == "autocomplete":
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


@view_config(route_name='pelias', renderer='json', http_cache=globals.CACHE_LONG)
@view_config(route_name='pelias_proxy', renderer='json', http_cache=globals.CACHE_LONG)
def pelias(request):
    """ call pelias_services() above w/out specifying a service ... so will default to autocomplete """
    return pelias_services(request)


@view_config(route_name='pelias_refine', renderer='json', http_cache=globals.CACHE_LONG)
def pelias_refine(request):
    """ call pelias_services() above w/out specifying a service ... so will default to autocomplete """
    return pelias_services(request, refine=True)


@view_config(route_name='pelias_rtp', renderer='json', http_cache=globals.CACHE_LONG)
def pelias_rtp(request):
    return pelias_services(request, is_rtp=True)
