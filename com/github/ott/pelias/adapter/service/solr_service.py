from ott.utils import object_utils

from com.github.ott.pelias.adapter.models.solr.solr_response import SolrResponse
from com.github.ott.pelias.adapter.service.config import (
    pelias_autocomplete_url,
    pelias_search_url,
)
from com.github.ott.pelias.adapter.service.pelias_to_solr import PeliasToSolr


def solr_api(request, def_rows=10) -> SolrResponse:
    """will handle SOLR routers params, then call pelias"""
    solr_params = {}

    query_params = dict(request.query_params)

    solr_params["q"] = (
        query_params["q"] if "q" in query_params else query_params["text"]
    )

    rows = query_params["rows"] if "rows" in query_params else None
    solr_params["rows"] = object_utils.safe_int(rows, def_rows)

    fq = query_params.get("fq")
    if fq:
        solr_params["fq"] = fq

    wt = query_params.get("wt", "json")
    solr_params["wt"] = wt

    # step 2: wrap call to Pelias and get SOLR response
    ret_val = PeliasToSolr.call_pelias(
        solr_params, pelias_autocomplete_url, pelias_search_url
    )
    return ret_val
