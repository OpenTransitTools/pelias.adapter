import requests

from ott.utils.dao.base import MinimalDao
from ott.utils.dao.base import BaseDao

from .solr_record import SolrRecord
from .solr_stop_record import SolrStopRecord

import logging
log = logging.getLogger(__file__)


class RouteStopRecords(object):
    cache = {}

    @classmethod
    def find_record(cls, id):
        ret_val = cls.cache.get(id)
        if ret_val is None:
            # step 1: query route stop service
            rs = requests.get("http://maps8.trimet.org/ti/index/stops/{}/routes/str".format(id))

            # step 2: cache record
            if rs and len(rs.text):
                #cls.cache.update()
                ret_val = rs.text
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

    def parse_pelias(self, json, add_route_stops=False):
        # import pdb; pdb.set_trace()
        try:
            # step 1: get pelias records
            features = json.get('features', [])

            # step 2: loop thru pelias records
            for f in features:
                # step 3: handle parsing of different layer types
                layer = f.get('properties', {}).get('layer')
                if layer:
                    if layer == 'stops':
                        solr_rec = SolrStopRecord.pelias_to_solr(f)
                        if add_route_stops and hasattr(solr_rec, 'stop_id'):
                            rs = RouteStopRecords.find_record(solr_rec.stop_id)
                            solr_rec.route_stops = rs
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
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=
    """
    def __init__(self):
        super(SolrResponse, self).__init__()
        self.responseHeader = ResponseHeader()
        self.response = Response()

    def parse_pelias(self, json, solr_params=None):
        self.responseHeader.parse_pelias(json)
        self.fix_headers(solr_params)

        add_route_stops = True  # object_utils.safe_get('')
        self.response.parse_pelias(json, add_route_stops)

    def num_records(self):
        return len(self.response.docs)

    def fix_headers(self, solr_params):
        if solr_params:
            self.responseHeader.params.update(solr_params)