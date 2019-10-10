from pyramid.response import Response
from pyramid.view import view_config

from ott.utils.dao import base
from ott.utils import json_utils
from ott.utils import object_utils

from ott.utils.svr.pyramid import response_utils
from ott.utils.svr.pyramid import globals

from pelias.adapter.model.solr.solr_response import SolrResponse

from pelias.adapter.control.pelias_to_solr import PeliasToSolr
from pelias.adapter.control.pelias_wrapper import PeliasWrapper


import logging
log = logging.getLogger(__file__)


def do_view_config(cfg):
    # import pdb; pdb.set_trace()
    config_globals(cfg)

    cfg.add_route('pelias', '/pelias')
    cfg.add_route('pelias_proxy', '/proxy')
    cfg.add_route('pelias_services', '/pelias/{service}')

    cfg.add_route('solr', '/solr')
    cfg.add_route('solr_select', '/solr/select')
    cfg.add_route('solr_stops', '/solr/stops')
    cfg.add_route('solr_stops_select', '/solr/stops')
    cfg.add_route('solr_boundary', '/solr/boundry')
    cfg.add_route('solr_boundary_select', '/solr/boundary/select')


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


def call_pelias(request):
    query = request.params.get('q')
    if not query:
        query = request.params.get('text')
    solr_params = {}
    solr_params['q'] = query
    ret_val = PeliasToSolr.call_pelias(solr_params, pelias_autocomplete_url, pelias_search_url)
    return ret_val


def call_boundary(response, boundary="all"):
    """
    will call a boundary service to check if results are in/out of a given boundary(s)
    will update the response object with in/out status...
    """
    # TODO stepz below
    # step 1: look thru response objects
    # step 2: get lat,lon and call service
    # step 3: update record w/result
    pass


@view_config(route_name='solr_boundary', renderer='json', http_cache=globals.CACHE_LONG)
@view_config(route_name='solr_boundary_select', renderer='json', http_cache=globals.CACHE_LONG)
def solr_boundary(request):
    """
    This query has a good variety of hits for both in and out of ADA and DISTRICT
    http://localhost:45454/solr/boundary?q=8
    """


    ret_val = None
    try:
        ret_val = call_pelias(request)
        if ret_val and ret_val.response:
            call_boundary(ret_val.response)
        ret_val = response_utils.dao_response(ret_val)
    except Exception as e:
        log.warn(e)
        ret_val = response_utils.sys_err_response()
    return ret_val


@view_config(route_name='solr_stops', renderer='json', http_cache=globals.CACHE_LONG)
@view_config(route_name='solr_stops_select', renderer='json', http_cache=globals.CACHE_LONG)
def solr_stops(request):
    """
    STOP QUERY:
    replicate this SOLR interface:
       https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop (type%3Astop)
       8th and lambert

    todo: have to pull route stops from /data/ service, and append that to SOLR response
    """
    return "HI"


@view_config(route_name='solr', renderer='json', http_cache=globals.CACHE_LONG)
@view_config(route_name='solr_select', renderer='json', http_cache=globals.CACHE_LONG)
def solr_json(request):
    ret_val = None
    try:
        json = call_pelias(request)
        ret_val = response_utils.dao_response(json)
    except Exception as e:
        log.warn(e)
        ret_val = response_utils.sys_error_response()
    return ret_val


@view_config(route_name='pelias_services', renderer='json', http_cache=globals.CACHE_LONG)
def pelias_services(request):
    """

    :param request:
    :return:
    """
    #import pdb; pdb.set_trace()
    try:
        service = request.matchdict['service']
    except:
        service = "autocomplete"

    if service == "autocomplete":
        ret_val = PeliasWrapper.wrapp(pelias_autocomplete_url, pelias_search_url, pelias_reverse_url, request.query_string)
    elif service == "search":
        ret_val = PeliasWrapper.wrapp(pelias_search_url, pelias_autocomplete_url, pelias_reverse_url, request.query_string)
    elif service == "reverse":
        ret_val = response_utils.proxy_json(pelias_reverse_url, request.query_string)
    else:
        ret_val = response_utils.sys_err_response()
    return ret_val


@view_config(route_name='pelias', renderer='json', http_cache=globals.CACHE_LONG)
@view_config(route_name='pelias_proxy', renderer='json', http_cache=globals.CACHE_LONG)
def pelias(request):
    """ call pelias_ervices() above """
    return pelias_services(request)


