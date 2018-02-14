from pyramid.response import Response
from pyramid.view import view_config

from ott.utils.parse import StopParamParser
from ott.utils.parse import GeoParamParser
from ott.utils.parse import RouteParamParser

from ott.utils.dao import base
from ott.utils import json_utils
from ott.utils import object_utils

#from ott.geocoder.geosolr import GeoSolr
#from ott.geocoder.geo_dao import GeoListDao

import logging
log = logging.getLogger(__file__)


cache_long = 500
system_err_msg = base.ServerError()


def do_view_config(cfg):
    cfg.add_route('solr_stops', '/solr/stops')
    cfg.add_route('solr_json',  '/solr/select')
    cfg.add_route('solr_xml',   '/solr/xml')
    cfg.add_route('solr_txt',   '/solr/txt')


@view_config(route_name='solr_txt', renderer='string', http_cache=cache_long)
def solr_txt(request):
    return "HI"


@view_config(route_name='solr_stops', renderer='json', http_cache=cache_long)
def solr_stops(request):
    """
    STOP QUERY:
    replicate this SOLR interface: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type%3Astop (type:stop)
    8th and lambert
    """
    return "HI"


@view_config(route_name='solr_json', renderer='json')
def solr_json(request):
    # import pdb; pdb.set_trace()
    ret_val = None
    try:
        d = k
        pass
    except Exception, e:
        log.warn(e)
        ret_val = system_err_msg
    finally:
        pass
    return dao_response(ret_val)


@view_config(route_name='solr_xml', renderer='json', http_cache=cache_long)
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


SOLR = None
def get_solr():
    global SOLR
    if SOLR is None:
        SOLR = GeoSolr(CONFIG.get('solr_url'))
    return SOLR

