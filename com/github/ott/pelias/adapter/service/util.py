import re
import enum
from typing import Optional


class QueryType(enum.Enum):
    STREET_ADDRESS = "street_address"
    JUST_A_NUMBER = "just_a_number"
    STOP_REQUEST = "stop_request"
    UNKNOWN = "unknown"


def is_street_address(text: str) -> bool:
    return bool(
        re.search(
            r"\b\d{1,5}\s+\w+(?:\s+\w+)*\s+(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|ct|court)\b",
            text.lower(),
        )
    )


def get_query_type(query: str) -> tuple[QueryType, int]:
    query = query.lower().strip()
    stop_id = -1
    try:
        stop_id = int(query)
    except ValueError:
        pass
    if is_street_address(query):
        query_type = QueryType.STREET_ADDRESS
    elif (
        query.startswith("stop")
        or query.startswith("stopid")
        or query.startswith("stop_id")
    ):
        query_type = QueryType.STOP_REQUEST
    elif stop_id > 0:
        query_type = QueryType.JUST_A_NUMBER
    else:
        query_type = QueryType.UNKNOWN

    return query_type, stop_id


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


def remove_non_digits(s: Optional[str]) -> str:
    """Return only the digits from `s`. None -> ''."""
    if not s:
        return ""
    return re.sub(r"\D+", "", s)
