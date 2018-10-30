import unittest
from pyramid import testing

from ott.utils import json_utils
from ott.utils import file_utils
from pelias.adapter.control.pelias_to_solr import PeliasToSolr
from pelias.adapter.model.solr.solr_stop_record import SolrStopRecord

PORT="45454"


class BaseUnit(unittest.TestCase):
    def setUp(self):
        self.base_path = file_utils.get_file_dir(__file__)

    def tearDown(self):
        pass

    def csv(self, file_name):
        file_path = file_utils.path_join(self.base_path, file_name)
        json = json_utils.file_to_json(file_path)
        p = PeliasToSolr.parse_json(json)
        return p

    def json(self, file_name):
        file_path = file_utils.path_join(self.base_path, file_name)
        json = json_utils.file_to_json(file_path)
        p = PeliasToSolr.parse_json(json)
        return p


class TestStringsCrash(BaseUnit):
    def setUp(self):
        super(TestStringsCrash, self).setUp()
        self.auto_url = "https://ws-st.trimet.org/pelias/v1/autocomplete"
        self.search_url = "https://ws-st.trimet.org/pelias/v1/search"

    def tearDown(self):
        pass

    def test_wrapp_alias(self):
        p = self.csv('./data/search13135.json')
        self.assertTrue(len(p.response.docs) > 0)
