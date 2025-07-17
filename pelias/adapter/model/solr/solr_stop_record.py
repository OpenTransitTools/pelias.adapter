from .solr_record import SolrRecord

import logging
log = logging.getLogger(__file__)


class SolrStopRecord(SolrRecord):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop
    """
    def __init__(self):
        super(SolrStopRecord, self).__init__()

    '''
    NOT USED in April 2021 ... broken no query_stop method
    def query_stop_information(self):
        """
        will grab detailed stop data from service, if needed...
        """

        """
        Route Stops:
        https://maps.trimet.org/ti/index/stops/4/routes/str

        Show In/Out of district on this page:
        https://trimet.org/taxinfo/#boundary
        https://maps.trimet.org/solr/select?_dc=1618955956672&start=0&limit=10&fq=(-type%3A26%20AND%20-type%3Aroute)&wt=json&qt=dismax&rows=10&q=44%20se
        """


        """
        need this ?   really?
        self.amenities = None  # "Crosswalk near stop;Curbcut;Front-door Landing Paved;Sidewalk;;Back-door Landing Paved"
        self.providers = None  # "Transportation Reaching People (TRP);Friends of Estacada Community Center"
        self.routes = None  # "30:30:Estacada:snow"
        self.route_stops = None  # "30,\"Estacada\",0,\"To Estacada\",false,false,false",
        """

        stop_json = query_stop(self.stop_id)
        self.amenities = stop_json.get('amenities')
        self.providers = stop_json.get('')
        self.routes = stop_json.get('')
        self.route_stops = stop_json.get('')
        self.begin_date = stop_json.get('')
        self.end_date = stop_json.get('')
    '''

    def parse_pelias(self, json):
        super(SolrStopRecord, self).parse_pelias(json)

        self.type_name = "Stop ID"
        self.begin_date = "2025-07-14"
        self.end_date = "9999-12-31"

        try:
            gtfs = json.get('properties').get('addendum').get('gtfs')
            self.agency_id = gtfs.get('agency_id', "")
            self.stop_id = gtfs.get('stop_id', "")
            self.stop_code = gtfs.get('stop_code', "")
            self.street_direction = gtfs.get('direction', "")
            self.position = gtfs.get('position', "")
            self.mode = gtfs.get('mode', "")
        except Exception as e:
            log.warning(e)
