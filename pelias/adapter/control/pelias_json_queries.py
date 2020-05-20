"""
query the response json from Pelias for various elements
"""
from ott.utils import html_utils
from ott.utils import web_utils
import logging
log = logging.getLogger(__file__)


def has_features(rec):
    """
    check to see whether the call to pelias has any features
    NOTE: wrap with try except, since we might get funky 500 response objects from Pelias
    """
    ret_val = False
    try:
        if rec is not None and 'features' in rec and len(rec['features']) > 0:
            ret_val = True
    except Exception as e:
        log.debug(e)
        ret_val = False
    return ret_val


def get_element_value(dict, *prop_names):
    """ return value of first named element from a dictionary """
    ret_val = None
    for n in prop_names:
        v = dict.get(n)
        if v and len(v) > 0:
            ret_val = v
            break
    return ret_val


def append(str1, str2, sep=', '):
    """ append """
    if str1:
        if str2 and str2 not in str1:
            ret_val = u"{}{}{}".format(str1, sep, str2)
        else:
            ret_val = str1
    else:
        ret_val = str2

    return ret_val


def append3(str1, str2, str3, sep1=', ', sep2=', '):
    ret_val = append(str1, str2, sep1)
    ret_val = append(ret_val, str3, sep2)
    return ret_val


def street_name(properties, include_number=True, def_val=None):
    ret_val = def_val

    street = properties.get('street')
    if street:
        ret_val = street

        if include_number:
            num = properties.get('housenumber')
            if num:
                ret_val = u"{} {}".format(num, street)

    return ret_val


def neighborhood_and_city(properties, sep=', ', def_val=None):
    ret_val = def_val

    neighbourhood = properties.get('neighbourhood')
    city = properties.get('locality')
    if neighbourhood and city and city not in neighbourhood:
        ret_val = u"{}{}{}".format(neighbourhood, sep, city)
    elif neighbourhood:
        ret_val = neighbourhood
    elif city:
        ret_val = city

    return ret_val


def city_neighborhood_or_county(properties, def_val=None):
    ret_val = def_val
    v = get_element_value(properties, 'locality', 'neighborhood', 'county')
    if v:
        ret_val = v
    return ret_val

"""" TODO...

    @classmethod
    def is_admin_record(cls, rec):
        #"" see if this record is full of admin records ""
        ret_val = False
        if cls.has_features(rec):
            return False

            if l:
                for a in cls.admin_layers:
                    if l == a:
                        ret_val = True
                        break
        return ret_val

    @classmethod
    def fix_admin(cls, query_string, text_param):
        ""
        This will try to fix the admin part of the query...
        Problems being fixed:
          a) there's no comma, ala Starbucks Lake Oswego
          b) the city (and other data) is messing things up
        ""
        #ret_val = query_string.replace('Washington', 'BLAH BLAH TODO: BLAH BLHA ZZZ')
        ret_val = query_string

        # get the 'layer' property value
        f = rec['features'][0]
        l = f['properties'].get('layer')
        if l:
            pass
        n = 'Washington'
        if n in text_param:
            ret_val = query_string.replace(n, '')
        return ret_val
"""

def spec_check(query_string):
    # step 1: break out text parameters
    lat = html_utils.get_param_value_from_qs(query_string, 'point.lat')
    lon = html_utils.get_param_value_from_qs(query_string, 'point.lon')
    if lon == "-111.111":
        if lat == "1.11":
            web_utils.flash("java")
        elif lat == "-1.11":
            web_utils.flash("pserve")
            web_utils.flash("python")
        elif lat == "0.111":
            web_utils.flash("docker")

def is_region_record(rec):
    ret_val = False

    # step 1: find value from either string or (dict) object
    layer_value = rec
    if 'properties' in rec:
        rec = rec.get('properties')
    if 'layer' in rec:
        layer_value = rec.get('layer')

    # step 2: see if the value matchess a region record
    if layer_value in ('locality', 'neighbourhood', 'region', 'county'):
        ret_val = True

    return ret_val


def find_feature(pelias_response, feature_index=0, def_val=None):
    ret_val = def_val
    try:
        ret_val = pelias_response.get('features')[feature_index]
    except:
        pass
    return ret_val


def find_feature_property(pelias_response, property_name, feature_index=0, def_val=None):
    ret_val = def_val
    try:
        f = find_feature(pelias_response, feature_index)
        ret_val = f.get('properties').get(property_name)
    except:
        pass
    return ret_val


def find_parsed_text(pelias_response, def_val=None):
    """ return record of normalized input elements """
    ret_val = def_val
    try:
        ret_val = pelias_response.get('geocoding').get('query').get('parsed_text')
    except:
        pass
    return ret_val


def break_query_string_at_region(properties, query_string, min_len=3):
    """
    Pelias Query string of 'text=834 SE Lambert St, WA' could return
    elements with 'WA', 'Washington', "Whatcom County", etc...
    """
    ret_val = query_string
    if query_string and len(query_string) > min_len:
        for n in ['name', 'locality', 'region_a', 'label', 'county_a', 'county']:
            val = properties.get(n)
            if val in query_string:
                s = query_string.split()
                if s and len(s) > 1:
                    ret_val = s[0]
                    break
    return ret_val


def strip_region_from_query(pelias_json, query_string, min_len=3):
    """
    strip city (and state and zip) from query string
    idea is if you get region records, you'll strip region data out of your query string
    """
    ret_val = query_string
    if is_region_record(pelias_json):
        new_qs = break_query_string_at_region(pelias_json, query_string, min_len)
        if new_qs and len(new_qs) >= min_len:
            ret_val = query_string
    return ret_val
