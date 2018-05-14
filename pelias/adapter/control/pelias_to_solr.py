from pelias.adapter.model.solr.solr_response import SolrResponse
from ott.utils import json_utils
from ott.utils import html_utils

import urllib
import logging
log = logging.getLogger(__file__)


class PeliasToSolr(object):

    @classmethod
    def solr_to_pelias_param(cls, solr_params):
        """
        convert SOLR dict params dict of params for Pelias

        :see: https://trimet.org/solr/select?q=3&rows=6
        :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop
        :see: https://ws-st.trimet.org/pelias/v1/autocomplete?text=13135&size=1&layers=address&sources=osm
        """
        ret_val = {}

        text = html_utils.get_first_param(solr_params, 'q')
        if text: ret_val['text'] = text

        size = html_utils.get_first_param(solr_params, 'rows')
        if size: ret_val['size'] = size

        format = html_utils.get_first_param(solr_params, 'wt')
        if format and format == "xml":
            ret_val['format'] = 'xml'

        layers = html_utils.get_first_param(solr_params, 'fq')
        if layers:
            layers = layers.replace('%3A', ':')
            if layers == 'type:stop':
                ret_val['layers'] = 'stops'
            elif layers == 'type:pr':
                ret_val['layers'] = 'pr'

        return ret_val

    @classmethod
    def solr_to_pelias_param_str(cls, solr_params):
        """
        convert SOLR dict params to string of params for calling Pelias via url
        """
        pelias_params = cls.solr_to_pelias_param(solr_params)
        ret_val = urllib.urlencode(pelias_params)  # converts dict to a string after encoding each value in dict
        return ret_val

    @classmethod
    def parse_json(cls, json):
        ret_val = SolrResponse()
        ret_val.parse_pelias(json)
        return ret_val

    @classmethod
    def call_pelias_parse_results(cls, solr_params, url):
        param_str = cls.solr_to_pelias_param_str(solr_params)
        json = json_utils.stream_json(url, param_str)
        ret_val = cls.parse_json(json)
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
        #import pdb; pdb.set_trace()
        pelias = None
        if auto_url:
            pelias = cls.call_pelias_autocomplete(solr_params, auto_url)

        if search_url and (pelias is None or pelias.num_records() < 1):
            pelias = cls.call_pelias_search(solr_params, search_url)

        return pelias


