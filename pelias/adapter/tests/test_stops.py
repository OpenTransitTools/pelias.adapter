from cProfile import run
from ott.utils.tests.base_unit import BaseUnit
from ott.utils import file_utils
from ott.utils import json_utils
from ott.utils import string_diff
import requests

PORT="45554"

class TestStops(BaseUnit):
    def setUp(self):
        self.url_tmpl = f"http://localhost:{PORT}/pelias/autocomplete?text="
        self.base_path = file_utils.get_file_dir(__file__)
        self.csv = self.csv('./data/stops.csv', "stop_code")

    def tearDown(self):
        pass

    def runz(self, url_tmpl, within=3):
        ret_val = True
        for c in self.csv:
            id = c.get("stop_code")
            url = url_tmpl + id
            res = requests.get(url).json()
            features = res.get('features')
            seen = False
            index = 0
            feat = None
            for i, f in enumerate(features):
                fid = f.get('properties').get('id')
                if fid and fid.startswith(id + '::'):
                    seen = True
                    index = i+1
                    feat = f.get('properties').get('id')
                    break

            if not seen:
                print("ERROR: {} not seen".format(id))
                ret_val = False
            elif index > within:
                print("WARN: {} seen in record {}".format(id, index))
            #else: 
                #print("INFO: {} seen in record {}".format(id, index, feat))
        return ret_val

    def test_dedupe(self):
        """ test that we get one record back """
        ret_val = True
        for s in ["101 SW Main", "834 SE Lamb", "834 SE Sandy", "1931 NE Sandy"]:
            url = self.url_tmpl + s
            jsn = json_utils.stream_json(url)
            errors = jsn.get('geocoding').get('errors')
            features = jsn.get('features')
            self.assertTrue(jsn and errors is None and len(features) is not None and len(features) == 1)

    def test_dedupe_distance(self):
        """
        test that we are not chewing up too many records based on (a too large) distance between points
        note: this test is more to generate logs/app.log content, to shows which stops are getting dedup'd
        cmdline: echo "" > logs/app.log; poetry run pytest pelias/adapter/tests/test_stops.py ; cat logs/app.log
        """
        ret_val = True
        for s in ["834 NE S", "834 NE Sha", "834 NE Ha"]:
            url = self.url_tmpl + s
            jsn = json_utils.stream_json(url)
            errors = jsn.get('geocoding').get('errors')
            features = jsn.get('features')
            self.assertTrue(jsn and errors is None and len(features) is not None and len(features) >= 1)

    def test_autocomplete(self):
        print("\n\nTODO - broken AUTOCOMPLETE test")
        return
        url_tmpl = "https://ws-st.trimet.org/pelias/v1/autocomplete?text="
        self.assertTrue(self.runz(url_tmpl))

    def test_search(self):
        print("\n\nTODO - broken SEARCH test")
        return
        url_tmpl = "https://ws-st.trimet.org/pelias/v1/search?text="
        self.assertTrue(self.runz(url_tmpl))
