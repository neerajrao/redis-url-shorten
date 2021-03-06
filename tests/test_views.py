import env
from unittest import TestCase, main
from os import path
import url_short.views as v
from url_short import app
import json
import redis

TESTDIR = path.dirname(path.realpath(__file__))

class UrlShortTestCase(TestCase):
    def setUp(self):
        v.r = redis.from_url('redis://localhost:6379/') # use a local redis-server for testing
        v.r.flushall() # clean up old test results
        self.app = app.test_client()

    def test_shorten_new_url(self):
        long_url = 'test'
        response = self.app.get('/shorten?url=%s' % long_url)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['long_url'], long_url)
        self.assertEqual(int(data['visits']), 0)
        self.assertTrue(data['short_url'])

    def test_shorten_existing_url(self):
        long_url = 'test'
        response = self.app.get('/shorten?url=%s' % long_url)
        data = json.loads(response.data)
        short_url = data['short_url']

        # try shortening the same url again. You should get back the
        # same short url as before
        response = self.app.get('/shorten?url=%s' % long_url)
        self.assertEqual(data['short_url'], short_url)
        self.assertTrue(data['success'])
        self.assertEqual(data['long_url'], long_url)
        self.assertEqual(int(data['visits']), 0)

    def test_shorten_short_url(self):
        response = self.app.get('/shorten?url=%s' % 'http://localhost/test')
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], app.config['MSG_ALREADY_SHORT_URL'])

    def test_invalid_details_request(self):
        response = self.app.get('/detail?url=test') # request param is 'id', not 'url'
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], app.config['MSG_ID_REQ_PARAM_MISSING'])

    def test_details_nonexistent_short_url(self):
        response = self.app.get('/detail?id=test')
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], app.config['MSG_UNKNOWN_SHORT_URL'])

    def test_details_existing_short_url(self):
        long_url = 'test'
        response = self.app.get('/shorten?url=%s' % long_url)
        data = json.loads(response.data)
        short_url_with_domain_name = data['short_url']
        short_url = short_url_with_domain_name[short_url_with_domain_name.rfind('/')+1:] # discard the domain name

        # try lengthening the same url again. You should get back the
        # original long url
        response = self.app.get('/detail?id=%s' % short_url)
        data = json.loads(response.data)
        self.assertEqual(data['short_url'], short_url_with_domain_name)
        self.assertEqual(data['id'], short_url)
        self.assertTrue(data['success'])
        self.assertEqual(data['long_url'], long_url)
        self.assertEqual(int(data['visits']), 1)

if __name__ == '__main__':
    main()
