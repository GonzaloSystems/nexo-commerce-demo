"""Synthetic fixtures; these tests do not validate real API access or commercial accuracy."""
import io,json,tempfile,unittest,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from nexo_data.config import load_credentials,save_credentials,readiness,ConfigurationError
from nexo_data.providers import KeepaClient,SpApiClient,MARKETPLACE_MX
from nexo_data.normalize import keepa_product,sp_product,pairs,KEEPA_EPOCH,DataError
from nexo_data.storage import Store
from nexo_data.history import weighted_feature,period_features
from nexo_data.transport import Transport,ProviderError

def fixture():
 t=int((datetime(2026,9,1,tzinfo=timezone.utc)-KEEPA_EPOCH).total_seconds()/60);csv=[None]*12;current=[-1]*12
 csv[0]=[t,10000,t+720,-1];csv[1]=[t,9000,t+720,9500];csv[3]=[t,100,t+720,400];csv[11]=[t,4];current[1]=9500;current[3]=400;current[11]=4
 return {'asin':'B000000001','domainId':11,'title':'Synthetic fixture only','parentAsin':'B000000002','lastUpdate':t+720,'salesRankReference':123,'categoryTree':[{'catId':123,'name':'Test category'}],'csv':csv,'stats':{'current':current},'salesRanks':{'123':[t,100,t+720,400]},'monthlySold':100,'lastSoldUpdate':t+720,'monthlySoldHistory':[t,50,t+720,100]}
class FakeTransport:
 def __init__(self,responses):self.responses=list(responses);self.calls=[]
 def request(self,*args):self.calls.append(args);return self.responses.pop(0)
class DataTests(unittest.TestCase):
 def test_keepa_currency_identity_history_and_threshold(self):
  p=keepa_product(fixture());self.assertEqual(p['price_current'],95);self.assertEqual(p['rank_current'],400);self.assertEqual(p['parent_asin'],'B000000002');self.assertEqual(p['monthly_units_min'],100);self.assertIsNone(p['actual_competitor_sales']);self.assertEqual(p['rank_category_id'],'123');self.assertIsNone(p['price_history']['amazon'][-1]['value'])
 def test_negative_and_missing_do_not_turn_into_zero_or_stale_positive_price(self):
  f=fixture();f['stats']['current'][0]=-1;f['stats']['current'][1]=-1;f['monthlySold']=-1;p=keepa_product(f);self.assertIsNone(p['price_current']);self.assertIsNone(p['monthly_units_min']);self.assertIsNone(keepa_product({'asin':'B000000001','domainId':11})['rank_current'])
 def test_wrong_marketplace_and_malformed_history(self):
  f=fixture();f['domainId']=1
  with self.assertRaises(DataError):keepa_product(f)
  with self.assertRaises(DataError):pairs([10,20,30])
 def test_category_switch_is_not_a_stable_history(self):
  f=fixture();f['salesRanks']={};f['salesRankReferenceHistory']=[1234,999];p=keepa_product(f);self.assertEqual(p['rank_history_by_category'],{});self.assertIn('rank_reference_changed_csv3_not_used_for_history',p['quality_warnings'])
 def test_sibling_variants_not_mislabeled_as_children(self):
  f=fixture();f['variations']=[{'asin':'B000000003'}];self.assertEqual(keepa_product(f)['child_asins'],[]);f['parentAsin']=f['asin'];self.assertEqual(keepa_product(f)['child_asins'],['B000000003'])
 def test_keepa_requests_mexico_history_without_optional_costs(self):
  t=FakeTransport([{'products':[]}]);KeepaClient({'KEEPA_API_KEY':'TEST_ONLY'},t).products(['B000000001']);url=t.calls[0][1];self.assertIn('domain=11',url);self.assertIn('history=1',url);self.assertNotIn('offers=',url);self.assertNotIn('stock=',url)
 def test_missing_credentials_issue_no_calls(self):
  t=FakeTransport([])
  with self.assertRaises(ConfigurationError):KeepaClient({},t).products(['B000000001'])
  with self.assertRaises(ConfigurationError):SpApiClient({},t).product('B000000001')
  self.assertEqual(t.calls,[])
 def test_sp_token_reused_and_only_catalog_reads_after_token(self):
  t=FakeTransport([{'access_token':'TEST_TOKEN','expires_in':3600},{'asin':'B000000001'},{'asin':'B000000001'}]);c=SpApiClient({'SP_API_CLIENT_ID':'TEST_ID','SP_API_CLIENT_SECRET':'TEST_SECRET','SP_API_REFRESH_TOKEN':'TEST_REFRESH'},t,sleeper=lambda _:None);c.product('B000000001',False);c.product('B000000001',False);self.assertEqual([x[0] for x in t.calls],['POST','GET','GET']);self.assertIn('marketplaceIds='+MARKETPLACE_MX,t.calls[1][1]);self.assertNotIn('TEST_SECRET',t.calls[1][1])
 def test_offer_count_not_claimed_as_unique_seller_total(self):
  b={'catalog':{'asin':'B000000001'},'offers':{'payload':{'ASIN':'B000000001','marketplaceId':MARKETPLACE_MX,'Summary':{'TotalOfferCount':8,'NumberOfOffers':[{'condition':'new','fulfillmentChannel':'Amazon','OfferCount':3},{'condition':'new','fulfillmentChannel':'Merchant','OfferCount':4}],'BuyBoxPrices':[{'condition':'New','LandedPrice':{'CurrencyCode':'MXN','Amount':123.45}}]},'Offers':[{'SellerId':'TEST_A'},{'SellerId':'TEST_A'},{'SellerId':'TEST_B'}]}},'pricing_status':'received'};p=sp_product(b);self.assertEqual(p['price_current'],123.45);self.assertEqual(p['offer_count_total'],8);self.assertEqual(p['new_offer_count'],7);self.assertEqual(p['seller_count_observed'],2);self.assertIn('not_total',p['seller_count_scope']);self.assertIsNone(p['actual_competitor_sales'])
 def test_sqlite_deduplicates_events_and_separates_categories(self):
  with tempfile.TemporaryDirectory() as td:
   s=Store(Path(td)/'test.sqlite3');r=keepa_product(fixture(),'2026-09-02T00:00:00+00:00');s.save(r);s.save(r);self.assertEqual(len(s.history(r['asin'],'rank','123')),2);self.assertEqual(s.history(r['asin'],'rank','999'),[]);self.assertEqual(len(s.products()),1)
 def test_weighted_geomean_and_missing_coverage(self):
  es=[{'at':'2026-09-01T00:00:00+00:00','value':100,'state':'observed'},{'at':'2026-09-01T12:00:00+00:00','value':400,'state':'observed'}];r=weighted_feature(es,'2026-09-01','2026-09-02',True);self.assertAlmostEqual(r['value'],200);self.assertEqual(r['coverage'],1);es[1]['value']=None;es[1]['state']='unavailable_or_unknown';self.assertEqual(weighted_feature(es,'2026-09-01','2026-09-02',True)['coverage'],.5)
 def test_stale_signal_not_filled_over_month_or_marked_training_ready(self):
  with tempfile.TemporaryDirectory() as td:
   s=Store(Path(td)/'test.sqlite3');s.save(keepa_product(fixture()));r=period_features(s,'B000000001','123','2026-09-01','2026-09-30');self.assertIsNone(r['bsr_geomean']);self.assertFalse(r['training_ready']);self.assertIsNone(r['units_30d'])
 def test_private_permissions_and_status_not_secret(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'private/credentials.json';save_credentials({'KEEPA_API_KEY':'TEST_ONLY'},p);self.assertEqual(p.stat().st_mode&0o777,0o600);self.assertNotIn('TEST_ONLY',json.dumps(readiness(load_credentials(p))));p.chmod(0o644)
   with self.assertRaises(ConfigurationError):load_credentials(p)
 def test_provider_error_redacts_key_and_body(self):
  class Opener:
   def open(self,req,timeout):raise urllib.error.HTTPError(req.full_url,403,'Forbidden',{},io.BytesIO(b'{"secret":"TEST_SECRET"}'))
  with self.assertRaises(ProviderError) as c:Transport(opener=Opener(),retries=0).request('GET','https://api.keepa.com/product?key=TEST_SECRET')
  self.assertNotIn('TEST_SECRET',str(c.exception));self.assertEqual(c.exception.status,403)
 def test_other_host_rejected(self):
  with self.assertRaises(ProviderError):Transport().request('GET','https://example.com/product?key=TEST_ONLY')
if __name__=='__main__':unittest.main()
