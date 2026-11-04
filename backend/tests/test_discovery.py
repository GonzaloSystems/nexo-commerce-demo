import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from nexo_data.discovery import RainforestClient,DiscoveryService,rainforest_item
from nexo_data.config import ConfigurationError
from nexo_data.transport import ProviderError

class FakeTransport:
 def __init__(self,data):self.data=data;self.calls=[]
 def request(self,*args):self.calls.append(args);return self.data

def fixture():return {'asin':'B000000001','title':'Synthetic only','price':{'value':1499,'currency':'MXN'},'image':'https://m.media-amazon.com/images/I/test.jpg','rating':4.5,'ratings_total':12,'position':1,'recent_sales':'100+ bought in past month','categories':[{'id':'123','name':'Test'}]}

class DiscoveryTests(unittest.TestCase):
 def test_mexico_and_no_automatic_extra_products_or_estimators(self):
  t=FakeTransport({'request_info':{'success':True},'request_parameters':{'amazon_domain':'amazon.com.mx'},'search_results':[fixture()]})
  r=RainforestClient({'RAINFOREST_API_KEY':'TEST_ONLY'},t).search('audio');u=t.calls[0][1]
  self.assertIn('amazon_domain=amazon.com.mx',u);self.assertIn('type=search',u);self.assertNotIn('include_products_count',u);self.assertIsNone(r['products'][0]['units_30d']);self.assertIsNone(r['products'][0]['revenue_30d']);self.assertEqual(r['products'][0]['ranks'],[])
 def test_usd_not_relabelled_as_pesos_and_search_position_not_bsr(self):
  f=fixture();f['price']['currency']='USD';r=rainforest_item(f,'2026-11-03T12:00:00Z');self.assertIsNone(r['price']);self.assertEqual(r['ranks'],[]);self.assertIsNone(r['units_30d'])
 def test_missing_credential_prevents_network_request(self):
  t=FakeTransport({})
  with self.assertRaises(ConfigurationError):RainforestClient({},t).search('audio')
  self.assertEqual(t.calls,[])
 def test_cache_deduplicates_and_budget_stops_more_queries(self):
  service=DiscoveryService(lambda:{'RAINFOREST_API_KEY':'TEST_ONLY'},limit=1);result={'products':[],'provider':'rainforest','cached':False}
  with patch('nexo_data.discovery.RainforestClient.search',return_value=result) as call:
   self.assertFalse(service.search('Audio')['cached']);self.assertTrue(service.search(' audio ')['cached']);self.assertEqual(call.call_count,1)
   with self.assertRaises(ProviderError):service.search('other')
 def test_failed_provider_response_not_claimed_as_data(self):
  with self.assertRaises(ProviderError):RainforestClient({'RAINFOREST_API_KEY':'TEST_ONLY'},FakeTransport({'request_info':{'success':False}})).search('audio')
 def test_cache_persists_public_results_without_api_key(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'cache.json';loader=lambda:{'RAINFOREST_API_KEY':'TEST_ONLY'}
   service=DiscoveryService(loader,cache_path=path)
   with patch('nexo_data.discovery.RainforestClient.search',return_value={'products':[],'provider':'rainforest','marketplace':'amazon.com.mx','cached':False}):service.search('audio')
   self.assertNotIn('TEST_ONLY',path.read_text());self.assertEqual(path.stat().st_mode&0o777,0o600)
   restored=DiscoveryService(loader,cache_path=path);self.assertTrue(restored.latest()['stored_snapshot'])
   with patch('nexo_data.discovery.RainforestClient.search') as call:self.assertTrue(restored.search('audio')['cached']);call.assert_not_called()
 def test_ten_letter_words_are_not_misclassified_as_asins(self):
  t=FakeTransport({'request_info':{'success':True},'search_results':[]});RainforestClient({'RAINFOREST_API_KEY':'TEST_ONLY'},t).search('aspiradora');self.assertIn('type=search',t.calls[0][1])
 def test_asin_queries_use_product_and_untrusted_images_are_rejected(self):
  f=fixture();f['image']='https://example.com/track';t=FakeTransport({'request_info':{'success':True},'product':f});r=RainforestClient({'RAINFOREST_API_KEY':'TEST_ONLY'},t).search('B000000001');self.assertIn('type=product',t.calls[0][1]);self.assertIsNone(r['products'][0]['image_url'])
if __name__=='__main__':unittest.main()
