

class SolrStopRecord(SolrRecord):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop
    """
    type_name = "Stop ID"
    type = "stop"

    begin_date = "2018-02-22"
    end_date = "9999-12-31"

    stop_id = None # "3720"
    street_direction = "S"
    zone_id = 0
    amenities = None # "Crosswalk near stop;Curbcut;Front-door Landing Paved;Sidewalk;;Back-door Landing Paved"
    providers = None # "Transportation Reaching People (TRP);Friends of Estacada Community Center"
    routes = None # "30:30:Estacada:"
    route_stops = None # "30,\"Estacada\",0,\"To Estacada\",false,false,false",
