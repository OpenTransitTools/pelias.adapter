import unittest
from pyramid import testing

from ott.utils import json_utils
from ott.utils import file_utils
from pelias.adapter.control.pelias_to_solr import PeliasToSolr

PORT="45454"


class TestPeliasToSolr(unittest.TestCase):
    def setUp(self):
        self.base_path = file_utils.get_file_dir(__file__)

    def tearDown(self):
        pass

    def test_pelias_to_solr(self):
        p = self.parse('./data/search13135.json')
        self.assertTrue(len(p.response.docs) > 0)

    def parse(self, file_name):
        file_path = file_utils.path_join(self.base_path, file_name)
        json = json_utils.file_to_json(file_path)
        p = PeliasToSolr.parse_json(json)
        return p
