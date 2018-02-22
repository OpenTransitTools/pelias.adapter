import unittest
from pyramid import testing

from ott.utils import json_utils
from ott.utils import file_utils
from pelias.adapter.control.pelias_to_solr import PeliasToSolr
from pelias.adapter.model.solr.solr_stop_record import SolrStopRecord

PORT="45454"


class TestPeliasToSolr(unittest.TestCase):
    def setUp(self):
        self.base_path = file_utils.get_file_dir(__file__)

    def tearDown(self):
        pass

    def test_pelias_to_solr(self):
        p = self.parse('./data/search13135.json')
        self.assertTrue(len(p.response.docs) > 0)

    def test_unique_coords(self):
        p = self.parse('./data/autocomplete-hop-fastpass.json')
        coords = []
        for d in p.response.docs:
            self.assertTrue(d.lat != 0.0)
            self.assertTrue(d.lon != 0.0)
            self.assertTrue(d.lon not in coords)
            self.assertTrue(d.lat not in coords)
            coords.append(d.lat)
            coords.append(d.lon)

    def test_stops(self):
        p = self.parse('./data/search13135.json')
        num_stops = 0
        for d in p.response.docs:
            if isinstance(d, SolrStopRecord):
                num_stops += 1
                self.assertTrue(len(d.stop_id) > 0)
                self.assertTrue(len(d.agency_id) > 0)
                # print d.stop_id
        self.assertTrue(num_stops > 0)

    def test_no_results(self):
        p = self.parse('./data/autocomplete_no_results.json')
        self.assertTrue(len(p.response.docs) == 0)

    def parse(self, file_name):
        file_path = file_utils.path_join(self.base_path, file_name)
        json = json_utils.file_to_json(file_path)
        p = PeliasToSolr.parse_json(json)
        return p
