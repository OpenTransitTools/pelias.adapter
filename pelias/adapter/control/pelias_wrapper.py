from ott.utils.svr.pyramid import response_utils
from ott.utils import html_utils
from . import pelias_json_queries

class PeliasWrapper(object):

    @classmethod
    def wrapp(cls, main_url, bkup_url, reverse_geo_url, query_string, def_size=5):
        """ will call either autocomplete or search """

        # step 1: break out the size and text parameters
        text = html_utils

        ret_val = response_utils.proxy_json(main_url, query_string)
        if ret_val is None or ret_val['features'] is None or len(ret_val['features']) < 1:
            ret_val = response_utils.proxy_json(bkup_url, query_string)

        # import pdb; pdb.set_trace()
        size = def_size # TODO parse query_string for 'size'
        cls.fixup_response(ret_val, size)
        return ret_val

    @classmethod
    def fixup_response(cls, pelias_json, size, ele='label'):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element """

        # step 1: loop thru the records in the Pelias response
        if pelias_json.get('features'):
            for i, f in enumerate(pelias_json['features']):
                p = f.get('properties')
                if p is None:
                    continue
                if i > size:
                    break

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

                # step 4: append
                if rename:
                    p[ele] = rename



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
