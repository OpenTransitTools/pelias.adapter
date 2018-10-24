from ott.utils.svr.pyramid import response_utils


class PeliasWrapper(object):

    @classmethod
    def wrapp(cls, main_url, bkup_url, query_string):
        """ will call either autocomplete or search """
        ret_val = response_utils.proxy_json(main_url, query_string)
        if ret_val is None or ret_val['features'] is None or len(ret_val['features']) < 1:
            ret_val = response_utils.proxy_json(bkup_url, query_string)
        cls.fixup_results(ret_val)
        return ret_val

    @classmethod
    def fixup_results(cls, pelias_json):
        """ will loop thru results, cleaning up the  """
        # import pdb; pdb.set_trace()
        if pelias_json.get('features'):
            for f in pelias_json['features']:
                p = f.get('properties')
                if p and p.get('layer') == 'venue':
                    n = cls.rename(p)
                    if n:
                        p['label'] = n
                else:
                    n = cls.rename(p)
                    if n:
                        p['label'] = n

    @classmethod
    def street_name(cls, pelias_json, include_number=True, def_val=None):
        ret_val = def_val

        street = pelias_json.get('street')
        if street:
            ret_val = street

            if include_number:
                num = pelias_json.get('housenumber')
                if num:
                    ret_val = "{} {}".format(num, street)

        return ret_val

    @classmethod
    def neighborhood_and_city(cls, pelias_json, sep=', ', def_val=None):
        ret_val = def_val

        neighbourhood = pelias_json.get('neighbourhood')
        city = pelias_json.get('locality')
        if neighbourhood and city:
            ret_val = "{}{}{}".format(neighbourhood, sep, city)
        elif neighbourhood:
            ret_val = neighbourhood
        elif city:
            ret_val = city

        return ret_val

    @classmethod
    def city_neighborhood_or_county(cls, pelias_json, def_val=None):
        ret_val = def_val

        city = pelias_json.get('locality')
        if city:
            ret_val = city
        else:
            neighbourhood = pelias_json.get('neighborhood')
            if neighbourhood:
                ret_val = neighbourhood
            else:
                county = pelias_json.get('county')
                if county:
                    ret_val = county

        return ret_val


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
