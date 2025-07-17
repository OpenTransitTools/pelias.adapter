from ott.utils.dao.base import MinimalDao
from ott.utils import geo_utils

import logging
log = logging.getLogger(__file__)


"""
TODO: have an endpoint /solrwrap/boundary?text=834 SE that calculates the bounds

Show In/Out of district on this page:
https://trimet.org/taxinfo/#boundary
https://maps.trimet.org/solr/select?_dc=1618955956672&start=0&limit=10&fq=(-type%3A26%20AND%20-type%3Aroute)&wt=json&qt=dismax&rows=10&q=44%20se
"""

class SolrRecord(MinimalDao):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=
    """
    def __init__(self):
        super(SolrRecord, self).__init__()
        self.id = ""
        self.type = ""
        self.type_name = ""
        self.vtype = "1"
        self.name = ""

        self.city = ""
        self.county = ""
        self.neighborhood = ""
        self.zip_code = ""

        self.x = 7645053.5
        self.y = 684388.9
        self.lon = -122.67371
        self.lat = 45.523335

        self.timestamp = "2018-02-03T07:47:45.045Z"
        self.score = 0.0

    def set_value(self, name, val):
        pass

    def parse_pelias(self, json):
        try:
            # step 1: parse props
            properties = json.get('properties')
            self.id = properties.get('id')
            self.type = properties.get('layer')
            self.type_name = "Address"

            self.name = properties.get('name', "")
            self.city = properties.get('locality', "")
            self.neighborhood = properties.get('neighborhood', "")
            self.county = properties.get('county', "")
            self.score = properties.get('confidence', 0.1)

            # step 2: parse / calculate geometry
            geojson = json.get('geometry')
            lon, lat = self.parse_geojson(geojson)
            self.lon = lon
            self.lat = lat
            x, y = geo_utils.to_OSPN(lon, lat)
            self.x = x
            self.y = y

        except Exception as e:
            log.warning(e)

    @classmethod
    def pelias_to_solr(cls, json):
        # import pdb; pdb.set_trace()
        ret_val = None
        try:
            rec = cls()  # inheritance polymorphism constructor call
            rec.parse_pelias(json)
            ret_val = rec
        except Exception as e:
            log.warning(e)
        return ret_val
