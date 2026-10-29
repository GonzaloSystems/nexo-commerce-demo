import json
import re
import time
from urllib.parse import urlencode
from .config import ConfigurationError
from .transport import ProviderError, Transport

MARKETPLACE_MX = 'A1AM78C64UM0Y8'
ASIN_RE = re.compile(r'^[A-Z0-9]{10}$')

def validate_asins(asins):
    asins = list(dict.fromkeys(asins))
    if not asins or len(asins)>100 or any(not ASIN_RE.fullmatch(a) for a in asins):
        raise ConfigurationError('Indica de 1 a 100 ASIN válidos, con diez letras o números.')
    return asins

class KeepaClient:
    def __init__(self, credentials, transport=None):
        self.key = credentials.get('KEEPA_API_KEY','')
        self.transport = transport or Transport()

    def products(self, asins, days=180, offers=0):
        if not self.key:
            raise ConfigurationError('Falta KEEPA_API_KEY. No se ha realizado una petición autenticada.')
        asins=validate_asins(asins)
        if not 1<=days<=3650 or offers not in (0,20,40,60,80,100):
            raise ConfigurationError('Días u ofertas fuera del rango admitido.')
        # Plain product history is the default. Do not incur optional offer,
        # stock or Buy Box costs unless the operator explicitly requests them.
        params = {'key':self.key,'domain':11,'asin':','.join(asins),'history':1,'days':days,'stats':days}
        if offers:
            params['offers']=offers
        data = self.transport.request('GET','https://api.keepa.com/product?'+urlencode(params))
        if data.get('error'):
            raise ProviderError('provider_rejected_request')
        if not isinstance(data.get('products'),list):
            raise ProviderError('missing_products')
        return data

class SpApiClient:
    def __init__(self, credentials, transport=None, sleeper=time.sleep):
        self.credentials = credentials
        self.transport = transport or Transport()
        self.sleeper = sleeper
        self.token = None
        self.expires = 0

    def access_token(self):
        if self.token and time.monotonic()<self.expires:
            return self.token
        keys=('SP_API_CLIENT_ID','SP_API_CLIENT_SECRET','SP_API_REFRESH_TOKEN')
        if not all(self.credentials.get(k) for k in keys):
            raise ConfigurationError('Faltan credenciales SP-API de la aplicación y su autorización de vendedor.')
        form=urlencode({'grant_type':'refresh_token','client_id':self.credentials[keys[0]],
                        'client_secret':self.credentials[keys[1]],'refresh_token':self.credentials[keys[2]]}).encode()
        data=self.transport.request('POST','https://api.amazon.com/auth/o2/token',
                                    {'Content-Type':'application/x-www-form-urlencoded'},form)
        if not isinstance(data.get('access_token'),str):
            raise ProviderError('token_not_returned')
        self.token=data['access_token']
        self.expires=time.monotonic()+max(0,int(data.get('expires_in',3600))-60)
        return self.token

    def search(self, keywords=None, identifiers=None, classification_ids=None, brand_names=None, page_token=None, page_size=20):
        """One official catalog page. No price/BSR-range server filter is invented."""
        identifiers=list(identifiers or []);keywords=list(keywords or [])
        if bool(identifiers)==bool(keywords):
            raise ConfigurationError('Indica palabras clave o ASIN, en consultas separadas.')
        if not 1<=page_size<=20 or len(keywords)>20 or any(not isinstance(k,str) or not k.strip() or len(k)>200 for k in keywords):
            raise ConfigurationError('Máximo 20 palabras clave y 20 resultados por página.')
        if identifiers:
            identifiers=validate_asins(identifiers)
            if len(identifiers)>20 or classification_ids or brand_names:
                raise ConfigurationError('Hasta 20 ASIN por búsqueda; categoría y marca solo con palabras clave.')
        if classification_ids and any(not str(c).isdigit() for c in classification_ids):
            raise ConfigurationError('La categoría de Amazon debe indicarse mediante su identificador numérico.')
        if brand_names and any(not isinstance(b,str) or not b.strip() or len(b)>200 for b in brand_names):
            raise ConfigurationError('Marca de búsqueda no válida.')
        if page_token and (not isinstance(page_token,str) or len(page_token)>4096):
            raise ConfigurationError('Token de página no válido.')
        params={'marketplaceIds':MARKETPLACE_MX,'includedData':'summaries,images,classifications,relationships,salesRanks','pageSize':page_size}
        if identifiers:params.update(identifiers=','.join(identifiers),identifiersType='ASIN')
        else:
            params['keywords']=','.join(keywords)
            if classification_ids:params['classificationIds']=','.join(map(str,classification_ids))
            if brand_names:params['brandNames']=','.join(brand_names)
        if page_token:params['pageToken']=page_token
        data=self.transport.request('GET','https://sellingpartnerapi-na.amazon.com/catalog/2022-04-01/items?'+urlencode(params),{'x-amz-access-token':self.access_token()})
        if not isinstance(data.get('items'),list):raise ProviderError('missing_catalog_items')
        return data

    def product(self, asin, with_offers=True):
        validate_asins([asin])
        headers={'x-amz-access-token':self.access_token()}
        q=urlencode({'marketplaceIds':MARKETPLACE_MX,'includedData':'summaries,images,classifications,relationships,salesRanks'})
        item=self.transport.request('GET',f'https://sellingpartnerapi-na.amazon.com/catalog/2022-04-01/items/{asin}?{q}',headers)
        offers=None
        pricing_status='not_requested'
        if with_offers:
            # Separate Pricing role may be absent; preserve a successful catalog
            # response without claiming that a denied offer query succeeded.
            self.sleeper(2.1)
            q=urlencode({'MarketplaceId':MARKETPLACE_MX,'ItemCondition':'New','CustomerType':'Consumer'})
            try:
                offers=self.transport.request('GET',f'https://sellingpartnerapi-na.amazon.com/products/pricing/v0/items/{asin}/offers?{q}',headers)
                pricing_status='received'
            except ProviderError as exc:
                pricing_status=f'{exc.code}:{exc.status or "unknown"}'
        return {'catalog':item,'offers':offers,'pricing_status':pricing_status}
