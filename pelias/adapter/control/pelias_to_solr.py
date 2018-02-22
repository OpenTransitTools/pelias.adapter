from pelias.adapter.model.solr.solr_response import SolrResponse
from ott.utils import html_utils

class PeliasToSolr(object):

    @classmethod
    def solr_to_pelias_param(cls, solr_params):
        """
        convert SOLR dict params dict of params for Pelias

        :see: https://trimet.org/solr/select?q=3&rows=6
        :see: https://trimet.org/solr/select?q=3&rows=6&wt=json&fq=type:stop
        :see: https://ws-st.trimet.org/pelias/v1/autocomplete?text=13135&size=1&layers=address&sources=osm
        """
        import pdb; pdb.set_trace()

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
        ret_val = html_utils.dict_to_param_str(pelias_params)
        return ret_val

    @classmethod
    def parse_json(cls, json):
        ret_val = SolrResponse()
        ret_val.parse_pelias(json)
        return ret_val
