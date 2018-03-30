from pyramid.response import Response
from pyramid.view import view_config

from ott.utils.dao import base
from ott.utils import json_utils
from ott.utils import object_utils

from pelias.adapter.model.solr.solr_response import SolrResponse
from pelias.adapter.control.pelias_to_solr import PeliasToSolr

from ott.boundary.pyramid import views as boundary_views

import logging
log = logging.getLogger(__file__)


cache_long = 500
system_err_msg = base.ServerError()


def do_view_config(cfg):
    # import pdb; pdb.set_trace()
    config_globals(cfg)
    cfg.add_route('solr', '/solr')
    cfg.add_route('solrselect', '/solr/select')
    cfg.add_route('solr_json', '/solr_json')
    cfg.add_route('solr_txt', '/solr_txt')
    cfg.add_route('solrtxt', '/solr/txt')
    cfg.add_route('solr_xml', '/solr/xml')
    cfg.add_route('solrxml', '/solr/xml')
    cfg.add_route('solr_stops', '/solr_stops')
    cfg.add_route('solrstops', '/solr/stops')
    cfg.add_route('pelias_proxy', '/proxy')


pelias_autocomplete_url = None
pelias_search_url = None
def config_globals(cfg):
    global pelias_autocomplete_url
    global pelias_search_url
    pelias_autocomplete_url = cfg.registry.settings.get('pelias_autocomplete_url')
    pelias_search_url = cfg.registry.settings.get('pelias_search_url')
    #make_boundaries_global(cfg)


@view_config(route_name='solrtxt', renderer='string', http_cache=cache_long)
@view_config(route_name='solr_txt', renderer='string', http_cache=cache_long)
def solr_txt(request):
    return boundary_views.distance_txt(request)


@view_config(route_name='solrstops', renderer='json', http_cache=cache_long)
@view_config(route_name='solr_stops', renderer='json', http_cache=cache_long)
def solr_stops(request):
    """
    STOP QUERY:
    replicate this SOLR interface:
       https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop (type%3Astop)
       8th and lambert

    todo: have to pull route stops from /data/ service, and append that to SOLR response
    """
    return "HI"


@view_config(route_name='solr', renderer='json')
@view_config(route_name='solrselect', renderer='json')
@view_config(route_name='solr_json', renderer='json')
def solr_json(request):
    ret_val = None
    try:
        solr_params = {}
        solr_params['q'] = request.params.get('q')
        ret_val = PeliasToSolr.call_pelias(solr_params, pelias_autocomplete_url, pelias_search_url)
    except Exception, e:
        log.warn(e)
        ret_val = system_err_msg
    finally:
        pass
    return dao_response(ret_val)


@view_config(route_name='solr_xml', renderer='json', http_cache=cache_long)
@view_config(route_name='solrxml', renderer='json', http_cache=cache_long)
def solr_xml(request):
    ret_val = None
    try:
        place = request.params.get('place')
        rows = request.params.get('rows')
        s = get_solr().solr(place, rows)
        ret_val = s
    except Exception, e:
        log.warn(e)
        ret_val = dao_response(system_err_msg)
    finally:
        pass
    return ret_val


@view_config(route_name='pelias_proxy', renderer='json', http_cache=cache_long)
def pelias_proxy(request):
    ret_val = proxy_json(pelias_autocomplete_url, request.query_string)
    return ret_val


def url_response(host, service, id, agency_id=None, extra="&detailed"):
    ''' return a url with id and other good stuff
    '''
    url = "http://{}/{}?id={}"
    if agency_id:
        url = url + "&agency_id={}".format(agency_id)
    if extra:
        url = url + extra
    ret_val = url.format(host, service, id)
    return ret_val


def dao_response(dao):
    ''' using a BaseDao object, send the data to a pyramid Reponse '''
    if dao is None:
        dao = data_not_found
    return json_response(json_data=dao.to_json(), status=dao.status_code)


def json_response(json_data, mime='application/json', status=200):
    ''' @return Response() with content_type of 'application/json' '''
    if json_data is None:
        json_data = data_not_found.to_json()
    return Response(json_data, content_type=mime, status_int=status)


def json_response_list(lst, mime='application/json', status=200):
    ''' @return Response() with content_type of 'application/json' '''
    json_data = []
    for l in lst:
        if l:
            jd = l.to_json()
            json_data.append(jd)
    return json_response(json_data, mime, status)


def proxy_json(url, query_string):
    ''' will call a json url and send back response / error string...
    '''
    ret_val = None
    try:
        ret_val = json_utils.stream_json(url, query_string)
    except Exception, e:
        log.warn(e)
        ret_val = system_err_msg.status_message
    finally:
        pass

    return ret_val
