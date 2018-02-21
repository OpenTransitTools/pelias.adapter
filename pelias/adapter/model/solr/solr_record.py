from ott.utils.dao.base import MinimalDao

import logging
log = logging.getLogger(__file__)


TYPE_NAMES = {}
TYPE_NAMES["address"] = "Address"
TYPE_NAMES["stop"] = "Stop ID"


class SolrRecord(MinimalDao):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=
    """

    def __init__(self):
        super(SolrRecord, self).__init__()
        self.id = "Address-1"
        self.type = "address"
        self.type_name = TYPE_NAMES[self.type]
        self.vtype = "1"
        self.name = None

        self.neighborhood = "Sellwood"
        self.city = "PORTLAND"
        self.county = "Multnomah"
        self.zip_code = "97202"

        self.ada_boundary = True
        self.trimet_boundary = True

        self.x = 7645053.5
        self.y = 684388.9
        self.lon = -122.67371
        self.lat = 45.523335

        self.timestamp = "2018-02-03T07:47:45.045Z"
        self.score = 1.11

    def parse_pelias(self, json):
        try:
            # import pdb; pdb.set_trace()

            # step 1: parse props
            properties = json.get('properties')

            # step 2: parse / calculate geometry
            geometry = json.get('geometry')
            x, y = self.parse_geojson(geometry)
            self.lon = x
            self.lat = y

        except Exception, e:
            log.warn(e)

    @classmethod
    def pelias_to_solr(cls, json):
        ret_val = None
        try:
            rec = cls()  # inheritance polymorphism constructor call
            rec.parse_pelias(json)
            ret_val = rec
        except Exception, e:
            log.warn(e)
        return ret_val
