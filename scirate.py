#!/usr/bin/env python3
"""SciRate and arXiv CLI with a read-only MCP and explicit browser actions."""
import argparse
import datetime
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from community import parse as parse_community

ROOT = Path(os.environ.get('SCIRATE_DATA_DIR', str(Path.home() / '.local/share/scirate-tools/data')))
ID = re.compile(r'^(?:\d{4}\.\d{4,5}|[a-zA-Z.-]+/\d{7})(?:v\d+)?$')
VERSION = '0.3.0'

def private_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            output.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def fetch(url):
    ROOT.mkdir(parents=True, exist_ok=True)
    cache = ROOT / (hashlib.sha256(url.encode()).hexdigest() + '.json')
    if cache.exists():
        try:
            record = json.loads(cache.read_text())
            if time.time() - record['cached_at'] < 3600:
                return record['body'], record['fetched_at']
        except (ValueError, KeyError, TypeError):
            pass
    request = urllib.request.Request(url, headers={'User-Agent': f'SciRate-CLI/{VERSION} (read-only)', 'Accept': 'application/json,text/html,application/atom+xml'})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read(8_000_001)
            if len(body) > 8_000_000:
                raise ValueError('response_too_large')
            body = body.decode('utf-8')
    except urllib.error.HTTPError as error:
        body = error.read(10000).decode('utf-8', errors='replace')
        if error.headers.get('cf-mitigated') == 'challenge' or 'Just a moment' in body:
            raise ValueError('cloudflare_challenge: open SciRate in your browser and import a saved page') from error
        raise ValueError(f'http_error:{error.code}') from error
    if 'cf-chl-' in body or '<title>Just a moment' in body:
        raise ValueError('cloudflare_challenge')
    stamp = now()
    private_write(cache, json.dumps({'cached_at': time.time(), 'fetched_at': stamp, 'body': body}))
    return body, stamp

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.text = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag == 'a':
            href = dict(attrs).get('href', '')
            if href.startswith('/arxiv/'):
                uid = href.removeprefix('/arxiv/')
                if ID.fullmatch(uid) and uid not in self.links:
                    self.links.append(uid)

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.text.append(data.strip())

def page_record(body, source, stamp):
    if 'cf-chl-' in body or '<title>Just a moment' in body:
        raise ValueError('saved_page_is_challenge')
    parser = Page()
    parser.feed(body)
    return {'source_url': source, 'fetched_at': stamp, 'arxiv_ids': parser.links, 'page_text': '\n'.join(parser.text), **parse_community(body)}

def community(arxiv_id):
    if not ID.fullmatch(arxiv_id):
        raise ValueError('invalid_arxiv_id')
    source = 'https://scirate.com/arxiv/' + arxiv_id
    body, stamp = fetch(source)
    return page_record(body, source, stamp)

def paper(arxiv_id):
    if not ID.fullmatch(arxiv_id):
        raise ValueError('invalid_arxiv_id')
    source = 'https://export.arxiv.org/api/query?' + urllib.parse.urlencode({'id_list': arxiv_id})
    body, stamp = fetch(source)
    atom = {'a': 'http://www.w3.org/2005/Atom'}
    entry = ET.fromstring(body).find('a:entry', atom)
    if entry is None or entry.findtext('a:title', '', atom) == 'Error':
        raise ValueError('paper_not_found')
    return {'arxiv_id': arxiv_id, 'title': ' '.join(entry.findtext('a:title', '', atom).split()), 'abstract': entry.findtext('a:summary', '', atom).strip(), 'authors': [a.findtext('a:name', '', atom) for a in entry.findall('a:author', atom)], 'categories': [c.attrib['term'] for c in entry.findall('a:category', atom)], 'published': entry.findtext('a:published', '', atom), 'updated': entry.findtext('a:updated', '', atom), 'source_url': source, 'scirate_url': 'https://scirate.com/arxiv/' + arxiv_id, 'fetched_at': stamp}

def feed(category='quant-ph'):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9.-]*', category):
        raise ValueError('invalid_category')
    source = 'https://scirate.com/arxiv/' + category
    body, stamp = fetch(source)
    return page_record(body, source, stamp)

def scites(username, page=1):
    if not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', username) or type(page) is not int or page < 1:
        raise ValueError('invalid_username_or_page')
    source = 'https://scirate.com/' + urllib.parse.quote(username, safe='') + '/download_scites?page=' + str(page)
    body, stamp = fetch(source)
    records = json.loads(body)
    if not isinstance(records, list):
        raise ValueError('unexpected_scites_response')
    return {'source_url': source, 'fetched_at': stamp, 'page': page, 'records': records, 'possibly_more': len(records) == 1000}

OPS = {'paper': paper, 'feed': feed, 'scites': scites, 'community': community}

def browser_read(browser='Chrome'):
    from browser import snapshot
    captured = snapshot(browser)
    return page_record(captured['html'], captured['url'], now())

def auth_status(browser='Chrome'):
    from browser import status
    return status(browser)

OPS.update({'browser_read': browser_read, 'auth_status': auth_status})

def mcp():
    schemas = {'paper': {'arxiv_id': {'type': 'string'}}, 'community': {'arxiv_id': {'type': 'string'}}, 'feed': {'category': {'type': 'string'}}, 'scites': {'username': {'type': 'string'}, 'page': {'type': 'integer', 'minimum': 1}}}
    required = {'paper': ['arxiv_id'], 'community': ['arxiv_id'], 'feed': [], 'scites': ['username']}
    for name in ('browser_read', 'auth_status'):
        schemas[name] = {'browser': {'type': 'string', 'enum': ['Chrome', 'Safari']}}
        required[name] = []
    for line in sys.stdin:
        request = {}
        try:
            request = json.loads(line)
            if 'id' not in request:
                continue
            method = request['method']
            if method == 'initialize':
                requested = request.get('params', {}).get('protocolVersion')
                protocol = requested if requested in ('2024-11-05', '2025-03-26', '2025-06-18') else '2024-11-05'
                result = {'protocolVersion': protocol, 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'scirate-local', 'version': VERSION}}
            elif method == 'ping':
                result = {}
            elif method == 'tools/list':
                result = {'tools': [{'name': name, 'description': function.__name__ + ' (read-only; SciRate may require browser access)', 'inputSchema': {'type': 'object', 'properties': schemas[name], 'required': required[name], 'additionalProperties': False}, 'annotations': {'readOnlyHint': True}} for name, function in OPS.items()]}
            elif method == 'tools/call':
                params = request['params']
                try:
                    name = params['name']
                    arguments = params.get('arguments', {})
                    if name not in OPS or not isinstance(arguments, dict):
                        raise ValueError('invalid_tool_or_arguments')
                    if set(arguments) - set(schemas[name]) or set(required[name]) - set(arguments):
                        raise ValueError('invalid_arguments')
                    for key, value in arguments.items():
                        expected = int if schemas[name][key]['type'] == 'integer' else str
                        if type(value) is not expected:
                            raise ValueError('invalid_argument_type:' + key)
                        if 'enum' in schemas[name][key] and value not in schemas[name][key]['enum']:
                            raise ValueError('invalid_argument_value:' + key)
                    value = OPS[name](**arguments)
                    result = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}]}
                except Exception as error:
                    result = {'isError': True, 'content': [{'type': 'text', 'text': str(error)}]}
            else:
                print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'error': {'code': -32601, 'message': 'Method not found'}}), flush=True)
                continue
            print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
        except Exception as error:
            print(json.dumps({'jsonrpc': '2.0', 'id': request.get('id') if isinstance(request, dict) else None, 'error': {'code': -32700 if isinstance(error, json.JSONDecodeError) else -32600, 'message': str(error)}}), flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('mcp')
    p = commands.add_parser('browser-read'); p.add_argument('--browser', choices=['Chrome', 'Safari'], default='Chrome')
    p = commands.add_parser('auth-status'); p.add_argument('--browser', choices=['Chrome', 'Safari'], default='Chrome')
    p = commands.add_parser('act'); p.add_argument('name', choices=['scite', 'unscite', 'subscribe', 'unsubscribe', 'comment', 'reply']); p.add_argument('target'); p.add_argument('--content'); p.add_argument('--browser', choices=['Chrome', 'Safari'], default='Chrome')
    p = commands.add_parser('receipt'); p.add_argument('ticket'); p.add_argument('--browser', choices=['Chrome', 'Safari'], default='Chrome')
    p = commands.add_parser('paper'); p.add_argument('arxiv_id')
    p = commands.add_parser('community'); p.add_argument('arxiv_id')
    p = commands.add_parser('feed'); p.add_argument('category', nargs='?', default='quant-ph')
    p = commands.add_parser('scites'); p.add_argument('username'); p.add_argument('--page', type=int, default=1)
    p = commands.add_parser('import'); p.add_argument('file', type=Path); p.add_argument('--source-url', required=True)
    args = vars(parser.parse_args())
    command = args.pop('command')
    if command == 'mcp':
        mcp(); return
    try:
        if command in ('browser-read', 'auth-status', 'act', 'receipt'):
            import browser
            if command == 'browser-read':
                captured = browser.snapshot(**args)
                result = page_record(captured['html'], captured['url'], now())
            elif command == 'auth-status':
                result = browser.status(**args)
            elif command == 'act':
                result = browser.action(**args)
            else:
                result = browser.receipt(**args)
        elif command == 'import':
            source = args['source_url']
            url = urllib.parse.urlparse(source)
            if url.scheme != 'https' or url.hostname != 'scirate.com':
                raise ValueError('source_url_must_be_scirate_https')
            path = args['file']
            if path.stat().st_size > 8_000_000:
                raise ValueError('response_too_large')
            body = path.read_text(encoding='utf-8')
            result = page_record(body, source, now())
            ROOT.mkdir(parents=True, exist_ok=True)
            archive = ROOT / (hashlib.sha256(body.encode()).hexdigest() + '.html')
            private_write(archive, body)
            result['archive_path'] = str(archive)
        else:
            result = OPS[command](**args)
        print(json.dumps({'ok': True, 'data': result}, ensure_ascii=False, indent=2))
    except Exception as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
