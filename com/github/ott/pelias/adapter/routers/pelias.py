import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from com.github.ott.pelias.adapter.core.config import CACHE_LONG_STR
from com.github.ott.pelias.adapter.service import pelias_service
from com.github.ott.pelias.adapter.service.config import SearchApiType

log = logging.getLogger(__file__)

router = APIRouter()


def get_json_response(
    request: Request,
    service: SearchApiType = SearchApiType.autocomplete,
    is_rtp: bool = False,
    refine: bool = False,
) -> JSONResponse:
    ret_val = pelias_service.get_pelias_response(
        request, service, is_rtp, refine=refine
    )

    return JSONResponse(content=ret_val, headers={"Cache-Control": CACHE_LONG_STR})


@router.get("/{api}")
def pelias(
    request: Request,
    api: SearchApiType = SearchApiType.autocomplete,
) -> JSONResponse:
    return get_json_response(request=request, service=api)


@router.get("/refine/{api}")
def refine(
    request: Request,
    api: SearchApiType = SearchApiType.autocomplete,
) -> JSONResponse:
    return get_json_response(request=request, service=api, refine=True)


@router.get("/rtp/{api}")
def pelias_from_rtp(
    request: Request,
    api: SearchApiType = SearchApiType.autocomplete,
) -> JSONResponse:
    return get_json_response(request=request, service=api, is_rtp=True)
