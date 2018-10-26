from ott.utils.svr.pyramid import response_utils
from ott.utils import html_utils
from ott.utils import geo_utils
from . import pelias_json_queries


class PeliasWrapper(object):

     #admin_props = ''

    @classmethod
    def wrapp(cls, main_url, bkup_url, reverse_geo_url, query_string, def_size=5, in_recursion=False):
        """ will call either autocomplete or search """
        ret_val = None

        # import pdb; pdb.set_trace()

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
            ret_val = response_utils.proxy_json(main_url, query_string)
            if not cls.has_features(ret_val):
                ret_val = response_utils.proxy_json(bkup_url, query_string)

        # step 4: check whether the query result has something usable...
        if not in_recursion:

            # step 4a: if this is an admin record, let's see whether
            if cls.is_admin_record(ret_val):
                qs = cls.strip_admin(query_string)
                r = cls.wrapp(main_url, bkup_url, reverse_geo_url, qs, def_size, in_recursion=True)
                if cls.has_features(r):
                    ret_val = r

        # step 5: clean up the label attribute
        cls.fixup_response(ret_val, size)

        return ret_val

    @classmethod
    def has_features(cls, rec):
         """ check to see whether the call to pelias has any features """
         ret_val = False
         if rec is not None and 'features' in rec and len(rec['features']) > 0:
             ret_val = True
         return ret_val

    @classmethod
    def is_admin_record(cls, ret_val):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element """
        ret_val = False
        ret_val = True
        return ret_val

    @classmethod
    def strip_admin(cls, query_string):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element """
        ret_val = query_string.replace('Washington', '')
        return ret_val

    @classmethod
    def fixup_response(cls, pelias_json, size, ele='label'):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element """

        # step 1: loop thru the records in the Pelias response
        if pelias_json.get('features'):
            for i, f in enumerate(pelias_json['features']):
                if i >= size:
                    break

                p = f.get('properties')
                if p is None:
                    continue

                rename = None

                # step 2: for venues, rename the venue with the neighborhood & city
                if p.get('layer') in ('venue', 'major_employer'):
                    name = pelias_json_queries.get_name(p)
                    street = pelias_json_queries.street_name(p, include_number=False)
                    city = pelias_json_queries.neighborhood_and_city(p, sep=' - ')
                    rename = pelias_json_queries.append3(name, street, city)

                # step 3: Post Office ... add zipcode to label
                elif p.get('layer') == 'post_office':
                    name = pelias_json_queries.get_name(p)
                    zipcode = pelias_json_queries.get_name(p, ele='postalcode', ele2='street')
                    rename = pelias_json_queries.append3(name, 'Post Office', zipcode, sep1=' ')

                # step 4: default rename is to add city or region, etc...
                else:
                    name = pelias_json_queries.get_name(p)
                    city = pelias_json_queries.city_neighborhood_or_county(p)
                    rename = pelias_json_queries.append(name, city)

                # step 5: append
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
        """ will loop thru results, and append street names to venues """
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