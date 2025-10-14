from typing import Optional, Any, Dict, List

from pydantic import BaseModel, Field

from com.github.ott.pelias.adapter.models.solr.solr_response import (
    Response as SResponse,
)
from com.github.ott.pelias.adapter.models.solr.solr_response import SolrResponse
from com.github.ott.pelias.adapter.models.solr.solr_stop_record import SolrStopRecord


class SolrQueryModel(BaseModel):
    q: str  # query
    rows: Optional[int] = 6
    fq: Optional[str] = None
    stop: Optional[str] = None


class SolrParams(BaseModel):
    q: Optional[str] = None
    fl: Optional[str] = None
    rows: Optional[int] = None
    wt: Optional[str] = None
    start: Optional[str] = None
    sort: Optional[str] = None
    fq: Optional[List[str]] = None  # filter queries can be multiple


class SolrResponseHeader(BaseModel):
    status: int
    QTime: int
    params: Optional[SolrParams] = None

    @staticmethod
    def to_schema(header_dict: Dict[str, Any]) -> "SolrResponseHeader":
        params = header_dict.get("params", {})
        solr_params = SolrParams(**params) if params else None
        return SolrResponseHeader(
            status=header_dict.get("status", 0),
            QTime=header_dict.get("QTime", 0),
            params=solr_params,
        )


class SolrDoc(BaseModel):
    id: str
    name: Optional[str] = ""
    score: Optional[float] = None

    type: Optional[str] = ""
    type_name: Optional[str] = ""
    vtype: Optional[str] = "1"
    city: Optional[str] = ""
    county:Optional[str] = ""
    neighborhood: Optional[str] = ""
    zip_code: Optional[str] = ""
    x: Optional[int | float] = None
    y: Optional[int | float] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    timestamp: Optional[int | str] = None

    # add dynamic fields Solr might include, e.g. geospatial, type, etc.
    model_config = {"extra": "allow", "exclude_none": False, "populate_by_name": True}

    @staticmethod
    def toSchema(record:SolrStopRecord):
        record_dict = record.__dict__
        return SolrDoc(**record_dict)



class SolrResponseBody(BaseModel):
    numFound: int
    start: int
    docs: List[SolrDoc]

    @staticmethod
    def to_schema(response: SResponse) -> "SolrResponseBody":
        docs = [SolrDoc.toSchema(doc) for doc in response.docs]
        return SolrResponseBody(
            numFound=response.numFound, start=response.start, docs=docs
        )


class SolrResponseSchema(BaseModel):
    status_code: int = 200,
    status_message: Optional[str] = None,
    has_errors: bool = False,
    has_alerts: bool = False,
    alerts: Optional[List[str]] = [],
    date_info: Optional[Dict[str, Any]] = {}
    responseHeader: SolrResponseHeader
    response: SolrResponseBody

    @staticmethod
    def to_schema(solr_response: SolrResponse):
        response: SolrResponseBody = SolrResponseBody.to_schema(solr_response.response)
        response_header = solr_response.responseHeader.__dict__
        header = SolrResponseHeader.to_schema(response_header)
        return SolrResponseSchema(
            status_code=solr_response.status_code,
            status_message=solr_response.status_message,
            has_errors=solr_response.has_errors,
            has_alerts=solr_response.has_alerts,
            date_info=solr_response.date_info,
            alerts=solr_response.alerts,
            response=response,
            responseHeader=header)
