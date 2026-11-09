import requests

from ott.utils.dao.base import MinimalDao
from ott.utils.dao.base import BaseDao

from .solr_record import SolrRecord
from .solr_stop_record import SolrStopRecord

from pelias.adapter.service import boundary

import logging
log = logging.getLogger(__file__)


class ResponseHeader(MinimalDao):
    def __init__(self):
        self.status = 0
        self.QTime = 2
        self.params = {}

    def parse_pelias(self, json):
        pass


class Response(MinimalDao):
    def __init__(self, geoserver_domain=None):
        self.numFound = 0
        self.start = 0
        self.maxScore = 0
        self.docs = []
        self.geoserver_domain = geoserver_domain

    def parse_pelias(self, json, do_boundary=True):
        #import pdb; pdb.set_trace()
        try:
            # step 1: get pelias records
            features = json.get('features', [])

            # step 2: loop thru pelias records
            for f in features:
                # step 3: handle parsing of different layer types
                layer = f.get('properties', {}).get('layer')
                if layer:
                    if ':stops' in layer:
                        solr_rec = SolrStopRecord.pelias_to_solr(f)
                    else:
                        solr_rec = SolrRecord.pelias_to_solr(f)

                    # step 4: if we get a good record, add it to the response
                    if solr_rec:
                        if do_boundary:
                            boundary.ada(solr_rec, self.geoserver_domain)
                            boundary.district(solr_rec, self.geoserver_domain)

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
        from pelias.adapter.pyramid.views import geoserver_domain
        super(SolrResponse, self).__init__()
        self.responseHeader = ResponseHeader()
        self.response = Response(geoserver_domain)

    def parse_pelias(self, json, solr_params=None):
        self.responseHeader.parse_pelias(json)
        self.fix_headers(solr_params)
        self.response.parse_pelias(json)

    def num_records(self):
        return len(self.response.docs)

    def fix_headers(self, solr_params):
        if solr_params:
            self.responseHeader.params.update(solr_params)
