from ott.utils.tests.base_unit import BaseUnit

from pelias.adapter.control.pelias_to_solr import PeliasToSolr
from pelias.adapter.model.solr.solr_stop_record import SolrStopRecord

PORT="45454"


class TestStringsCrash(BaseUnit):
    def setUp(self):
        super(TestStringsCrash, self).setUp()
        self.url_tmpl = "http://localhost:{}/pelias?text=".format(PORT)

    def tearDown(self):
        pass

    def test_landmarks(self):
        csv = self.csv('./data/landmarks.csv', "name")
        for c in csv:
            # import pdb; pdb.set_trace()
            url = self.url_tmpl + c.get("name")
            res = self.call_test_json(url, find_attribute="features")
            self.assertTrue(res)

    def xtest_alias(self):
        csv = self.csv('./data/alias.csv', "NAME")
        for c in csv:
            url = self.url_tmpl + c.get("NAME")
            res = self.call_test_json(url, find_attribute="features")
            self.assertTrue(res)

