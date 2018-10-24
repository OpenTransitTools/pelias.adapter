from ott.utils.svr.pyramid import response_utils
from . import pelias_json_queries

class PeliasWrapper(object):

    @classmethod
    def wrapp(cls, main_url, bkup_url, query_string):
        """ will call either autocomplete or search """
        ret_val = response_utils.proxy_json(main_url, query_string)
        if ret_val is None or ret_val['features'] is None or len(ret_val['features']) < 1:
            ret_val = response_utils.proxy_json(bkup_url, query_string)

        # import pdb; pdb.set_trace()
        cls.fixup_response(ret_val)
        return ret_val

    @classmethod
    def fixup_response(cls, pelias_json, ele='label'):
        """ will loop thru results, cleaning up / renaming / relabeling the specified element """

        # step 1: loop thru the records in the Pelias response
        if pelias_json.get('features'):
            for f in pelias_json['features']:
                rename = None
                p = f.get('properties')

                # step 2: for venues, rename the venue with the neighborhood & city
                if p and p.get('layer') == 'venue':
                    pass

                # step 3: default rename is to add city or region, etc...
                else:
                    pass

                #
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
