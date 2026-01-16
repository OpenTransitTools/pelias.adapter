from ott.utils.tests.base_unit import BaseUnit
from ott.utils.config_util import ConfigUtil
from ott.utils import json_utils

PORT="45554"

class TestReverseGeocoder(BaseUnit):
    """ https://ws.trimet.org/peliaswrap/v1/reverse?layers=address&sources=openstreetmap&point.lat=45.62&point.lon=-122.17 """
    def setUp(self):
        self.url_tmpl = f"http://localhost:{PORT}/pelias/reverse"

    def tearDown(self):
        pass

    def xtest_specified_source(self):
        """ test reverse by specifying the OA souce, which should return feature using just the OA source """
        coords = [{'x':-122.27, 'y':45.62}, {'x':-122.5, 'y':45.5}]
        for c in coords:
            url = f"{self.url_tmpl}?sources=openaddresses&point.lat={c['y']}&point.lon={c['x']}"
            jsn = json_utils.stream_json(url)
            errors = jsn.get('geocoding').get('errors')
            features = jsn.get('features')
            self.assertTrue(jsn and errors is None)
            self.assertTrue(len(features) > 0)
            for f in features:
                #import pdb; pdb.set_trace()
                s = f.get('properties').get('source')
                self.assertTrue(s == 'openaddresses')

    def xtest_reverse_svc(self):
        """ test reverse, which should return a feature using the (default) OSM source """
        coords = [{'x':-122.17, 'y':45.62}, {'x':-122.5, 'y':45.5}]
        for c in coords:
            #import pdb; pdb.set_trace()
            url = f"{self.url_tmpl}?layers=address&point.lat={c['y']}&point.lon={c['x']}"
            jsn = json_utils.stream_json(url)
            errors = jsn.get('geocoding').get('errors')
            features = jsn.get('features')
            sources = jsn['geocoding']['query'].get('sources')
            self.assertTrue(jsn and errors is None) 
            self.assertTrue(len(features) > 0)
            self.assertTrue(len(sources) == 1 and sources[0] == 'openstreetmap')
            for f in features:
                s = f.get('properties').get('source')
                self.assertTrue(s == 'openstreetmap')

    def test_fallback_sources(self):
        """ test fallback doesn't call the geocoder """
        coords = [{'x':-1.17, 'y':4.62}, {'x':-1.5, 'y':4.5}]
        for c in coords:
            url = f"{self.url_tmpl}?layers=address&point.lat={c['y']}&point.lon={c['x']}"
            jsn = json_utils.stream_json(url)
            sources = jsn['geocoding']['query'].get('sources')
            features = jsn.get('features')
            self.assertTrue(sources is None)
            self.assertTrue(len(features) < 1)
