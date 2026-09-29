import json
import unittest
from unittest.mock import patch
import browser

class BrowserTests(unittest.TestCase):
    def test_comment_uses_official_form_fields_and_csrf(self):
        with patch.object(browser, 'run_javascript', return_value='{"ticket":"id","status":"pending"}') as call:
            result = browser.action('comment', '1509.01147', 'A "quote"')
        script = call.call_args.args[0]
        self.assertIn('comment[paper_uid]', script)
        self.assertIn('comment[content]', script)
        self.assertIn('X-CSRF-Token', script)
        self.assertEqual(result['status'], 'pending')

    def test_reply_target_validation(self):
        with self.assertRaises(ValueError):
            browser.action('reply', '../delete', 'text')

    def test_pending_is_not_success(self):
        with patch.object(browser, 'run_javascript', return_value='{"status":"pending"}'):
            self.assertEqual(browser.receipt('id'), {'status': 'pending'})

if __name__ == '__main__':
    unittest.main()
