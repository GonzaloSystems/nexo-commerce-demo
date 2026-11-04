"""On-demand Amazon discovery for the local pilot; no browser collection."""
import re,time,threading,json,os
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from .providers import ASIN_RE,SpApiClient
from .normalize import number,utc_now,sp_product
from .transport import Transport,ProviderError
from .config import load_credentials,ConfigurationError

AMAZON_MX='amazon.com.mx'
def is_asin_query(value):return bool(re.fullmatch(r'(?:B0[A-Z0-9]{8}|[0-9]{9}[0-9X])',value.upper()))
def image_url(value):
    if not isinstance(value,str):return None
    p=urlsplit(value)
    return value if p.scheme=='https' and p.hostname in ('m.media-amazon.com','images-na.ssl-images-amazon.com','images-eu.ssl-images-amazon.com') else None

def rainforest_item(p,queried_at,detail=False):
    asin=p.get('asin')
    if not isinstance(asin,str) or not ASIN_RE.fullmatch(asin):raise ValueError('invalid_asin')
    offer=(p.get('buybox_winner') or {}) if detail else {}
    price=offer.get('price') or p.get('price') or {}
    if not isinstance(price,dict):price={}
    amount=number(price.get('value')) if price.get('currency')=='MXN' else None
    if amount is not None and amount<0:amount=None
    ranks=p.get('bestsellers_rank') or []
    if isinstance(ranks,dict):ranks=[ranks]
    ranks=[{'rank':int(number(r['rank'])),'category':str(r.get('category',''))} for r in ranks if isinstance(r,dict) and number(r.get('rank')) is not None and number(r['rank'])>0]
    cats=[{'id':str(c.get('id','')),'name':str(c.get('name',''))} for c in p.get('categories',[]) if isinstance(c,dict)]
    main=p.get('main_image') or {}
    photo=image_url(main.get('link') if isinstance(main,dict) else None) or image_url(p.get('image'))
    rating=number(p.get('rating'));reviews=number(p.get('ratings_total'))
    if rating is not None and not 0<=rating<=5:rating=None
    if reviews is not None and reviews<0:reviews=None
    return {'asin':asin,'title':str(p.get('title') or asin)[:1000],'brand':p.get('brand') if isinstance(p.get('brand'),str) else None,
            'url':'https://www.amazon.com.mx/dp/'+asin,'image_url':photo,'currency':'MXN','price':amount,
            'rating':rating,'reviews':int(reviews) if reviews is not None else None,'categories':cats,
            'ranks':ranks,'parent_asin':p.get('parent_asin'),'provider':'rainforest','marketplace':'amazon.com.mx',
            'data_kind':'product' if detail else 'search','rating_distribution':distribution(p.get('rating_breakdown')),'monthly_units_min':monthly_threshold(p.get('recent_sales')),'seller':None,'queried_at':queried_at,'units_30d':None,'revenue_30d':None,'sales_status':'not_estimated',
            'recent_sales_public_text':str(p.get('recent_sales') or '')[:200] or None,
            'sponsored':p.get('sponsored') is True,'availability':str((p.get('availability') or offer.get('availability') or {}).get('raw') or '')[:300] or None}

def monthly_threshold(text):
    if not isinstance(text,str):return None
    match=re.search(r'(\d+(?:[.,]\d+)?)\s*(mil|k)?\s*\+',text.casefold())
    if not match:return None
    value=float(match[1].replace(',','.'))*(1000 if match[2] else 1)
    return int(value) if value>0 else None

def distribution(value):
    result=[]
    for stars,key in [(5,'five_star'),(4,'four_star'),(3,'three_star'),(2,'two_star'),(1,'one_star')]:
        row=(value or {}).get(key) or {};pct=number(row.get('percentage'));count=number(row.get('count'))
        if pct is not None and 0<=pct<=100:result.append({'stars':stars,'percentage':pct,'count':int(count) if count is not None and count>=0 else None})
    return result

class RainforestClient:
    def __init__(self,credentials,transport=None):self.key=credentials.get('RAINFOREST_API_KEY');self.transport=transport or Transport(retries=0,timeout=45)
    def search(self,query):
        query=query.strip()
        if not query or len(query)>200:raise ConfigurationError('Escribe un producto o ASIN, con hasta 200 caracteres.')
        if not self.key:raise ConfigurationError('Falta la clave Rainforest API; no se ha consultado Amazon.')
        is_asin=is_asin_query(query)
        params={'api_key':self.key,'type':'product' if is_asin else 'search','amazon_domain':AMAZON_MX,'currency':'MXN'}
        params['asin' if is_asin else 'search_term']=query.upper() if is_asin else query
        # Never request include_products_count, estimation or other paid extras.
        data=self.transport.request('GET','https://api.rainforestapi.com/request?'+urlencode(params))
        info=data.get('request_info') or {}
        if info.get('success') is not True:raise ProviderError('provider_rejected_request')
        echoed=data.get('request_parameters') or {}
        if echoed.get('amazon_domain') not in (None,AMAZON_MX):raise ProviderError('wrong_marketplace')
        items=[data['product']] if is_asin and isinstance(data.get('product'),dict) else data.get('search_results',[])
        if not isinstance(items,list):raise ProviderError('invalid_product_results')
        products=[];stamp=utc_now();seen=set()
        for p in items[:50]:
            try:r=rainforest_item(p,stamp,is_asin)
            except (ValueError,TypeError,KeyError):continue
            if r['asin'] not in seen:products.append(r);seen.add(r['asin'])
        return {'provider':'rainforest','products':products,'queried_at':stamp,'marketplace':'amazon.com.mx',
                'credits_remaining':info.get('credits_remaining'),'credits_used_this_request':info.get('credits_used_this_request'),
                'data_kind':'product' if is_asin else 'search','cached':False,'sales_note':'Señales públicas; las ventas e ingresos del modelo siguen pendientes de calibración.'}

    def offers(self,asin):
        if not ASIN_RE.fullmatch(asin):raise ConfigurationError('ASIN no válido.')
        if not self.key:raise ConfigurationError('Falta Rainforest API.')
        data=self.transport.request('GET','https://api.rainforestapi.com/request?'+urlencode({'api_key':self.key,'type':'offers','amazon_domain':AMAZON_MX,'currency':'MXN','asin':asin,'offers_condition_new':'true'}))
        info=data.get('request_info') or {}
        if info.get('success') is not True:raise ProviderError('provider_rejected_request')
        offers=[]
        for row in data.get('offers',[])[:30]:
            seller=row.get('seller') or {};price=row.get('price') or {};n=number(price.get('value')) if price.get('currency')=='MXN' else None
            offers.append({'seller_id':seller.get('id'),'seller_name':str(seller.get('name') or 'Vendedor no indicado')[:200],'price':n if n is not None and n>=0 else None,'condition':str((row.get('condition') or {}).get('title') or '')[:100]})
        return {'data_kind':'offers','asin':asin,'marketplace':AMAZON_MX,'provider':'rainforest','queried_at':utc_now(),'offers':offers,'cached':False,'credits_remaining':info.get('credits_remaining')}

class DiscoveryService:
    def __init__(self,credential_loader=load_credentials,limit=20,cache_path=None):
        self.load=credential_loader;self.limit=limit;self.used=0;self.cache={};self.lock=threading.Lock();self.cache_path=Path(cache_path) if cache_path else None
        if self.cache_path and self.cache_path.exists() and not self.cache_path.is_symlink():
            try:
                if self.cache_path.stat().st_size<=4*1024*1024 and not self.cache_path.stat().st_mode&0o077:
                    for entry in json.loads(self.cache_path.read_text()):
                        key=entry['key'];result=entry['result']
                        if len(key)==2 and key[0] in ('sp-api','rainforest') and result.get('marketplace')=='amazon.com.mx' and (isinstance(result.get('products'),list) or isinstance(result.get('offers'),list)):self.cache[tuple(key)]=(float(entry['saved_at']),result)
            except (ValueError,KeyError,TypeError,OSError):self.cache={}
    def enrich(self,result):
        if not isinstance(result.get('products'),list):return result
        products=[]
        for p in result['products']:
            candidates=[row for _,r in self.cache.values() for row in r.get('products',[]) if row.get('asin')==p.get('asin') and row.get('data_kind')=='product']
            detailed=max(candidates,key=lambda row:row['queried_at']) if candidates else None
            merged={**p,**detailed,'sponsored':p.get('sponsored',False)} if detailed else dict(p)
            offer_cache=self.cache.get(('rainforest','offers:'+p.get('asin','')))
            if offer_cache:merged['seller_names']=sorted(set(o['seller_name'] for o in offer_cache[1].get('offers',[])))
            products.append(merged)
        return {**result,'products':products}

    def latest(self):
        with self.lock:
            if not self.cache:return None
            candidates=[pair for pair in self.cache.values() if pair[1].get('data_kind') not in ('product','offers') and isinstance(pair[1].get('products'),list)]
            stamp,result=max(candidates or [pair for pair in self.cache.values() if 'products' in pair[1]],key=lambda pair:pair[0])
            return {**self.enrich(result),'cached':True,'stored_snapshot':True}
    def persist(self):
        if not self.cache_path:return
        try:
            self.cache_path.parent.mkdir(exist_ok=True,parents=True,mode=0o700)
            entries=[{'key':list(key),'saved_at':stamp,'result':result} for key,(stamp,result) in sorted(self.cache.items(),key=lambda item:item[1][0])[-20:]]
            temp=self.cache_path.with_suffix('.tmp');fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|getattr(os,'O_NOFOLLOW',0),0o600)
            with os.fdopen(fd,'w') as f:os.fchmod(f.fileno(),0o600);json.dump(entries,f,ensure_ascii=False)
            os.replace(temp,self.cache_path)
        except OSError:pass  # Preserve a successful provider response even if a local cache write fails.
    def cached_product(self,asin):
        with self.lock:
            rows=[p for _,r in self.cache.values() for p in r.get('products',[]) if p.get('asin')==asin and p.get('data_kind')=='product']
            return max(rows,key=lambda p:p['queried_at']) if rows else None

    def offers(self,asin):
        if not isinstance(asin,str) or not ASIN_RE.fullmatch(asin):raise ConfigurationError('ASIN no válido.')
        with self.lock:
            key=('rainforest','offers:'+asin);cached=self.cache.get(key)
            if cached and time.time()-cached[0]<1800:return {**cached[1],'cached':True}
            if not self.load().get('RAINFOREST_API_KEY'):raise ConfigurationError('Consulta de vendedores disponible con Rainforest API.')
            if self.used>=self.limit:raise ProviderError('local_request_budget_reached',429)
            self.used+=1;data=RainforestClient(self.load()).offers(asin);self.cache[key]=(time.time(),data);self.persist();return data

    def detail(self,asin,catalog_path=None):
        if not isinstance(asin,str) or not ASIN_RE.fullmatch(asin):raise ConfigurationError('ASIN no válido.')
        data=self.search(asin)
        product=next((p for p in data['products'] if p['asin']==asin),None)
        if not product:raise ProviderError('product_not_returned')
        product=dict(product);offer_cache=self.cache.get(('rainforest','offers:'+asin));offer_data=offer_cache[1] if offer_cache else None
        product['seller_names']=sorted(set(r['seller_name'] for r in offer_data['offers'])) if offer_data else []
        observations=[]
        if catalog_path:
            try:
                catalog=json.loads(Path(catalog_path).read_text())
                for row in catalog['products']:
                    m=row.get('markets',{}).get('amazon',{})
                    if m.get('id')==asin:observations.append({'at':m['priceDate'],'price':m.get('price'),'rank':m.get('bsr'),'category':m.get('rankCategory'),'source':'catálogo observado'})
            except (OSError,ValueError,KeyError):pass
        seen=set()
        for _,cached in self.cache.values():
            for p in cached.get('products',[]):
                if p.get('asin')==asin and p.get('queried_at') not in seen:
                    seen.add(p.get('queried_at'));observations.append({'at':p['queried_at'],'price':p.get('price'),'rank':(p.get('ranks') or [{}])[0].get('rank'),'category':(p.get('ranks') or [{}])[0].get('category'),'source':p['provider']})
        return {**data,'product':product,'offers':offer_data,'observations':sorted(observations,key=lambda r:r['at']),'history_note':'Observaciones disponibles; no historial diario completo.'}

    def status(self):
        c=self.load();provider='sp-api' if all(c.get(k) for k in ['SP_API_CLIENT_ID','SP_API_CLIENT_SECRET','SP_API_REFRESH_TOKEN']) else 'rainforest' if c.get('RAINFOREST_API_KEY') else None
        return {'configured':provider is not None,'provider':provider,'requests_this_start':self.used,'request_limit_this_start':self.limit}
    def search(self,query):
        if not isinstance(query,str) or not query.strip() or len(query)>200:raise ConfigurationError('Escribe un producto o ASIN, con hasta 200 caracteres.')
        with self.lock:
            status=self.status();provider=status['provider']
            if not provider:raise ConfigurationError('Conecta Rainforest API o autoriza SP-API para buscar productos nuevos.')
            key=(provider,query.strip().casefold());cached=self.cache.get(key)
            if cached and time.time()-cached[0]<1800:return {**self.enrich(cached[1]),'cached':True}
            if self.used>=self.limit:raise ProviderError('local_request_budget_reached',429)
            self.used+=1;c=self.load()
            if provider=='rainforest':result=RainforestClient(c).search(query)
            else:
                client=SpApiClient(c);q=query.strip();stamp=utc_now()
                if is_asin_query(q):items=[client.product(q.upper(),with_offers=False)['catalog']]
                else:items=client.search(keywords=[q])['items']
                products=[]
                for item in items:
                    r=sp_product({'catalog':item,'pricing_status':'not_requested'},stamp)
                    products.append({'asin':r['asin'],'title':r['title'] or r['asin'],'brand':r['brand'],'url':'https://www.amazon.com.mx/dp/'+r['asin'],
                                     'image_url':image_url(r['image_url']),'currency':'MXN','price':r['price_current'],'rating':None,'reviews':None,
                                     'categories':r['category_tree'],'ranks':[{'rank':r['rank_current'],'category':r['rank_category_name']}] if r['rank_current'] else [],
                                     'parent_asin':r['parent_asin'],'provider':'sp-api','marketplace':'amazon.com.mx','queried_at':stamp,
                                     'units_30d':None,'revenue_30d':None,'sales_status':'not_estimated','sponsored':False})
                result={'provider':'sp-api','products':products,'queried_at':stamp,'cached':False,'marketplace':'amazon.com.mx','sales_note':'Catálogo oficial; precios, reseñas y ventas pueden no estar disponibles en esta consulta.'}
            self.cache[key]=(time.time(),result);self.persist();return self.enrich(result)
