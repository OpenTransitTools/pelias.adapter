from typing import List, Optional

from pydantic import BaseModel, Field


class LangModel(BaseModel):
    name: Optional[str] = None
    iso6391: Optional[str] = Field(None, alias="iso6391")


class QueryModel(BaseModel):
    text: str
    size: Optional[int] = None
    layers: Optional[List[str]] = None
    lang: Optional[LangModel] = None


class GeocodingModel(BaseModel):
    version: Optional[str] = None
    attribution: Optional[str] = None
    query: Optional[QueryModel] = None


class GeometryModel(BaseModel):
    type: str
    coordinates: List[float]


class PropertiesModel(BaseModel):
    id: Optional[str] = None
    gid: Optional[str] = None
    layer: Optional[str] = None
    source: Optional[str] = None
    name: Optional[str] = None
    confidence: Optional[float] = None
    country: Optional[str] = None
    country_a: Optional[str] = None
    region: Optional[str] = None
    locality: Optional[str] = None
    label: Optional[str] = None


class FeatureModel(BaseModel):
    type: str
    geometry: GeometryModel
    properties: PropertiesModel


class PeliasResponse(BaseModel):
    geocoding: GeocodingModel
    type: str = Field(..., description="Usually 'FeatureCollection'")
    features: List[FeatureModel]
    bbox: Optional[List[float]] = None
