import unittest
from pyramid import testing

import urllib
import contextlib
import json

PORT="44444"


class TestMyView(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_routes(self):
        url = get_url('routes')
        j = call_url(url)
        s = json.dumps(j)
        self.assertEqual(j['status_code'], 200)
        self.assertGreaterEqual(j['count'], 85)
        self.assertRegexpMatches(s,"MAX Blue")

    def test_route(self):
        url = get_url('route', 'route_id=100')
        j = call_url(url)
        s = json.dumps(j)
        self.assertEqual(j['status_code'], 200)
        self.assertRegexpMatches(s,"MAX Blue")

    def test_rs(self):
        def asserts(j, s):
            self.assertEqual(j['status_code'], 200)
            self.assertGreaterEqual(j['directions'][0]['stop_list']['count'], 45)
            self.assertRegexpMatches(s,"MAX Blue")
            self.assertRegexpMatches(s,"Hatfield Government")

        # both route directions
        url = get_url('route_stops', 'route_id=100')
        j = call_url(url)
        s = json.dumps(j)
        asserts(j, s)
        self.assertGreaterEqual(len(j['directions']), 2)

        # single route direction
        url = get_url('route_stops', 'route_id=100&direction_id=1')
        j = call_url(url)
        s = json.dumps(j)
        asserts(j, s)
        self.assertGreaterEqual(len(j['directions']), 1)

    def test_stop(self):
        url = get_url('stop', 'stop_id=2')
        j = call_url(url)
        s = json.dumps(j)
        self.assertEqual(j['status_code'], 200)
        self.assertRegexpMatches(s,"Lake Oswego")

    def test_stops_near(self):
        url = get_url('stops_near', 'lat=45.5&lon=-122.5')
        j = call_url(url)
        s = json.dumps(j)
        self.assertEqual(j['status_code'], 200)
        self.assertEqual(j['count'], 10)
        self.assertRegexpMatches(s,"SE Division")

    def test_stop_schedule(self):
        url = get_url('stop_schedule', 'stop_id=2')
        j = call_url(url)
        s = json.dumps(j)
        self.assertEqual(j['status_code'], 200)
        self.assertRegexpMatches(s,"Lake Oswego")

    def test_plan_trip(self):
        url = get_url('plan_trip', 'from=pdx::45.587546,-122.592925&to=zoo')
        j = call_url(url)
        s = json.dumps(j)
        self.assertRegexpMatches(s,"Zoo")
        self.assertRegexpMatches(s,"itineraries")

    def test_geocode(self):
        url = get_url('geocode', 'place=zoo')
        j = call_url(url)
        s = json.dumps(j)
        self.assertEqual(j['status_code'], 200)
        self.assertRegexpMatches(s,"-122.71")
        self.assertRegexpMatches(s,"45.51")


def get_url(svc_name, params=None):
    ret_val = "http://localhost:{0}/{1}".format(PORT, svc_name)
    if params:
        ret_val = "{0}?{1}".format(ret_val, params)
    return ret_val

def call_url(url):
    print url
    with contextlib.closing(urllib.urlopen(url)) as f:
        ret_json = json.load(f)
    return ret_json

def call_url_text(url):
    print url
    return urllib.urlopen(url).read()
