from ott.utils.dao.base import MinimalDao
from ott.utils.dao.base import BaseDao

from .solr_record import SolrRecord
from .solr_stop_record import SolrStopRecord

import logging
log = logging.getLogger(__file__)


class ResponseHeader(MinimalDao):
    def __init__(self):
        self.status = 0
        self.QTime = 2
        self.params = {
           'q': "3",
           'wt': "json",
           'fq': "type:stop",
           'rows': "6"
        }

    def parse_pelias(self, json):
        pass


class Response(MinimalDao):
    def __init__(self):
        self.numFound = 0
        self.start = 0
        self.maxScore = 0
        self.docs = []

    def parse_pelias(self, json):
        self.parse_features(json)

    def parse_features(self, json):
        try:
            # step 1: get pelias records
            features = json.get('features', [])

            # step 2: loop thru pelias records
            for f in features:
                # import pdb; pdb.set_trace()

                # step 3: handle parsing of different layer types
                layer = f.get('properties', {}).get('layer')
                if layer:
                    if layer == 'stops':
                        solr_rec = SolrStopRecord.pelias_to_solr(f)
                    else:
                        solr_rec = SolrRecord.pelias_to_solr(f)

                    # step 4: if we get a good record, add it to the response
                    if solr_rec:
                        self.docs.append(solr_rec)
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

    def parse_pelias(self, json):
        self.responseHeader.parse_pelias(json)
        self.response.parse_pelias(json)

    def num_records(self):
        return len(self.response.docs)
