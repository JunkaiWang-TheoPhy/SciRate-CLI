import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import browser
import scirate


class ReleaseTests(unittest.TestCase):
    def test_unknown_receipt_is_not_pending(self):
        with patch.object(browser, 'run_javascript', return_value='{"status":"unknown_ticket"}') as call:
            self.assertEqual(browser.receipt('missing')['status'], 'unknown_ticket')
        self.assertIn('unknown_ticket', call.call_args.args[0])

    def test_action_has_timeout(self):
        with patch.object(browser, 'run_javascript', return_value='{"ticket":"id"}') as call:
            browser.action('scite', '1509.01147')
        self.assertIn('AbortController', call.call_args.args[0])
        self.assertIn('25000', call.call_args.args[0])

    def test_corrupt_cache_recovers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            url = 'https://scirate.com/arxiv/quant-ph'
            cache = root / (hashlib.sha256(url.encode()).hexdigest() + '.json')
            cache.write_text('{broken')
            response = unittest.mock.MagicMock()
            response.__enter__.return_value.read.return_value = b'<html>valid</html>'
            with patch.object(scirate, 'ROOT', root), patch('urllib.request.urlopen', return_value=response):
                self.assertEqual(scirate.fetch(url)[0], '<html>valid</html>')
                with patch('urllib.request.urlopen', side_effect=AssertionError('cache miss')):
                    self.assertEqual(scirate.fetch(url)[0], '<html>valid</html>')
            self.assertEqual(cache.stat().st_mode & 0o777, 0o600)

    def test_mcp_malformed_json_does_not_kill_server(self):
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO('{broken\n{"id":1,"method":"ping"}\n')), patch('sys.stdout', output):
            scirate.mcp()
        rows = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(rows[0]['error']['code'], -32700)
        self.assertEqual(rows[1]['result'], {})

    def test_unknown_protocol_not_echoed(self):
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO('{"id":1,"method":"initialize","params":{"protocolVersion":"invented"}}')), patch('sys.stdout', output):
            scirate.mcp()
        self.assertEqual(json.loads(output.getvalue())['result']['protocolVersion'], '2024-11-05')

    def test_invalid_scites_page_type(self):
        with patch.object(scirate, 'fetch', return_value=('[]', 'now')), self.assertRaises(ValueError):
            scirate.scites('alice', True)

    @unittest.skipUnless(shutil.which('node'), 'Node.js needed for browser-script contract test')
    def test_generated_script_executes_without_real_network(self):
        with patch.object(browser, 'run_javascript', return_value='{"ticket":"id"}') as call:
            browser.action('comment', '1509.01147', 'A "quote" & text')
        script = call.call_args.args[0]
        harness = '''const vm=require('node:vm');
const context={window:{},document:{querySelector:s=>s.includes('csrf')?{content:'fixture-token'}:{}},crypto:{randomUUID:()=> 'ticket'},AbortController,URLSearchParams,setTimeout,clearTimeout};
context.fetch=async (path,options)=>{if(path!='/comments')throw Error('wrong path');if(options.headers['X-CSRF-Token']!=='fixture-token')throw Error('missing csrf');if(options.body.get('comment[content]')!=='A "quote" & text')throw Error('wrong content');return {status:200,url:'https://scirate.com/arxiv/1509.01147',text:async()=> 'fixture'};};
vm.runInNewContext(SCRIPT,context);setImmediate(()=>{console.log(JSON.stringify(context.window.__scirateResults.ticket));});
'''.replace('SCRIPT', json.dumps(script))
        result = subprocess.run(['node', '-e', harness], capture_output=True, text=True, timeout=10, check=True)
        self.assertEqual(json.loads(result.stdout)['body'], 'fixture')


if __name__ == '__main__':
    unittest.main()
