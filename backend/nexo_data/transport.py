"""Bounded HTTPS JSON transport. Never log provider URLs, headers or error bodies."""
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request

ALLOWED_HOSTS = {'api.keepa.com', 'api.amazon.com', 'sellingpartnerapi-na.amazon.com'}
MAX_BYTES = 32 * 1024 * 1024

class ProviderError(Exception):
    def __init__(self, code, status=None, retry_after=None):
        self.code, self.status, self.retry_after = code, status, retry_after
        super().__init__(code)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError('redirect_rejected', code)

class Transport:
    def __init__(self, opener=None, sleeper=time.sleep, retries=2):
        self.opener = opener or urllib.request.build_opener(NoRedirect())
        self.sleeper = sleeper
        self.retries = retries

    def request(self, method, url, headers=None, body=None):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.port not in (None,443):
            raise ProviderError('endpoint_not_allowed')
        if method not in ('GET','POST'):
            raise ProviderError('method_not_allowed')
        hdr = {'Accept': 'application/json', 'Accept-Encoding': 'gzip', 'User-Agent': 'Nexo-Commerce-Data/0.1'}
        hdr.update(headers or {})
        request = urllib.request.Request(url, data=body, headers=hdr, method=method)
        for attempt in range(self.retries + 1):
            try:
                with self.opener.open(request, timeout=15) as response:
                    content = response.read(MAX_BYTES + 1)
                    if len(content) > MAX_BYTES:
                        raise ProviderError('response_too_large')
                    if response.headers.get('Content-Encoding') == 'gzip':
                        # Bound decompressed size as well as the wire body.
                        import io
                        with gzip.GzipFile(fileobj=io.BytesIO(content)) as zipped:
                            content = zipped.read(MAX_BYTES + 1)
                        if len(content) > MAX_BYTES:
                            raise ProviderError('response_too_large')
                    try:
                        data = json.loads(content)
                    except (ValueError, UnicodeError):
                        raise ProviderError('invalid_json') from None
                    if not isinstance(data, dict):
                        raise ProviderError('invalid_response')
                    return data
            except urllib.error.HTTPError as exc:
                status = exc.code
                retry = exc.headers.get('Retry-After', '')
                try:
                    wait = max(0, int(retry)) if retry else 2 ** attempt
                except ValueError:
                    wait = 2 ** attempt
                # A 429 can mean an empty Keepa bucket. Do not burn requests or
                # ignore a long retry delay; leave that job for the scheduler.
                if status in (429,500,502,503,504) and attempt < self.retries and wait <= 5:
                    self.sleeper(wait)
                    continue
                code = 'authentication_required' if status in (401,403) else 'rate_limited' if status == 429 else 'payment_or_plan_required' if status == 402 else 'http_error'
                raise ProviderError(code, status, wait if status == 429 else None) from None
            except (urllib.error.URLError, TimeoutError, OSError):
                raise ProviderError('network_error') from None
        raise ProviderError('request_failed')
