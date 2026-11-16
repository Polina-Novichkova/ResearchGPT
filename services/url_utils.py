from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def get_domain(url:str) -> str:
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.hostname or ''
    except ValueError:
        return ''
    
    domain = domain.lower()
    
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def normalize_url(url: str) -> str:
    try:
        parsed = urlparse(url.strip())
        port = parsed.port
    except ValueError:
        return ''
    
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or '').lower()
    
    if scheme not in ['http', 'https'] or not hostname:
        return ''
    
    if hostname.startswith('www.'):
        hostname = hostname[4:]
    
    if port and not(
        (scheme == 'http' and port == 80) or
        (scheme == 'https' and port == 443)
    ):
        hostname = f'{hostname}:{port}'
        
    path = parsed.path.rstrip('/')
    if not path:
        path = '/'
    
    query_params = parse_qsl(
        parsed.query,
        keep_blank_values = True
    )
    
    query_params.sort()
    query = urlencode(query_params)
    normalized = urlunparse((
        scheme,
        hostname,
        path,
        '',
        query,
        ''
    ))

    return normalized