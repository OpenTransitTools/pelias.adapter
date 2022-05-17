from cProfile import run
from ott.utils.tests.base_unit import BaseUnit
from ott.utils import file_utils
import requests


class TestStops(BaseUnit):
    def setUp(self):
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
            for i, f in enumerate(features):
                fid = f.get('properties').get('id')
                if fid and fid.startswith(id + '::'):
                    seen = True
                    index = i+1
                    break

            if not seen:
                print("ERROR: {} not seen".format(id))
                ret_val = False
            elif index > within:
                print("WARN: {} seen in record {}".format(id, index))
        
        return ret_val

    def test_autocomplete(self):
        url_tmpl = "https://ws-st.trimet.org/pelias/v1/autocomplete?text="
        self.assertTrue(self.runz(url_tmpl))

    def test_search(self):
        url_tmpl = "https://ws-st.trimet.org/pelias/v1/search?text="
        self.assertTrue(self.runz(url_tmpl))
