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

    def test_wrapp_alias(self):
        csv = self.csv('./data/alias.csv', "NAME")
        for c in csv:
            n = c.get("NAME")
            url = self.url_tmpl + n
            self.call_test(url, has_attribute="features")