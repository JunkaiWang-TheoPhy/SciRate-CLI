import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import scirate

class ClientTests(unittest.TestCase):
    def test_invalid_id(self):
        with self.assertRaises(ValueError):
            scirate.paper('../login')

    def test_challenge_import_rejected(self):
        with self.assertRaises(ValueError):
            scirate.page_record('<title>Just a moment</title>', 'https://scirate.com', 'now')

    def test_api_shape(self):
        with patch.object(scirate, 'fetch', return_value=('[{"uid":"1509.01147","scite_created_at":"today"}]', 'now')):
            row = scirate.scites('alice')
        self.assertEqual(row['records'][0]['scite_created_at'], 'today')
        self.assertFalse(row['possibly_more'])

    def test_mcp_handshake_and_list(self):
        messages = '\n'.join(json.dumps(m) for m in [{'id':1,'method':'initialize','params':{'protocolVersion':'2024-11-05'}}, {'id':2,'method':'tools/list'}])
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO(messages)), patch('sys.stdout', output):
            scirate.mcp()
        rows = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(rows[1]['result']['tools']), 6)

if __name__ == '__main__':
    unittest.main()
