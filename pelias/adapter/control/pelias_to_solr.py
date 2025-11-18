from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlencode

from ott.utils import json_utils
from ott.utils import html_utils
from pelias.adapter.model.solr.solr_response import SolrResponse
from .pelias_wrapper import PeliasWrapper

import logging
log = logging.getLogger(__file__)


class PeliasToSolr(PeliasWrapper):

    @classmethod
    def solr_to_pelias_param(cls, solr_params, is_rtp=False):
        """
        convert SOLR dict params dict of params for Pelias

        :see: https://trimet.org/solr/select?q=3&rows=6
        :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop
        :see: https://ws-st.trimet.org/pelias/v1/autocomplete?text=13135&size=1&layers=address&sources=osm
        :see: https://dv.trimet.org/solr/select?rows=6&wt=json&qt=dismax&fq=(-type%3A26+AND+-type%3Aroute)&q=3
        """
        ret_val = {}

        text = html_utils.get_first_param(solr_params, 'q')
        if text: ret_val['text'] = text

        size = html_utils.get_first_param(solr_params, 'rows')
        if size: ret_val['size'] = size

        format = html_utils.get_first_param(solr_params, 'wt')
        if format and format == "xml":
            ret_val['format'] = 'xml'

        #import pdb; pdb.set_trace()
        layers = html_utils.get_first_param(solr_params, 'fq')
        if layers:
            l = ''
            n = ''

            # negation of layer type
            if '-type' in layers:
                n = '-'

            if 'stop' in layers and cls._rtp_agency_filter != "SKIP":
                # negate all stops layers ... only include trimet stops
                if n == '-':
                    l = "{}{},{},".format(l, cls.rtp_agency_filter(), '-trimet:stops')
                else:
                    l = "{}{}{},".format(l, n, 'trimet:stops')
            if 'pr' in layers:
                l = "{}{}{},".format(l, n, 'pr')
            if 'tc' in layers:
                l = "{}{}{},".format(l, n, 'tc')

            if len(l) > 1:
                ret_val['layers'] = l[:-1]  # trim off last ,comma,

        # note: if no SOLR 'fq' layer (filter) param was mapped, then apply the rtp agency filter
        if not ret_val.get('layers') and not is_rtp and cls._rtp_agency_filter != "SKIP":
            ret_val['layers'] = cls.rtp_agency_filter()

        return ret_val

    @classmethod
    def solr_to_pelias_param_str(cls, solr_params):
        """
        convert SOLR dict params to string of params for calling Pelias via url
        """
        pelias_params = cls.solr_to_pelias_param(solr_params)
        ret_val = urlencode(pelias_params)  # converts dict to a string after encoding each value in dict
        return ret_val

    @classmethod
    def parse_json(cls, json, solr_params=None):
        ret_val = SolrResponse()
        ret_val.parse_pelias(json, solr_params)
        return ret_val

    @classmethod
    def fix_venues_in_pelias_response(cls, pelias_json):
        """
        will loop thru results, and append street names to venues
        NOTE: 2-24-2020: this routine is only used in the SOLR wrapper
              the Pelias wrapper has a different rendering (see above)
        """
        if pelias_json.get('features', []):
            for f in pelias_json.get('features', []):
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


    @classmethod
    def call_pelias_parse_results(cls, solr_params, url):
        param_str = cls.solr_to_pelias_param_str(solr_params)
        json = json_utils.stream_json(url, param_str)
        cls.check_invalid_layers(json)
        #cls.fix_venues_in_pelias_response(pelias_json=json)
        cls.fixup_response(json, is_calltaker=True, is_rtp=False)
        ret_val = cls.parse_json(json, solr_params)
        return ret_val

    @classmethod
    def call_pelias_autocomplete(cls, solr_params, auto_url):
        ret_val = cls.call_pelias_parse_results(solr_params, auto_url)
        return ret_val

    @classmethod
    def call_pelias_search(cls, solr_params, search_url):
        ret_val = cls.call_pelias_parse_results(solr_params, search_url)
        return ret_val

    @classmethod
    def call_pelias(cls, solr_params, auto_url=None, search_url=None):
        pelias = None
        if auto_url:
            pelias = cls.call_pelias_autocomplete(solr_params, auto_url)

        if search_url and (pelias is None or pelias.num_records() < 1):
            pelias = cls.call_pelias_search(solr_params, search_url)

        return pelias


