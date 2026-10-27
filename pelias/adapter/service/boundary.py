import requests
import schedule
import logging
log = logging.getLogger(__file__)


def_domain = "http://localhost:8080"
time_out = 3.0


def reset_timeout():
    """ pretty cool - we decrease time out if service not available, but resets if serv comes back """
    global time_out
    time_out = 3.0
    print("reset timeout")

schedule.every(200).seconds.do(reset_timeout)


def get_right_part(text, delimiter):
    """
    splits once from the right, then takes the last element
    will handle if delimiter not in text
    """
    return text.rsplit(delimiter, 1)[-1]


def check_layer(rec, layer, domain=def_domain, def_val=False):
    """
    call geoserver WFS to see if this geocord result is in/out of a given layer

    in testing the WFS result, we should see (at least part of) the layer name in the response,
    ala WFS on layer "ott:trimet_service_distrct" returns "id": "trimet_service_distrct.1" in the
    response whenever the given point is cointained in that service district layer
    """
    global time_out
    ret_val = def_val
    try:
        uri = f"{domain}/geoserver/ott/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName={layer}&propertyName=id&outputFormat=application/json&CQL_FILTER=CONTAINS(geom,POINT({rec.lon}%20{rec.lat}))"
        rs = requests.get(uri, timeout=time_out)
        simple_layer_name = get_right_part(layer, ":")  # e.g., "trimet_service_distrct" (drop the "ott:")
        if simple_layer_name in rs.text:
            ret_val = True
    except Exception as e:
        log.warning(e)
        time_out = time_out * 0.9 + 0.01
        schedule.run_pending()
    return ret_val


def district(rec, layer="ott:trimet_service_distrct"):
    val = check_layer(rec, layer)
    setattr(rec, get_right_part(layer, ":"), val)
    if "trimet" in layer:
        setattr(rec, "trimet_boundary", val)  # old SOLR element name for backwards compatability


def ada(rec, layer="ott:trimet_ada"):
    val = check_layer(rec, layer)
    setattr(rec, get_right_part(layer, ":"), val)
    if "trimet" in layer:
        setattr(rec, "ada_boundary", val)  # old SOLR element name
