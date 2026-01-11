from ott.utils.svr.pyramid import response_utils
from ott.utils import html_utils
from ott.utils import geo_utils

from . import pelias_json_queries
from . import pelias_json_queries

import logging
log = logging.getLogger(__file__)

SKIP="SKIP"


class PeliasWrapper(object):
    # note: agencies are defined in config/base.ini, and set here pyramid.view
    rtp_agencies = []
    _rtp_agency_filter = None

    @classmethod
    def rtp_agency_filter(cls):
        """
        cache up list of agency filters before calling Pelias, so we only get TriMet data
        pelias/search?text=2&layers=-wapark:stops,-smart:stops,-ctran:stops
        -ctran:stops,-smart:stops,-sam:stops,-rideconnection:stops,-clackamas:stops,-mult:stops,-wapark:stops
        """
        if len(cls.rtp_agencies) < 1:
            cls._rtp_agency_filter = SKIP

        if not cls._rtp_agency_filter:
            f = ["-{}:stops".format(a) for a in cls.rtp_agencies]
            cls._rtp_agency_filter = ','.join(f)

        return cls._rtp_agency_filter

    @classmethod
    def check_invalid_layers(cls, resp):
        """
        if Pelias doesn't like the layers parameter used for agency filtering, this will turn
        off the filter for future requests

        this is a bit of hackery to turn off the rtp_agency_filter for future requests so we 
        don't hose the wrapper. So if we see that Pelias doesn't like our layers setting, we'll
        set the agency filter to SKIP, and all future requests should now work.
        """
        try:
           if resp and resp.get('geocoding').get('errors'):
                err = resp.get('geocoding').get('errors')[0]
                if "invalid layers parameter" in err:
                    log.warning("turning off the filter {} due to this error {}".format(cls._rtp_agency_filter, err))
                    cls._rtp_agency_filter = SKIP
        except:
            pass

    @classmethod
    def wrapp(cls, main_url, bkup_url, reverse_geo_url, query_string, def_size=10, in_recursion=False, is_calltaker=False, is_rtp=False):
        """ will call either autocomplete or search """
        ret_val = None

        # step 1: break out the size and text parameters
        size = html_utils.get_numeric_value_from_qs(query_string, 'size', def_size)
        text = html_utils.get_param_value_from_qs(query_string, 'text')

        # don't filter (below) if request already includes its own layers param
        has_layers = "layers" in query_string

        # step 1b: filter agencies if we're in single-agency (TriMet) exclusive mode
        #import pdb; pdb.set_trace()
        if not has_layers and not is_rtp and cls._rtp_agency_filter != SKIP:
            query_string = "{}&layers={}".format(query_string, cls.rtp_agency_filter())

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

            # step 3b: call Pelias..and if autocomplete / search doesn't work, try the other service
            ret_val = response_utils.proxy_json(main_url, query_string)
            if not cls.has_features(ret_val):
                alt_resp = response_utils.proxy_json(bkup_url, query_string)
                if alt_resp and 'features' in alt_resp:
                    ret_val = alt_resp

        # step 3c: prevent our filter (Pelias error 'invalid layers') from screwing up all Pelias requests
        if not has_layers:
            cls.check_invalid_layers(ret_val)

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
        this mucks with the pelias_json to filter out (dedup) matching address 'features'
        if filtering is applied, then the pelias_json['features'] array will be altered 

        examples:
            1114 SE Cesar Chavez Blvd and 1114 SE Cesar Chavez Boulevard
            1505 NW 118th Ct
        """
        features = pelias_json.get('features', [])

        # step 0: make sure there are 2+ records (eg something to dedupe)
        if len(features) < 2:
            return

        def are_very_near(plist, feat):
            ret_val = False
            if len(plist) > 0:
                for p in plist:
                    # compare distances between p and feat
                    if p == feat:
                        # ret_val = True
                        break
                    pass

            return ret_val

        filtered = []
        prev = []

        # step a: loop thru all features
        for f in features:
            p = f.get('properties')

            # step b: treat address features differently
            if p.get('layer') in ('address'):
                # step c: if this address feature is near other seen features, filter it
                if are_very_near(prev, f):
                    log.info("filter this feature")
                else:
                    prev.append(f)
                    filtered.append(f)
            else:
                filtered.append(f)

        pelias_json['features'] = filtered
        return filtered

    @classmethod
    def fixup_response(cls, pelias_json, size=10, ele='label', is_calltaker=False, is_rtp=False):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element .. """

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
                    name = cls.get_property_value(p, 'name', 'label')

                    # 3a: if we're just a single agency (and TriMet), then strip off junk
                    if not is_rtp and "TRIMET" in p.get('id'):
                        name = name.replace("TriMet Stop ", "")

                        # backward compatible for old TORA id formatting of id::TRIMET::stops
                        # a stop page (https://trimet.org/home/stop/4) via geocoder https://trimet.org/home/search
                        # TODO: should probably remove this eventually
                        if "stops:TRIMET" in p.get('id'):
                            idz = p.get('id').replace("stops:TRIMET:", "")
                            p['id'] = "{}::TRIMET::stops".format(idz)

                    # 3b: remove "stops:" from ID to get TORA RTP to work properly
                    #     TODO: should probably remove this eventually
                    if is_rtp and "stops:" in p.get('id'):
                        p['id'] = p.get('id').replace("stops:", "")

                    # 3c: remove state and country from the label
                    if name and len(name) > 10:
                        city = pelias_json_queries.neighborhood_and_city(p, sep=' - ')
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
