import argparse,getpass,json,sys
from pathlib import Path
from urllib.parse import urlencode
from .config import ROOT,PROVIDER_KEYS,load_credentials,save_credentials,readiness,ConfigurationError
from .transport import Transport,ProviderError
from .providers import MARKETPLACE_MX
from .storage import Store
from .pipeline import sync
from .history import period_features
from .normalize import utc_now,DataError

def default_catalog():
    choices=[ROOT.parent/'site/catalog.json',ROOT.parent/'catalog.json']
    return next((p for p in choices if p.exists()),choices[0])

def asins_from(args):
    if getattr(args,'asins',None):return args.asins
    data=json.loads(Path(args.catalog).read_text())
    return [p['markets']['amazon']['id'] for p in data['products']]

def probe(provider):
    # Reachability only: a 4xx is not authentication success or product access.
    if provider=='keepa':url='https://api.keepa.com/product?'+urlencode({'domain':11,'asin':'B0C1HGKNG7','history':1,'days':180})
    else:url='https://sellingpartnerapi-na.amazon.com/catalog/2022-04-01/items/B0C1HGKNG7?'+urlencode({'marketplaceIds':MARKETPLACE_MX,'includedData':'summaries,salesRanks'})
    result={'provider':provider,'at':utc_now(),'test':'unauthenticated_reachability_only','authenticated':False,'products_received':0}
    try:
        Transport(retries=0).request('GET',url);result.update(endpoint_reachable=True,http_status=200,note='Respuesta HTTP sin probar credenciales ni cobertura de productos.')
    except ProviderError as e:result.update(endpoint_reachable=e.status is not None,http_status=e.status,result=e.code)
    return result

def main():
    parser=argparse.ArgumentParser(description='Nexo: adquisición por API sin navegador ni claves en frontend.');sub=parser.add_subparsers(dest='command',required=True)
    d=sub.add_parser('doctor');d.add_argument('--probe',choices=['keepa','sp-api','both'])
    c=sub.add_parser('configure');c.add_argument('provider',choices=list(PROVIDER_KEYS))
    s=sub.add_parser('sync');s.add_argument('--provider',choices=['auto','keepa','sp-api'],default='auto');s.add_argument('--asins',nargs='+');s.add_argument('--catalog',default=str(default_catalog()));s.add_argument('--days',type=int,default=180);s.add_argument('--offers',type=int,default=0)
    v=sub.add_parser('serve');v.add_argument('--site',default=str(ROOT.parent/'site' if (ROOT.parent/'site/app.html').exists() else ROOT.parent));v.add_argument('--catalog',default=str(default_catalog()));v.add_argument('--asins',nargs='+');v.add_argument('--provider',choices=['auto','keepa','sp-api'],default='auto');v.add_argument('--port',type=int,default=8787);v.add_argument('--sync-seconds',type=int,default=0);v.add_argument('--days',type=int,default=180)
    h=sub.add_parser('features');h.add_argument('--asin',required=True);h.add_argument('--category-id',required=True);h.add_argument('--start',required=True);h.add_argument('--end',required=True);h.add_argument('--provider',choices=['keepa','sp-api'],default='keepa')
    args=parser.parse_args()
    try:
        if args.command=='doctor':
            result={'at':utc_now(),'providers':readiness(load_credentials()),'authenticated_connection_verified':False,'note':'Configurado no significa autenticado. Solo una sincronización correcta verifica el acceso real.'}
            if args.probe:result['probes']=[probe(n) for n in (['keepa','sp-api'] if args.probe=='both' else [args.probe])]
            print(json.dumps(result,ensure_ascii=False,indent=2));return 0
        if args.command=='configure':
            values=load_credentials()
            for name in PROVIDER_KEYS[args.provider]:
                value=getpass.getpass(name+' (entrada oculta): ').strip()
                if not value:raise ConfigurationError('Credencial vacía; no se ha guardado el cambio.')
                values[name]=value
            save_credentials(values);print('Credenciales guardadas localmente con permisos 600. No se imprimen ni se suben a GitHub.');return 0
        store=Store()
        if args.command=='sync':
            result=sync(store,asins_from(args),args.provider,args.days,args.offers);print(json.dumps(result,ensure_ascii=False,indent=2))
            return 0 if all(r['status'] in ('ok','authenticated_no_products') for r in result['results']) else 2
        if args.command=='features':print(json.dumps(period_features(store,args.asin,args.category_id,args.start,args.end,args.provider),ensure_ascii=False,indent=2));return 0
        if args.command=='serve':
            from .server import serve
            serve(store,args.site,asins_from(args),args.port,args.sync_seconds,args.provider,args.days);return 0
    except (ConfigurationError,DataError) as e:print(json.dumps({'status':'blocked','reason':str(e)},ensure_ascii=False));return 2
    except ProviderError as e:print(json.dumps({'status':e.code,'http_status':e.status}));return 2
    except (OSError,ValueError,KeyError):print(json.dumps({'status':'configuration_or_data_error','note':'Revisa rutas y formatos; no se muestran secretos ni respuestas crudas.'}));return 2

if __name__=='__main__':sys.exit(main())
