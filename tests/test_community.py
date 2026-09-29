import unittest
from community import parse

PAPER = '''<li class="paper tex2jax"><div class="title"><a href="/arxiv/1509.01147">Title &amp; gravity</a></div><div class="authors"><a>Alice,</a><a>Bob</a></div><div class="scite-toggle" data-paper-uid="1509.01147"><div class="scites-count"><a><button>12</button></a></div></div><div class="abstract">A &lt; B</div></li>'''
COMMENTS = '''<div class="comment" data-id="10" data-markup="Original"><div class="nonvotes"><a href="/alice">Alice</a><span class="timeago"><abbr title="2026-09-29T00:00:00Z">today</abbr><span class="score">3</span></span><div class="body"><p>Hello</p></div></div></div><div class="comment reply" data-id="11"><a href="/bob">Bob</a> in reply to <a href="#10">Alice</a><div class="body">Reply</div><a class="permalink" href="#11">permalink</a></div><div class="comment deleted" data-id="12" data-markup="secret"><div class="body">secret</div></div>'''

class CommunityTests(unittest.TestCase):
    def test_count_and_metadata(self):
        p = parse(PAPER)['papers'][0]
        self.assertEqual(p['scites_count'], 12)
        self.assertEqual(p['title'], 'Title & gravity')
        self.assertEqual(p['authors'], ['Alice', 'Bob'])
        self.assertEqual(p['abstract'], 'A < B')

    def test_missing_count_is_unknown(self):
        p = parse(PAPER.replace('<button>12</button>', '<button>?</button>'))['papers'][0]
        self.assertIsNone(p['scites_count'])

    def test_comment_relationship_and_timestamp(self):
        rows = parse(COMMENTS)['comments']
        self.assertEqual(rows[0]['username'], 'alice')
        self.assertEqual(rows[0]['score'], 3)
        self.assertEqual(rows[0]['created_at'], '2026-09-29T00:00:00Z')
        self.assertEqual(rows[1]['parent_id'], '10')
        self.assertEqual(rows[1]['content'], 'Reply')

    def test_deleted_content_is_not_exposed(self):
        row = parse(COMMENTS)['comments'][2]
        self.assertIsNone(row['content'])
        self.assertIsNone(row['markup'])

    def test_sciters(self):
        self.assertEqual(parse('<table class="usertable"><tr><td><a href="/alice">Alice</a></td></tr></table>')['sciters'], [{'username': 'alice', 'name': 'Alice'}])

    def test_detail_authors_are_not_duplicated(self):
        html = PAPER.replace('<div class="authors"><a>Alice,</a><a>Bob</a></div>', '<ul class="authors"><li><a>Alice</a>,</li><li><a>Bob</a></li></ul>')
        self.assertEqual(parse(html)['papers'][0]['authors'], ['Alice', 'Bob'])

    def test_comment_reference_is_not_a_reply(self):
        html = '<div class="comment" data-id="20"><a href="/alice">Alice</a><div class="body">See <a href="#10">comment 10</a></div></div>'
        self.assertIsNone(parse(html)['comments'][0]['parent_id'])

    def test_hidden_class_does_not_expose_markup(self):
        html = '<div class="comment hidden" data-id="20" data-markup="secret"><div class="body">secret</div></div>'
        self.assertIsNone(parse(html)['comments'][0]['markup'])

    def test_detail_sciters(self):
        html = '<div class="scites"><strong>Scited by:</strong><a href="/alice">Alice</a></div>'
        self.assertEqual(parse(html)['sciters'], [{'username': 'alice', 'name': 'Alice'}])

if __name__ == '__main__':
    unittest.main()
