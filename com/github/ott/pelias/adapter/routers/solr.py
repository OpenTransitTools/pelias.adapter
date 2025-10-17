import logging

from fastapi import APIRouter, Request, Depends

from com.github.ott.pelias.adapter.models.solr.solr_response import SolrResponse
from com.github.ott.pelias.adapter.schema.solr_schema import SolrResponseSchema
from com.github.ott.pelias.adapter.service.solr_service import solr_api

log = logging.getLogger(__file__)

router = APIRouter()


@router.get("/")
def solr_json(request: Request) -> SolrResponseSchema:
    """
    SOLR response wrapper...

    SOLR Queries:
    https://trimet.org/solr/select?q=12&rows=6&wt=xml&fq=type%3Astop

    :param request:
    :return:
    """

    solr_response: SolrResponse = solr_api(request)
    response: SolrResponseSchema = SolrResponseSchema.to_schema(solr_response)

    return response


# todo Original api does have autocomlete, etc on endpoint but it is
# ignored. No autocomplete on solr so removing for now
@router.get("/select")
def solr_select(
    request: Request,
):
    return solr_json(request=request)
