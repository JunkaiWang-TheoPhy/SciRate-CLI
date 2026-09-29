"""Parse SciRate's official paper and comment template structures."""
from html.parser import HTMLParser
import re
from urllib.parse import urlparse

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.walk()

    def has(self, name):
        return name in self.attrs.get('class', '').split()

    def text(self):
        return ' '.join(c.text() if isinstance(c, Node) else c for c in self.children).strip()

    def select(self, name):
        return [n for n in self.walk() if n.has(name)]

    def first_text(self, name):
        found = self.select(name)
        return found[0].text() if found else None

class DOM(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.current = self.root
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)

def number(text):
    return int(text.strip()) if text and re.fullmatch(r'-?\d+', text.strip()) else None

def parse(body):
    root = DOM(body).root
    papers = []
    for node in root.select('paper'):
        uid = next((n.attrs['data-paper-uid'] for n in node.walk() if 'data-paper-uid' in n.attrs), None)
        if not uid:
            continue
        authors = node.select('authors')
        count = node.select('scites-count')
        papers.append({'arxiv_id': uid, 'title': node.first_text('title'),
                       'abstract': node.first_text('abstract'),
                       'authors': [n.text().rstrip(', ') for n in authors[0].walk() if n.tag == 'a'] if authors else [],
                       'scites_count': number(count[0].text()) if count else None,
                       'source_url': 'https://scirate.com/arxiv/' + uid})
    comments = []
    for node in root.select('comment'):
        if 'data-id' not in node.attrs:
            continue
        parent = next((n.attrs['href'][1:] for n in node.walk() if n.tag == 'a' and re.fullmatch(r'#\d+', n.attrs.get('href', '')) and not n.has('permalink') and not any(a.has('body') for a in ancestors(n))), None) if node.has('reply') else None
        author = next((n for n in node.walk() if n.tag == 'a' and re.fullmatch(r'/[^/]+', n.attrs.get('href', ''))), None)
        dates = [n.attrs.get('title') or n.attrs.get('datetime') for n in node.walk() if n.tag in ('abbr', 'time')]
        hidden = node.has('deleted') or node.has('hidden')
        comments.append({'comment_id': node.attrs['data-id'], 'parent_id': parent,
                         'author': author.text() if author else None,
                         'username': urlparse(author.attrs['href']).path.lstrip('/') if author else None,
                         'content': None if hidden else node.first_text('body'),
                         'markup': None if hidden else node.attrs.get('data-markup'),
                         'created_at': next((d for d in dates if d), None),
                         'score': number(node.first_text('score')), 'hidden_or_deleted': hidden})
    sciters = []
    for table in root.select('usertable') + root.select('scites'):
        for node in table.walk():
            if node.tag == 'a' and re.fullmatch(r'/[^/]+', node.attrs.get('href', '')):
                sciters.append({'username': node.attrs['href'][1:], 'name': node.text()})
    return {'papers': papers, 'comments': comments, 'sciters': sciters}

def ancestors(node):
    while node.parent is not None:
        node = node.parent
        yield node
