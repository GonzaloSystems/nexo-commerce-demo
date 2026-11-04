"""Local operator pilot; credentials stay on server and discovery is explicitly requested."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,unquote
import json,mimetypes,re,threading,secrets
from .discovery import DiscoveryService
from .transport import ProviderError
from .config import save_credentials,STATE_DIR
from .config import load_credentials,readiness,ConfigurationError
from .pipeline import sync
from .normalize import utc_now

PUBLIC_FILES={'index.html','app.html','styles.css','prisma.css','app.js','catalog.js','catalog.json','estimator.js','filters.js','discovery.js','experience.js','insights.js','evolution.css','runtime-config.js','calibracion.csv','nexo-extension.zip','research.css','research-filters.js','taxonomy.json'}

def make_handler(store,site_root):
    root=Path(site_root).resolve()
    discovery=DiscoveryService(cache_path=STATE_DIR/'discovery-cache.json')
    local_token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):return
        def send(self,status,payload,content_type='application/json; charset=utf-8'):
            body=payload if isinstance(payload,bytes) else json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(status)
            for key,value in [('Content-Type',content_type),('Content-Length',str(len(body))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer')]:self.send_header(key,value)
            self.end_headers();self.wfile.write(body)
        def do_POST(self):
            path=urlsplit(self.path).path
            allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            host=self.headers.get('Host','');origin=self.headers.get('Origin')
            extension_read=path=='/api/product' and origin and re.fullmatch(r'chrome-extension://[a-p]{32}',origin)
            if host not in allowed or (origin and origin!='http://'+host and not extension_read) or not secrets.compare_digest(self.headers.get('X-Nexo-Local',''),local_token):
                self.send(403,{'error':'local_session_required'});return
            if path not in ('/api/search','/api/product','/api/offers','/api/settings/rainforest'):self.send(405,{'error':'read_only_api'});return
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=8192 or self.headers.get('Content-Type','').split(';')[0]!='application/json':self.send(400,{'error':'invalid_request'});return
                data=json.loads(self.rfile.read(length))
                if not isinstance(data,dict):self.send(400,{'error':'invalid_request'});return
                if path=='/api/settings/rainforest':
                    key=data.get('key')
                    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,256}',key):self.send(400,{'error':'invalid_api_key_format'});return
                    values=load_credentials();values['RAINFOREST_API_KEY']=key;save_credentials(values)
                    self.send(200,{'saved':True,'authenticated':False,'note':'Clave guardada localmente. La primera búsqueda verificará el acceso.'});return
                if path=='/api/offers':self.send(200,discovery.offers(data.get('asin')));return
                if path=='/api/product':self.send(200,discovery.detail(data.get('asin'),root/'catalog.json'));return
                self.send(200,discovery.search(data.get('query'),data.get('category_id')))
            except ConfigurationError as e:self.send(503,{'error':'api_not_configured','message':str(e)})
            except ProviderError as e:self.send(502 if e.status!=429 else 429,{'error':e.code,'provider_status':e.status})
            except (ValueError,TypeError):self.send(400,{'error':'invalid_request'})
            except Exception:self.send(500,{'error':'internal_error'})
        def do_GET(self):
            try:
                path=unquote(urlsplit(self.path).path)
                if path=='/api/health':
                    status=store.status();self.send(200,{'status':'ok','at':utc_now(),'configured':readiness(load_credentials()),'discovery':discovery.status(),'has_successful_sync':any(r['status'] in ('ok','authenticated_no_products') for r in status['last_runs']),**status});return
                cached_match=re.fullmatch(r'/api/discovery/product/([A-Z0-9]{10})',path)
                if cached_match:self.send(200,{'product':discovery.cached_product(cached_match.group(1))});return
                if path=='/api/discovery/latest':self.send(200,{'result':discovery.latest()});return
                if path=='/api/products':
                    self.send(200,{'schema_version':1,'source_mode':'api_storage','at':utc_now(),'products':store.products(),'status':store.status()});return
                match=re.fullmatch(r'/api/products/([A-Z0-9]{10})/history',path)
                if match:
                    args=parse_qs(urlsplit(self.path).query);metric=args.get('metric',['rank'])[0];cat=args.get('category',[''])[0];provider=args.get('provider',['keepa'])[0]
                    if metric not in ('rank','price:new_lowest','price:amazon','price:buy_box','monthly_units_min','offer_count_new') or provider not in ('keepa','sp-api') or not re.fullmatch(r'\d{0,20}',cat):self.send(400,{'error':'invalid_history_query'});return
                    self.send(200,{'asin':match.group(1),'provider':provider,'metric':metric,'category':cat,'events':store.history(match.group(1),metric,cat,provider)});return
                if path=='/runtime-config.js':self.send(200,('window.NEXO_RUNTIME = '+json.dumps({'apiBaseUrl':'','refreshSeconds':300,'localToken':local_token})+';').encode(),'text/javascript; charset=utf-8');return
                relative=path.lstrip('/') or 'index.html';candidate=(root/relative).resolve()
                permitted=relative in PUBLIC_FILES or (relative.startswith('assets/') and candidate.suffix.lower() in {'.jpg','.jpeg','.png','.webp','.svg','.txt'})
                if not permitted or root not in candidate.parents or not candidate.is_file():self.send(404,{'error':'not_found'});return
                self.send(200,candidate.read_bytes(),mimetypes.guess_type(candidate.name)[0] or 'application/octet-stream')
            except ConfigurationError:self.send(503,{'error':'credentials_configuration_error'})
            except Exception:self.send(500,{'error':'internal_error'})
    return Handler

def serve(store,site_root,asins,port=8787,interval=0,provider='auto',days=180):
    if interval and interval<600:raise ConfigurationError('Usa al menos 600 segundos entre sincronizaciones.')
    stop=threading.Event()
    def worker():
        while not stop.is_set():
            try:
                if any(v['configured'] for v in readiness(load_credentials()).values()):sync(store,asins,provider,days)
            except Exception:pass  # Never print credentials or provider error bodies.
            stop.wait(interval)
    if interval:threading.Thread(target=worker,name='nexo-api-sync',daemon=True).start()
    server=ThreadingHTTPServer(('127.0.0.1',port),make_handler(store,site_root))
    print(f'Nexo local: http://127.0.0.1:{port} — APIs en servidor; sincronización {"activa si hay credenciales" if interval else "manual"}.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:stop.set();server.server_close()
