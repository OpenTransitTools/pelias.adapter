from ott.utils.svr.pyramid import response_utils
from ott.utils import html_utils
from ott.utils import geo_utils

from . import pelias_json_queries

import logging
log = logging.getLogger(__file__)


class PeliasWrapper(object):

    @classmethod
    def wrapp(cls, main_url, bkup_url, reverse_geo_url, query_string, def_size=5, in_recursion=False,
              is_calltaker=False):
        """ will call either autocomplete or search """
        # import pdb; pdb.set_trace()
        ret_val = None

        # step 1: break out the size and text parameters
        size = html_utils.get_numeric_value_from_qs(query_string, 'size', def_size)
        text = html_utils.get_param_value_from_qs(query_string, 'text')

        # step 2 call reverse geocoder if we think text is a coord
        if geo_utils.is_coord(text):
            x, y = geo_utils.ll_from_str(text)
            ll = geo_utils.xy_to_url_param_str(x, y, x_name="point.lon", y_name="point.lat", check_lat_lon=True)
            qs = "{}&{}".format(query_string, ll)
            ret_val = response_utils.proxy_json(reverse_geo_url, qs)

        # step 3: call geocoder (if we didn't already reverse geocode, or if that result was null)
        if ret_val is None:
            # step 3a: special query string handling
            if text and len(text) > 1:
                # import pdb; pdb.set_trace()
                # convert searches for trimet (and sub-strings) to "TriMet Admin"
                # TODO: make this generic and configurable ... not specific to TriMet
                if len(text) <= 7 and text.lower() in "trimet":
                    frm = "text={}".format(text)
                    to = "text=TriMet%20HOP%20Admin%20Office"
                    query_string = query_string.replace(frm, to)

            ret_val = response_utils.proxy_json(main_url, query_string)
            if not cls.has_features(ret_val):
                alt_resp = response_utils.proxy_json(bkup_url, query_string)
                if alt_resp and 'features' in alt_resp:
                    ret_val = alt_resp

        # step 4: check whether the query result has something usable...
        if not in_recursion:
            # step 4a: if this is an admin record, let's see whether we can resub just street address
            if cls.is_wrong_city_bug(ret_val):
                """
                This code addresses the WRONG CITY bug, etc...
                https://github.com/OpenTransitTools/trimet-mod-pelias/issues/23 
                
                Here's an address that brings up an admin record from Pelias due to the wrong city:
                .../pelias/autocomplete?text=11911%20SW%20TONQUIN%20RD,%20SHERWOOD,%20OR%2097140
                """

                # step 4b: create a new query string of just the "text=NUMBER STREET"
                normalized_data = pelias_json_queries.find_parsed_text(ret_val)
                qs = "text={number} {street}".format(**normalized_data)
                qs = qs.replace(' ', '%20')

                # step 4c: re-call Pelias with our simple
                r = cls.wrapp(main_url, bkup_url, reverse_geo_url, qs, def_size, in_recursion=True)
                if cls.has_features(r):
                    ret_val = r

        # step 5: clean up the label attribute
        cls.fixup_response(ret_val, size, is_calltaker=is_calltaker)

        return ret_val

    @classmethod
    def reverse(cls, reverse_geo_url, query_string):
        pelias_json_queries.spec_check(query_string)
        ret_val = response_utils.proxy_json(reverse_geo_url, query_string)
        cls.fixup_response(ret_val)
        return ret_val

    @classmethod
    def is_wrong_city_bug(cls, response):
        """
        check if the original Pelias response is just a 'region' record (like City)
        if we have a single region record, then see if we have normalized address elements
        (e.g., 'number' and 'street' in the parsed_text record)
        """
        # import pdb; pdb.set_trace()
        ret_val = False
        features = response.get('features')
        if features and len(features) == 1 and pelias_json_queries.is_region_record(features[0]):
            normalized_data = pelias_json_queries.find_parsed_text(response)
            if 'number' in normalized_data and 'street' in normalized_data:
                ret_val = True
        return ret_val

    @classmethod
    def has_features(cls, rec):
        return pelias_json_queries.has_features(rec)

    @classmethod
    def get_property_value(cls, rec, *names):
        return pelias_json_queries.get_element_value(rec, *names)

    @classmethod
    def fixup_response(cls, pelias_json, size=10, ele='label', is_calltaker=False):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element """

        # step 1: loop thru the records in the Pelias response
        if cls.has_features(pelias_json):
            for i, f in enumerate(pelias_json['features']):
                if i >= size:
                    break

                p = f.get('properties')
                if p is None:
                    continue

                rename = None

                # step 2: for venues, rename the venue with the neighborhood & city
                if p.get('layer') in ('venue', 'major_employer', 'fare', 'fare_outlet'):
                    name = cls.get_property_value(p, 'name', 'label')
                    street = pelias_json_queries.street_name(p, include_number=False)
                    city = pelias_json_queries.neighborhood_and_city(p, sep=' - ')
                    rename = pelias_json_queries.append3(name, street, city)

                # step 3: rename routes
                elif p.get('layer') == 'routes':
                    name = cls.get_property_value(p, 'name', 'label')
                    route_lbl = "Transit Route"
                    if "TRIMET" in p.get('id'):
                        route_lbl = "TriMet Route" 
                    rename = "{} ({})".format(name, route_lbl)
                    
                # step 4: Post Office ... add zipcode to label
                elif p.get('layer') == 'post_office':
                    name = cls.get_property_value(p, 'name', 'label')
                    zipcode = cls.get_property_value(p, 'postalcode')
                    rename = pelias_json_queries.append3(name, 'Post Office', zipcode, sep1=' ')

                # step 5: default rename is to add city or region, etc...
                else:
                    name = cls.get_property_value(p, 'name', 'label')
                    city = pelias_json_queries.city_neighborhood_or_county(p)
                    rename = pelias_json_queries.append(name, city)

                # step 6: append '*' to any calltaker response when dealing with  interpolated recs
                if is_calltaker and p.get('match_type') == "interpolated":
                    rename = "*" + rename 

                # step 7: apply the rename to this record's properties dict
                if rename:
                    p[ele] = rename


    #### TODO -- replace the routines below with 'fixup_response' above ???

    @classmethod
    def rename(cls, pelias_json, def_val=None):
        ret_val = def_val
        try:
            name = pelias_json.get('name')
            if name:
                new_name = name
                if name:
                    pass
                else:
                    neighborhood = pelias_json.get('neighbourhood')
                    if neighborhood:
                        new_name = "{} ({})".format(name, neighborhood)
                if new_name:
                    ret_val = new_name
        except:
            pass
        return ret_val

    @classmethod
    def fix_venues_in_pelias_response(cls, pelias_json):
        """ 
        will loop thru results, and append street names to venues 
        NOTE: 2-24-2020: this routine is only used in the SOLR wrapper 
              the Pelias wrapper has a different rendering (see above)
        """
        if pelias_json.get('features'):
            for f in pelias_json['features']:
                p = f.get('properties')
                if p and p.get('layer') == 'venue':
                    name = p.get('name')
                    if name:
                        new_name = name
                        street = p.get('street')
                        if street:
                            num = p.get('housenumber')
                            if num:
                                new_name = "{} ({} {})".format(name, num, street)
                            else:
                                new_name = "{} ({})".format(name, street)
                        else:
                            neighborhood = p.get('neighbourhood')
                            if neighborhood:
                                new_name = "{} ({})".format(name, neighborhood)
                        p['name'] = new_name
