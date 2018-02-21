from ott.utils.dao.base import MinimalDao
from ott.utils.dao.base import BaseDao

from .solr_record import SolrRecord
from .solr_stop_record import SolrStopRecord

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
        self.docs = None

    def parse_pelias(self, json):
        self.docs = [
                SolrRecord(),
                SolrStopRecord(),
                SolrRecord(),
                SolrStopRecord()
            ]


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
