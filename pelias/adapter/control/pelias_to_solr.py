from ott.utils.dao.base import MinimalDao

TYPE_NAMES = {}
TYPE_NAMES["address"] = "Address"
TYPE_NAMES["stop"] = "Stop ID"


class SolrRecord(MinimalDao):
    """
    :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=
    """
