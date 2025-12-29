from ott.utils.tests.base_unit import BaseUnit
from ott.utils import file_utils
import requests

PORT="45554"

class TestAgenciess(BaseUnit):
    def setUp(self):
        self.url_tmpl = f"http://localhost:{PORT}/pelias/autocomplete?text=2&layers="
        self.rtp_agencies = ["xx"]

    def tearDown(self):
        pass

    def test_autocomplete(self):        
        ret_val = True
        for r in self.rtp_agencies:
             l = f"{r}:stops"
             url = self.url_tmpl + r
             print(url)
             #self.assertTrue()
