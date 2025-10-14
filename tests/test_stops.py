import requests
from ott.utils import file_utils
from ott.utils.tests.base_unit import BaseUnit


class TestStops(BaseUnit):
    def setUp(self):
        self.base_path = file_utils.get_file_dir(__file__)
        self.csv = self.csv("data/stops.csv", "stop_code")

    def tearDown(self):
        pass

    def runz(self, url_tmpl, within=3):
        ret_val = True
        for c in self.csv:
            stop_id = c.get("stop_code")
            url = url_tmpl + stop_id
            res = requests.get(url).json()
            features = res.get("features")
            seen = False
            index = 0
            # feat = None
            expected_id = f"stops:TRIMET:{stop_id}"
            for i, feature in enumerate(features):
                fid = feature.get("properties").get("id")
                if fid and fid == expected_id:
                    seen = True
                    index = i + 1
                    # feat = feature.get("properties").get("id")
                    break

            if not seen:
                print("ERROR: {} not seen".format(stop_id))
                ret_val = False
            elif index > within:
                print("WARN: {} seen in record {}".format(stop_id, index))
            # else:
            # print("INFO: {} seen in record {}".format(id, index, feat))
        return ret_val

    def test_autocomplete(self):
        print("\n\nAUTOCOMPLETE:")
        url_tmpl = "https://ws-st.trimet.org/pelias/v1/autocomplete?text="
        self.assertTrue(self.runz(url_tmpl))

    def test_search(self):
        print("\n\nSEARCH:")
        url_tmpl = "https://ws-st.trimet.org/pelias/v1/search?text="
        self.assertTrue(self.runz(url_tmpl))
