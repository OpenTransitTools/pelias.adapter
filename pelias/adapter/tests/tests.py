import unittest
from pyramid import testing

import urllib
import contextlib
import json

PORT="45454"


class TestPeliasToSolr(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_pelias_to_solr(self):
        print "Hi"
        pass


    def ztest_solr(self):
        url = get_url('solr', 'limit=30&query=2')
        j = call_url(url)
        s = json.dumps(j)
        self.assertEqual(j['status_code'], 200)


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
