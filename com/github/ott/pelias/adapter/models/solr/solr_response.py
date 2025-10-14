import logging

import requests
from ott.utils.dao.base import BaseDao
from ott.utils.dao.base import MinimalDao

from .solr_record import SolrRecord
from .solr_stop_record import SolrStopRecord

log = logging.getLogger(__file__)


class RouteStopRecords(object):
    cache = {}
    _url = None

    @classmethod
    def url(cls):
        """get route stops as string"""
        if cls._url is None:
            from com.github.ott.pelias.adapter.routers.pelias import route_stop_str_url

            if route_stop_str_url and len(route_stop_str_url) > 5:
                cls._url = route_stop_str_url
            else:
                cls._url = "http://maps.trimet.org/ti/index/stops"
        return cls._url

    @classmethod
    def find_record(cls, id):
        """see requests_cache: https://requests-cache.readthedocs.io/en/latest/user_guide.html"""
        ret_val = None
        try:
            ret_val = cls.cache.get(id)
            if ret_val is None:
                # step 1: query route stop service
                rs = requests.get("{}/{}/routes/str".format(cls.url(), id))

                # step 2: cache record
                if rs and len(rs.text):
                    # cls.cache.update()
                    ret_val = rs.text
        except Exception as e:
            log.warning(e)
        return ret_val


class ResponseHeader(MinimalDao):
    def __init__(self):
        self.status = 0
        self.QTime = 2
        self.params = {}

    def parse_pelias(self, json):
        pass


class Response(MinimalDao):
    def __init__(self):
        self.numFound = 0
        self.start = 0
        self.maxScore = 0
        self.docs = []

    def parse_pelias(self, json, add_routes=False):
        # import pdb; pdb.set_trace()
        try:
            # step 1: get pelias records
            features = json.get("features", [])

            # step 2: loop thru pelias records
            for f in features:
                # step 3: handle parsing of different layer types
                layer = f.get("properties", {}).get("layer")
                if layer:
                    if "stops" in layer:
                        solr_rec = SolrStopRecord.pelias_to_solr(f)
                        """
                        if add_routes and hasattr(solr_rec, 'stop_id'):
                            rs = RouteStopRecords.find_record(solr_rec.stop_id)
                            solr_rec.routes = rs
                            pass
                        """
                    else:
                        solr_rec = SolrRecord.pelias_to_solr(f)

                    # step 4: if we get a good record, add it to the response
                    if solr_rec:
                        self.docs.append(solr_rec)
                        self.numFound += 1
        except Exception as e:
            log.warning(e)


class SolrResponse(BaseDao):
    """
    :see:
      https://trimet.org/solr/select?q=4&rows=6&wt=json&fq=type%3Astop
      routes": "37:37:Lake Grove:;78:78:Denney/Kerr Pkwy:snow",
    """

    def __init__(self):
        super(SolrResponse, self).__init__()
        self.responseHeader = ResponseHeader()
        self.response = Response()

    def parse_pelias(self, json, solr_params=None):
        self.responseHeader.parse_pelias(json)
        self.fix_headers(solr_params)

        add_routes = True  # object_utils.safe_get('')
        self.response.parse_pelias(json, add_routes)

    def num_records(self):
        return len(self.response.docs)

    def fix_headers(self, solr_params):
        if solr_params:
            self.responseHeader.params.update(solr_params)
