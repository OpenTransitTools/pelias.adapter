from ott.utils.tests.base_unit import BaseUnit
from ott.utils.config_util import ConfigUtil
from ott.utils import json_utils

PORT="45554"

class TestAgenciess(BaseUnit):
    def setUp(self):
        #import pdb; pdb.set_trace()
        self.url_tmpl = f"http://localhost:{PORT}/pelias/autocomplete?text=a&layers="
        self.config = ConfigUtil.factory(section="app:main")
        self.rtp_agencies = self.config.get_typed('agencies')

    def tearDown(self):
        pass

    def test_expected_agencies_exist_in_pelias(self):
        """ make sure trimet:stops, ctran:stops, etc... """
        ret_val = True
        for a in self.rtp_agencies:
            #import pdb; pdb.set_trace()
            l = f"{a}:stops"
            url = self.url_tmpl + l
            jsn = json_utils.stream_json(url)
            errors = jsn.get('geocoding').get('errors')
            features = jsn.get('features')
            print(f"{url} - errors: {errors}\n")
            #print(f"     - features: {features}")
            self.assertTrue(jsn and errors is None and features is not None and len(features) > 0)
