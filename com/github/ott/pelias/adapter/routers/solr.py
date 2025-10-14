import logging

from fastapi import APIRouter, Request, Depends

from com.github.ott.pelias.adapter.models.solr.solr_response import SolrResponse
from com.github.ott.pelias.adapter.schema.solr_schema import (
    SolrQueryModel,
    SolrResponseSchema,
)
from com.github.ott.pelias.adapter.service.config import SolrApiType
from com.github.ott.pelias.adapter.service.solr_service import solr_api

log = logging.getLogger(__file__)

router = APIRouter()


@router.get("/")
def solr_json(
    request: Request, params: SolrQueryModel = Depends()
) -> SolrResponseSchema:
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


@router.get("/{api}")
def solr_select(
    request: Request,
    api: SolrApiType = SolrApiType.select,
    params: SolrQueryModel = Depends(),
):
    log.info(f"solr_select api={api}")
    # todo do we need to apply the api type? it's not being handled in solr_api() yet...
    return solr_json(request=request)
