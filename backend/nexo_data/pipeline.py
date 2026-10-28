from .config import load_credentials,readiness,ConfigurationError
from .providers import KeepaClient,SpApiClient,validate_asins
from .normalize import keepa_product,sp_product,utc_now,DataError
from .transport import ProviderError

def sync(store,asins,provider='auto',days=180,offers=0,credentials=None):
    asins=validate_asins(asins);values=load_credentials() if credentials is None else credentials
    ready=readiness(values)
    providers=[p for p in ['sp-api','keepa'] if ready[p]['configured']] if provider=='auto' else [provider]
    if not providers:raise ConfigurationError('No hay API configurada. Ejecuta doctor; no se han consultado productos.')
    report=[]
    for name in providers:
        if name not in ready or not ready[name]['configured']:raise ConfigurationError('Faltan credenciales de '+name)
        count=0;missing=[];stamp=utc_now()
        try:
            if name=='keepa':
                payload=KeepaClient(values).products(asins,days,offers)
                returned=set()
                for item in payload['products']:
                    if item.get('asin') not in asins:raise DataError('unexpected_asin_in_response')
                    record=keepa_product(item,stamp);store.save(record);count+=1;returned.add(record['asin'])
                missing=sorted(set(asins)-returned)
                meta={k:payload.get(k) for k in ['tokensLeft','tokensConsumed','refillRate','refillIn']}
                meta['missing_asins']=missing
            else:
                client=SpApiClient(values)
                for asin in asins:
                    bundle=client.product(asin,with_offers=True)
                    record=sp_product(bundle,utc_now())
                    if record['asin']!=asin:raise DataError('unexpected_asin_in_response')
                    store.save(record);count+=1
                meta={'missing_asins':missing}
            status='ok' if count else 'authenticated_no_products'
            store.record_run(name,status,count,meta)
            report.append({'provider':name,'status':status,'products':count,**meta})
        except ProviderError as exc:
            status={'provider':name,'status':exc.code,'http_status':exc.status,'retry_after':exc.retry_after,'products':count}
            store.record_run(name,exc.code,count,{'http_status':exc.status,'retry_after':exc.retry_after})
            report.append(status)
        except DataError as exc:
            store.record_run(name,'invalid_provider_data',count)
            report.append({'provider':name,'status':'invalid_provider_data','products':count})
    return {'queried_at':stamp,'results':report,'data_source':'provider_api'}
