from ott.utils.svr.pyramid import response_utils
from ott.utils import html_utils
from ott.utils import geo_utils

from . import pelias_json_queries

import logging
log = logging.getLogger(__file__)


class PeliasWrapper(object):

    rtp_agencies = [
        "clackamas",
        "ctran",
        "mult",
        "rideconnection",
        "sam",
        "smart",
        "wapark"
    ]

    @classmethod
    def rtp_stop_filter(cls):
        """
        cache up list of pelias stop filters
        pelias/search?text=2&layers=-wapark:stops,-smart:stops,-ctran:stops
        -ctran:stops,-smart:stops,-sam:stops,-rideconnection:stops,-clackamas:stops,-mult:stops,-wapark:stops
        """
        if not cls._rtp_stop_filter:
            f = ["-{}:stops".format(a) for a in cls.rtp_agencies]
            cls._rtp_stop_filter = ','.join(f)
        return cls._rtp_stop_filter
    _rtp_stop_filter = None

    @classmethod
    def wrapp(cls, main_url, bkup_url, reverse_geo_url, query_string, def_size=10, in_recursion=False, is_calltaker=False, is_rtp=False):
        """ will call either autocomplete or search """
        ret_val = None

        # step 1: break out the size and text parameters
        size = html_utils.get_numeric_value_from_qs(query_string, 'size', def_size)
        text = html_utils.get_param_value_from_qs(query_string, 'text')

        # step 1b: filter agencies if we're in single-agency (TriMet) exclusive mode
        #import pdb; pdb.set_trace()
        if not is_rtp:
            query_string = "{}&layers={}".format(query_string, cls.rtp_stop_filter())

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
                r = cls.wrapp(main_url, bkup_url, reverse_geo_url, qs, def_size, is_calltaker=is_calltaker, is_rtp=is_rtp, in_recursion=True)
                if cls.has_features(r):
                    ret_val = r

        # step 5: clean up the label attribute
        cls.fixup_response(ret_val, size, is_calltaker=is_calltaker, is_rtp=is_rtp)

        return ret_val

    @classmethod
    def reverse(cls, reverse_geo_url, query_string):
        """
        call the reverse geocoder
        :note: pelias does not (seemingly) talk to the stops or other custom layers (just OSM layer)
        :url: /reverse?point.lat=45.51423467680257&point.lon=-122.7097523397708
        """
        # import pdb; pdb.set_trace()
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
    def dedup_addresses(cls, pelias_json):
        """
        TODO needs work and testing

        this mucks with the pelias_json to filter out (dedup) matching named 'features'
        if filtering is applied, then the pelias_json['features'] array will be altered 

        examples:
            1114 Cesar Chavez Blvd
            1505 NW 118th Ct
        """
        features = pelias_json.get('features', [])

        # step 0: make sure there are 2+ records (eg something to dedupe)
        if len(features) < 2:
            return

        # step 1: sort addresses from other records
        adds = []
        new_other = []
        for f in features:
            p = f.get('properties')
            if p is None:
                continue
            if p.get('layer') in ('address'):
                adds.append(f)
            else:
                new_other.append(f)

        # step 2: make sure we have at least 2 addresses (eg addresses to dedupe)
        if len(adds) < 2:
            return

        # step 3: filter duplicate (adjacent) named address records
        new_adds = []
        num_addresses = len(adds)
        if num_addresses > 0:
            new_adds.append(adds[0])
            if num_addresses >= 2:  # make sure we have multiple addresses (eg duplicates to potentially dedup)
                #import pdb; pdb.set_trace()
                i=1
                while i < num_addresses:
                    n1 = adds[i].get('properties').get('name', "").lower().replace('.', '').replace('boulevard','blvd').replace('court','ct')
                    n2 = adds[i-1].get('properties').get('name', "").lower().replace('.', '').replace('boulevard','blvd').replace('court','ct')
                    l1 = len(n1)
                    l2 = len(n2)
                    d  = abs(l1 - l2)
                    #import pdb; pdb.set_trace()
                    # filter out if address names are similar (e.g., same or majority subset of one another)
                    if l1 > 5 and l2 > 5 and d <= 6 and (n1 in n2 or n2 in n1):
                        i += 1
                        continue
                    else:
                        new_adds.append(features[i])
                        i += 1

        pelias_json['features'] = new_adds + new_other
        return

    @classmethod
    def fixup_response(cls, pelias_json, size=10, ele='label', is_calltaker=False, is_rtp=False):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element """

        # step 1: loop thru the records in the Pelias response
        if cls.has_features(pelias_json):
            #cls.dedup_addresses(pelias_json)

            for i, f in enumerate(pelias_json.get('features')):
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

                # step 3: for stops, possibly reduce the size of the string
                if "stops" in p.get('layer'):
                    if not is_rtp and "TRIMET" in p.get('id'):
                        name = cls.get_property_value(p, 'name', 'label')
                        if name and len(name) > 10:
                            city = pelias_json_queries.neighborhood_and_city(p, sep=' - ')
                            street_dir = pelias_json_queries.get_addendum_value(p, 'dir')
                            if street_dir:
                                name = name.replace("(TriMet Stop ", "{} (".format(street_dir))
                            else:
                                name = name.replace("TriMet Stop ", "")

                            rename = pelias_json_queries.append(name, city)

                # step 4: rename routes
                elif p.get('layer') == 'routes':
                    name = cls.get_property_value(p, 'name', 'label')
                    route_lbl = "Transit Route"
                    if "TRIMET" in p.get('id'):
                        route_lbl = "TriMet Route" 
                    rename = "{} ({})".format(name, route_lbl)
                    
                # step 5: Post Office ... add zipcode to label
                elif p.get('layer') == 'post_office':
                    name = cls.get_property_value(p, 'name', 'label')
                    zipcode = cls.get_property_value(p, 'postalcode')
                    rename = pelias_json_queries.append3(name, 'Post Office', zipcode, sep1=' ')

                # step 6: default rename is to add city or region, etc...
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
                    neighborhood = pelias_json_queries.get_neighborhood(pelias_json)
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
        if pelias_json.get('features', None):
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
                            neighborhood = pelias_json_queries.get_neighborhood(p)
                            if neighborhood:
                                new_name = "{} ({})".format(name, neighborhood)
                        p['name'] = new_name
