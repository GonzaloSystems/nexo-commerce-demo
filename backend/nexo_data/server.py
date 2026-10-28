"""Local API pilot. Provider credentials remain on server; visitors do not trigger paid calls."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs,unquote
import json,mimetypes,re,threading
from .config import load_credentials,readiness,ConfigurationError
from .pipeline import sync
from .normalize import utc_now

PUBLIC_FILES={'index.html','app.html','styles.css','app.js','catalog.js','catalog.json','estimator.js','runtime-config.js','calibracion.csv'}

def make_handler(store,site_root):
    root=Path(site_root).resolve()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):return
        def send(self,status,payload,content_type='application/json; charset=utf-8'):
            body=payload if isinstance(payload,bytes) else json.dumps(payload,ensure_ascii=False,allow_nan=False).encode()
            self.send_response(status)
            for key,value in [('Content-Type',content_type),('Content-Length',str(len(body))),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Referrer-Policy','no-referrer')]:self.send_header(key,value)
            self.end_headers();self.wfile.write(body)
        def do_POST(self):self.send(405,{'error':'read_only_api'})
        def do_GET(self):
            try:
                path=unquote(urlsplit(self.path).path)
                if path=='/api/health':
                    status=store.status();self.send(200,{'status':'ok','at':utc_now(),'configured':readiness(load_credentials()),'has_successful_sync':any(r['status'] in ('ok','authenticated_no_products') for r in status['last_runs']),**status});return
                if path=='/api/products':
                    self.send(200,{'schema_version':1,'source_mode':'api_storage','at':utc_now(),'products':store.products(),'status':store.status()});return
                match=re.fullmatch(r'/api/products/([A-Z0-9]{10})/history',path)
                if match:
                    args=parse_qs(urlsplit(self.path).query);metric=args.get('metric',['rank'])[0];cat=args.get('category',[''])[0];provider=args.get('provider',['keepa'])[0]
                    if metric not in ('rank','price:new_lowest','price:amazon','price:buy_box','monthly_units_min','offer_count_new') or provider not in ('keepa','sp-api') or not re.fullmatch(r'\d{0,20}',cat):self.send(400,{'error':'invalid_history_query'});return
                    self.send(200,{'asin':match.group(1),'provider':provider,'metric':metric,'category':cat,'events':store.history(match.group(1),metric,cat,provider)});return
                if path=='/runtime-config.js':self.send(200,b'window.NEXO_RUNTIME = {apiBaseUrl:"",refreshSeconds:300};','text/javascript; charset=utf-8');return
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
