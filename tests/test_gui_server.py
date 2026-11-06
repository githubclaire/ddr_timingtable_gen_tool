"""HTTP-level tests for the actual GUI server endpoints.

These exercise the same code paths the browser uses: preview command,
generate, analyze, save/load JSON, and file browsing.
"""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import gui  # noqa: E402
from tests.test_gui_matrix import base_params  # noqa: E402


class GuiServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cwd = os.getcwd()
        os.chdir(ROOT)
        cls.server = gui.ReuseAddrTCPServer(('127.0.0.1', 0), gui.DDRHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        os.chdir(cls.cwd)

    def _post(self, path, payload):
        req = urllib.request.Request(
            'http://127.0.0.1:%d%s' % (self.port, path),
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode())

    def _get(self, path):
        with urllib.request.urlopen(
                'http://127.0.0.1:%d%s' % (self.port, path), timeout=20) as resp:
            return resp.read().decode()

    def test_index(self):
        html = self._get('/')
        self.assertIn('id="paramsForm"', html)
        self.assertIn('orbit-freq-level', html)

    def test_preview_generate_analyze(self):
        params = base_params('lpddr4')
        params['dfs-lvl-t-ck-0'] = '938'
        params['dfs-lvl-t-ck-1'] = '1631'
        params['dfs-lvl-t-ck-2'] = '2500'
        preview = self._post('/preview-cmd', params)
        self.assertTrue(preview['success'])
        self.assertIn('gen_timing_params', preview['command'])

        result = self._post('/generate', params)
        self.assertTrue(result['success'], result)
        self.assertEqual(os.path.getsize('ddr_timing_table.bin'), 0x1000)

        analyzed = self._post('/analyze', {
            'file_path': 'ddr_timing_table.bin',
            'dram_type_override': 'auto',
            'two_channel_override': None,
        })
        self.assertTrue(analyzed['success'], analyzed)
        self.assertEqual(analyzed['data']['dram_type'], 'lpddr4')
        self.assertTrue(analyzed['data']['orbit']['available'])
        self.assertEqual(len(analyzed['data']['timing_entries']['entries']), 3)

    def test_save_load_json_and_browse(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, 'cfg.json')
            saved = self._post('/save-json', {
                'file_path': path,
                'data': {'dram-type': 'lpddr5', 'orbit-config-density': '8'},
            })
            self.assertTrue(saved['success'])
            loaded = self._post('/load-json-path', {'file_path': path})
            self.assertTrue(loaded['success'])
            self.assertEqual(loaded['data']['dram-type'], 'lpddr5')
            listing = self._post('/browse', {'path': td, 'filter': '.json'})
            self.assertTrue(listing['success'])
            self.assertIn('cfg.json', [e['name'] for e in listing['entries']])


if __name__ == '__main__':
    unittest.main(verbosity=2)
