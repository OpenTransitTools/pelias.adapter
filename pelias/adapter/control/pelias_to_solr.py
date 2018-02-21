from pelias.adapter.model.solr.solr_response import SolrResponse


class PeliasToSolr(object):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=
    """

    @classmethod
    def run(cls):
        ret_val = None
        ret_val = SolrResponse()
        return ret_val

    @classmethod
    def parse_json(cls, json):
        ret_val = None
        ret_val = SolrResponse()
        ret_val.parse_pelias(json)
        return ret_val
