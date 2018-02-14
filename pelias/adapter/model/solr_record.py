
TYPE_NAMES = []
TYPE_NAMES["address"] = "Address"
TYPE_NAMES["stop"] = "Stop ID"


class SolrRecord(object):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=
    """
    id = "Address-1"
    type = "address"
    type_name = "Address"
    vtype = "1"
    name = None

    neighborhood = "Sellwood"
    city = "PORTLAND"
    county = "Multnomah"
    zip_code = "97202"

    ada_boundary = True
    trimet_boundary = True

    x = 7645053.5
    y = 684388.9
    lon = -122.67371,
    lat = 45.523335,

    timestamp = "2018-02-03T07:47:45.045Z"
    score = 1.11

