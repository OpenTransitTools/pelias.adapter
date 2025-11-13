import enum
import re
from typing import Literal, Optional

from pyramid.encode import urlencode
from pyramid.request import Request

from pelias.adapter.service import pelias_service

TRANSIT_LAYERS = (
    "trimet:stops,ctran:stops,sam:stops,smart:stops,mult:stops,wapark:stops"
)



class EvaluatesAs(enum.Enum):
    STREET_ADDRESS = "street_address"
    JUST_A_NUMBER = "just_a_number"
    STOP_REQUEST = "stop_request"
    UNKNOWN = "unknown"


def remove_non_digits(s: Optional[str]) -> str:
    """Return only the digits from `s`. None -> ''."""
    if not s:
        return ""
    return re.sub(r"\D+", "", s)




def normalize_address(addr: str) -> str:
    """Normalize common street abbreviations and directions in a U.S. address."""
    if not addr:
        return ""

    addr = addr.lower().strip()

    # Directional replacements
    directions = {
        r"\bn\b": "north",
        r"\bs\b": "south",
        r"\be\b": "east",
        r"\bw\b": "west",
        r"\bnw\b": "northwest",
        r"\bne\b": "northeast",
        r"\bsw\b": "southwest",
        r"\bse\b": "southeast",
    }

    # Street type replacements
    streets = {
        r"\bst\b": "street",
        r"\bstreet\b": "street",
        r"\bave\b": "avenue",
        r"\bav\b": "avenue",
        r"\baven\b": "avenue",
        r"\bavenue\b": "avenue",
        r"\bblvd\b": "boulevard",
        r"\brd\b": "road",
        r"\bdr\b": "drive",
        r"\bln\b": "lane",
        r"\bct\b": "court",
        r"\bcir\b": "circle",
        r"\bhwy\b": "highway",
        r"\bpl\b": "place",
        r"\bter\b": "terrace",
        r"\bpkwy\b": "parkway",
    }

    # Apply direction and street normalization
    for pattern, repl in {**directions, **streets}.items():
        addr = re.sub(pattern + r"\.?", repl, addr)

    # Remove double spaces and capitalize properly
    addr = re.sub(r"\s+", " ", addr).strip().title()
    return addr


def remove_duplicate_features(features):
    """
    Best shot at normalizing and removing duplicate features from pelias response
    """
    refined = {
        f["properties"]["name"].strip().lower(): f
        for f in features
        if isinstance(f, dict)
           and "properties" in f
           and isinstance(f["properties"], dict)
           and "name" in f["properties"]
           and isinstance(f["properties"]["name"], str)
    }
    normalized_addresses = {normalize_address(key): v for key, v in refined.items()}

    return list(normalized_addresses.values())


def adjust_layers_for_query(query_type, query_params) -> tuple[bool, dict]:
    if query_type in (EvaluatesAs.STOP_REQUEST, EvaluatesAs.JUST_A_NUMBER):
        query_params["layers"] = TRANSIT_LAYERS
        return True, query_params
    elif query_type is EvaluatesAs.STREET_ADDRESS:
        query_params["layers"] = "address"
    return False, query_params


def is_street_address(text: str) -> bool:
    return bool(
        re.search(
            r"\b\d{1,5}\s+\w+(?:\s+\w+)*\s+(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|ct|court)\b",
            text.lower(),
        )
    )


def get_query_type(query: str) -> tuple[EvaluatesAs, int]:
    query = query.lower().strip()
    stop_id = -1
    try:
        stop_id = int(query)
    except ValueError:
        # If parsing fails, stop_id remains -1, indicating the query is not a number.
        pass
    if is_street_address(query):
        query_type = EvaluatesAs.STREET_ADDRESS
    elif (
            query.startswith("stop")
            or query.startswith("stopid")
            or query.startswith("stop_id")
    ):
        query_type = EvaluatesAs.STOP_REQUEST
    elif stop_id > 0:
        query_type = EvaluatesAs.JUST_A_NUMBER
    else:
        query_type = EvaluatesAs.UNKNOWN

    return query_type, stop_id

def get_best_match(ret_val, text: str, is_stop_request=False):
    """
    from a pelias response, find the best match (first in list) and return it
    :param ret_val: pelias response json
    :param text: original query text
    :param is_stop_request: whether this is a stop request
    :return: first match from pelias response
    """
    features = ret_val.get("features", [])
    if not features or len(features) == 1:
        return ret_val
    else:
        features = remove_duplicate_features(features)
        if is_stop_request:
            # for stop requests, we expect exactly one match
            stop_id = remove_non_digits(text)
            if stop_id:
                matches = [
                    feat
                    for feat in features
                    if isinstance(feat.get("id"), str)
                    and feat["id"].endswith(f":{stop_id}")
                ]
                ret_val["features"] = matches
        else:
            matches = [
                f
                for f in features
                if text == f.get("properties", {}).get("name", "").lower().strip()
            ]
            if not matches:
                matches = [
                    f
                    for f in features
                    if text in f.get("properties", {}).get("name", "").lower().strip()
                ]
            if matches:
                ret_val["features"] = matches
    return ret_val


def refactor_pelias_request(request: Request, new_params: dict) -> Request:
    """update both request._query_params and the ASGI scope query_string,
    and clear cached URL so request.url reflects the new params


    """

    request.environ["QUERY_STRING"] = urlencode(new_params, doseq=True)

    if hasattr(request, "_query_params"):
        del request._query_params

    if hasattr(request, "_url"):
        # noinspection PyProtectedMember
        del request._url

    request._GET = None

    return request



def refine(request: Request,
           service: Literal["autocomplete", "search", "reverse"] = "autocomplete",
           is_rtp: bool = False) -> Request:
    """
            Do some data normalization here to eliminate duplicates and normalize addresses.
            Try to get to a single result.
            If query was ambiguous and we still end up with more than one result, return the first IF the query's size = 1

            """

    original_params = request.GET.copy()

    new_params = request.GET.copy()

    size, text = (
        int(new_params.get("size", 10)),
        (new_params.get("text") or "").lower().strip(),
    )
    query_type, stop_id = get_query_type(text)

    # pelias will just return first, so we'll get 10 and try to get a better first
    if size == 1:
        new_params["size"] = "10"

    # determine if this is a stop request and apply reset layers to STOPS_LAYERS
    # or if determined an address "address", for request
    is_stop_request, new_params = adjust_layers_for_query(query_type, new_params)

    # required to ensure new params and layers stick
    request = refactor_pelias_request(request=request, new_params=new_params)

    ret_val = pelias_service.get_pelias_response(service=service, request=request, is_rtp=is_rtp)

    _features = ret_val.get("features", [])

    # after the first request, we'll use feature.property.name to normalize
    # and remove dupes
    features = (
        remove_duplicate_features(_features)
        if _features and len(_features) > 1
        else _features
    )

    # if the custom layers query resulted in none, try again without the layers filter
    if (
            query_type
            in (
            EvaluatesAs.STOP_REQUEST,
            EvaluatesAs.JUST_A_NUMBER,
            EvaluatesAs.STREET_ADDRESS,
    )
            and not features
    ):
        # restore original params in scope and cached attrs
        request = refactor_pelias_request(request, original_params)

        ret_val = pelias_service.get_pelias_response(
            service=service, request=request, is_rtp=is_rtp
        )
        features = ret_val.get("features", [])

    if len(features) > 1:
        ret_val = get_best_match(
            ret_val, text=text, is_stop_request=is_stop_request
        )
        if size == 1:
            # if size=1, give them 1
            features = ret_val.get("features", [])
            if len(features) > 1:
                ret_val["features"] = features[0:1]
    else:
        ret_val["features"] = features

    # restore original params before returning
    refactor_pelias_request(request, original_params)

    return ret_val
