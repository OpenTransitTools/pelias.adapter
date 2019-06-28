from .solr_record import SolrRecord

import logging
log = logging.getLogger(__file__)


class SolrStopRecord(SolrRecord):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop
    """

    def __init__(self):
        super(SolrStopRecord, self).__init__()

        self.agency_id = None  # "TRIMET" / "C-TRAN" / etc...
        self.stop_id = None  # "3720"
        self.street_direction = ""
        self.zone_id = 0
        self.amenities = None # "Crosswalk near stop;Curbcut;Front-door Landing Paved;Sidewalk;;Back-door Landing Paved"
        self.providers = None # "Transportation Reaching People (TRP);Friends of Estacada Community Center"
        self.routes = None # "30:30:Estacada:"
        self.route_stops = None # "30,\"Estacada\",0,\"To Estacada\",false,false,false",
        self.begin_date = "2018-01-31"
        self.end_date = "9999-12-31"

    def query_stop_information(self):
        """
        will grab detailed stop data from service, if needed...
        """
        stop_json = query_stop(self.stop_id)
        self.amenities = stop_json.get('amenities')
        self.providers = stop_json.get('')
        self.routes = stop_json.get('')
        self.route_stops = stop_json.get('')
        self.begin_date = stop_json.get('')
        self.end_date = stop_json.get('')

    def parse_pelias(self, json):
        super(SolrStopRecord, self).parse_pelias(json)
        try:
            properties = json.get('properties')

            # parse the id into parts <stop_code>::<agency_id>::<layer_id>
            id_parts = properties.get('id').split('::')
            self.stop_id = id_parts[0]
            self.agency_id = id_parts[1]
        except Exception as e:
            log.warn(e)
