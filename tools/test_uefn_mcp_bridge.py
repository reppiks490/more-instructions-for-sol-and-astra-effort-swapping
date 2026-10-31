#!/usr/bin/env python3
"""Real local HTTP mock-server tests for the stdlib MCP protocol client.

These verify transport/plan guards. The mock is not a UEFN editor.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MODULE = Path(__file__).resolve().parent / 'uefn_editor/mcp_editor_bridge.py'
spec = importlib.util.spec_from_file_location('aeonfall_mcp_bridge', MODULE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

SCHEMA = {'type': 'object', 'properties': {'message': {'type': 'string'}}, 'required': ['message'], 'additionalProperties': False}
TOOLS = [{'name': 'editor_advertised_probe', 'inputSchema': SCHEMA}]


class MCPHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.requests.append((payload, dict(self.headers)))
        method = payload['method']
        if method == 'notifications/initialized':
            self.send_response(204)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if method == 'initialize':
            result = {'protocolVersion': '2025-06-18', 'capabilities': {'tools': {}},
                      'serverInfo': {'name': 'test_mock_not_uefn', 'version': '1'}}
        elif method == 'tools/list':
            result = {'tools': TOOLS}
            if self.server.repeat_cursor:
                result['nextCursor'] = 'same-cursor'
        elif method == 'tools/call':
            result = {'content': [{'type': 'text', 'text': payload['params']['arguments']['message']}], 'isError': self.server.tool_error}
        else:
            result = {}
        response = json.dumps({'jsonrpc': '2.0', 'id': payload['id'], 'result': result}).encode()
        self.send_response(200)
        self.send_header('Mcp-Session-Id', 'mock-session')
        if self.server.sse:
            response = b'event: message\ndata: ' + response + b'\n\n'
            self.send_header('Content-Type', 'text/event-stream')
        else:
            self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), MCPHandler)
        self.server.requests = []
        self.server.sse = self.server.tool_error = self.server.repeat_cursor = False
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = bridge.EditorMCP(f'http://127.0.0.1:{self.server.server_port}/mcp', timeout=2)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def plan(self, catalog):
        return {'schema_version': 1, 'catalog_sha256': catalog['catalog_sha256'],
                'steps': [{'tool_name': TOOLS[0]['name'], 'input_schema_sha256': bridge.digest(SCHEMA),
                           'arguments': {'message': 'actual mock response'}, 'requested_purpose': 'transport verification'}]}

    def test_real_http_initialize_discover_and_session_headers(self):
        catalog = self.client.discover()
        self.assertEqual(catalog['tools'], TOOLS)
        self.assertEqual([item[0]['method'] for item in self.server.requests], ['initialize', 'notifications/initialized', 'tools/list'])
        headers = self.server.requests[-1][1]
        self.assertEqual(headers['Mcp-Session-Id'], 'mock-session')
        self.assertEqual(headers['Mcp-Protocol-Version'], '2025-06-18')

    def test_actual_sse_response_supported(self):
        self.server.sse = True
        self.assertEqual(self.client.discover()['tools'], TOOLS)

    def test_repeated_cursor_rejected(self):
        self.server.repeat_cursor = True
        with self.assertRaises(bridge.BridgeError):
            self.client.discover()

    def test_unadvertised_name_rejected_before_call(self):
        catalog = self.client.discover()
        plan = self.plan(catalog)
        plan['steps'][0]['tool_name'] = 'invented_place_device'
        with self.assertRaises(bridge.BridgeError):
            bridge.validate_plan(plan, catalog)
        self.assertFalse(any(item[0]['method'] == 'tools/call' for item in self.server.requests))

    def test_changed_schema_rejected(self):
        catalog = self.client.discover()
        plan = self.plan(catalog)
        plan['steps'][0]['input_schema_sha256'] = 'stale'
        with self.assertRaises(bridge.BridgeError):
            bridge.validate_plan(plan, catalog)

    def test_modified_catalog_rejected(self):
        catalog = self.client.discover()
        plan = self.plan(catalog)
        catalog['tools'][0]['description'] = 'tampered'
        with self.assertRaises(bridge.BridgeError):
            bridge.validate_plan(plan, catalog)

    def test_required_argument_and_unknown_property_checked(self):
        catalog = self.client.discover()
        for arguments in ({}, {'message': 'ok', 'invented_property': True}, {'message': False}):
            with self.subTest(arguments=arguments), self.assertRaises(bridge.BridgeError):
                plan = self.plan(catalog)
                plan['steps'][0]['arguments'] = arguments
                bridge.validate_plan(plan, catalog)

    def test_bounded_timeout_enforced(self):
        for timeout in (0, -1, 31):
            with self.subTest(timeout=timeout), self.assertRaises(bridge.BridgeError):
                bridge.EditorMCP(timeout=timeout)

    def test_raw_actual_response_recorded_without_engine_success_claim(self):
        catalog = self.client.discover()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'evidence.json'
            evidence = bridge.execute_plan(self.client, self.plan(catalog), catalog, path)
            self.assertEqual(evidence['acceptance_claim'], 'not_assessed')
            self.assertEqual(evidence['records'][0]['result']['content'][0]['text'], 'actual mock response')
            self.assertEqual(json.loads(path.read_text()), evidence)

    def test_tool_error_saved_and_following_mutation_not_executed(self):
        catalog = self.client.discover()
        self.server.tool_error = True
        plan = self.plan(catalog)
        plan['steps'].append(copy.deepcopy(plan['steps'][0]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'evidence.json'
            with self.assertRaises(bridge.BridgeError):
                bridge.execute_plan(self.client, plan, catalog, path)
            evidence = json.loads(path.read_text())
            self.assertEqual(evidence['records'][0]['transport_status'], 'tool_error')
            self.assertEqual(len(evidence['records']), 1)
        self.assertEqual(sum(item[0]['method'] == 'tools/call' for item in self.server.requests), 1)


if __name__ == '__main__':
    unittest.main()
