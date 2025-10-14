import logging

from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from com.github.ott.pelias.adapter.core.config import CACHE_LONG
from com.github.ott.pelias.adapter.service import pelias_service
from com.github.ott.pelias.adapter.service.config import SearchApiType

log = logging.getLogger(__file__)

router = APIRouter()

CACHE_LONG = f"public, max-age={CACHE_LONG}"


def get_json_response(
    request: Request,
    service: SearchApiType = SearchApiType.autocomplete,
    is_rtp: bool = False,
) -> JSONResponse:
    ret_val = pelias_service.get_pelias_response(
        service=service, request=request, is_rtp=is_rtp
    )

    return JSONResponse(content=ret_val, headers={"Cache-Control": CACHE_LONG})


@router.get("/{api}")
def pelias(
    request: Request,
    text: str = Query(..., description="The search text"),
    api: SearchApiType = SearchApiType.autocomplete,
) -> JSONResponse:
    return get_json_response(request=request, service=api)


@router.get("/rtp/{api}")
def pelias_from_rtp(
    request: Request,
    text: str = Query(..., description="The search text"),
    api: SearchApiType = SearchApiType.autocomplete,
) -> JSONResponse:
    return get_json_response(
        request=request, service=SearchApiType.autocomplete, is_rtp=True
    )
