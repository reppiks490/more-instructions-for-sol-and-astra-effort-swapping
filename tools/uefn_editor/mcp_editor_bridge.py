#!/usr/bin/env python3
"""Discover and invoke the tool schemas advertised by a running UEFN MCP server.

This is a stdlib Streamable HTTP client. It never invents UEFN tool names,
property names, placements, compilation success or Launch Session evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROTOCOL_VERSION = '2025-06-18'
MAX_BODY = 8 * 1024 * 1024


class BridgeError(RuntimeError):
    pass


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class EditorMCP:
    def __init__(self, url='http://127.0.0.1:8000/mcp', timeout=15):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise BridgeError('MCP endpoint must be an HTTP(S) URL without embedded credentials or fragment')
        if not 0 < timeout <= 30:
            raise BridgeError('HTTP timeout must be positive and no more than 30 seconds')
        self.url, self.timeout, self.session_id = url, timeout, None
        self.next_id = 0
        self.protocol_version = PROTOCOL_VERSION
        self.initialize_result = None

    def _post(self, payload, *, notification=False):
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
        if self.session_id:
            headers['Mcp-Session-Id'] = self.session_id
            headers['MCP-Protocol-Version'] = self.protocol_version
        request = urllib.request.Request(self.url, json.dumps(payload).encode(), headers, method='POST')
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                incoming_session = response.headers.get('Mcp-Session-Id')
                if incoming_session:
                    self.session_id = incoming_session
                if response.status in (202, 204) and notification:
                    return None
                content_type = response.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
                if content_type == 'text/event-stream':
                    message = self._read_sse(response, payload.get('id'))
                else:
                    body = response.read(MAX_BODY + 1)
                    if len(body) > MAX_BODY:
                        raise BridgeError('MCP response exceeds the body limit')
                    if notification and not body:
                        return None
                    message = json.loads(body)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            raise BridgeError(f'MCP HTTP request failed: {error}') from error
        if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
            raise BridgeError('Invalid JSON-RPC response')
        if message.get('id') != payload.get('id'):
            raise BridgeError('MCP response ID does not match the request')
        if 'error' in message:
            raise BridgeError(f'MCP server error: {json.dumps(message["error"], ensure_ascii=False)}')
        if 'result' not in message:
            raise BridgeError('MCP response has no result')
        return message['result']

    @staticmethod
    def _read_sse(response, request_id):
        data, total, events = [], 0, 0
        while True:
            raw = response.readline(MAX_BODY + 1)
            if not raw:
                raise BridgeError('MCP event stream closed without the matching response')
            total += len(raw)
            if total > MAX_BODY:
                raise BridgeError('MCP event stream exceeds the body limit')
            line = raw.decode('utf-8').rstrip('\r\n')
            if line.startswith('data:'):
                data.append(line[5:].lstrip(' '))
            elif not line and data:
                message = json.loads('\n'.join(data))
                data = []
                events += 1
                if isinstance(message, dict) and message.get('id') == request_id:
                    return message
                if events >= 64:
                    raise BridgeError('Too many unrelated MCP stream events')

    def request(self, method, params=None):
        self.next_id += 1
        payload = {'jsonrpc': '2.0', 'id': self.next_id, 'method': method}
        if params is not None:
            payload['params'] = params
        return self._post(payload)

    def initialize(self):
        result = self.request('initialize', {'protocolVersion': PROTOCOL_VERSION, 'capabilities': {},
                                             'clientInfo': {'name': 'aeonfall-editor-bridge', 'version': '1.0.0'}})
        if not isinstance(result, dict) or not isinstance(result.get('protocolVersion'), str):
            raise BridgeError('MCP initialize did not advertise a protocol version')
        self.protocol_version = result['protocolVersion']
        self.initialize_result = result
        self._post({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, notification=True)
        return result

    def discover(self):
        if self.initialize_result is None:
            self.initialize()
        tools, cursors, cursor = [], set(), None
        for _ in range(64):
            page = self.request('tools/list', {'cursor': cursor} if cursor else {})
            if not isinstance(page, dict) or not isinstance(page.get('tools'), list):
                raise BridgeError('MCP tools/list returned a malformed page')
            for item in page['tools']:
                if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not isinstance(item.get('inputSchema'), dict):
                    raise BridgeError('MCP advertised a malformed tool schema')
                tools.append(item)
            cursor = page.get('nextCursor')
            if not cursor:
                break
            if not isinstance(cursor, str) or cursor in cursors:
                raise BridgeError('MCP tool pagination cursor is invalid or repeated')
            cursors.add(cursor)
        else:
            raise BridgeError('MCP tool pagination exceeds the page limit')
        names = [item['name'] for item in tools]
        if len(names) != len(set(names)):
            raise BridgeError('MCP advertised duplicate tool names')
        return {'schema_version': 1, 'discovered_at_utc': timestamp(), 'endpoint': self.url,
                'server_initialize': self.initialize_result, 'tools': tools,
                'catalog_sha256': digest(tools)}

    def call(self, name, arguments):
        return self.request('tools/call', {'name': name, 'arguments': arguments})


def argument_errors(value, schema, path='$'):
    """Check common JSON Schema constraints; the editor validates the full schema."""
    errors = []
    kind = schema.get('type')
    kinds = kind if isinstance(kind, list) else [kind]
    matches = {'object': isinstance(value, dict), 'array': isinstance(value, list), 'string': isinstance(value, str),
               'integer': type(value) is int, 'number': type(value) in (int, float),
               'boolean': type(value) is bool, 'null': value is None}
    if kind and not any(matches.get(candidate, True) for candidate in kinds):
        return [f'{path}: expected {kind}']
    if 'enum' in schema and value not in schema['enum']:
        errors.append(f'{path}: value is outside the advertised enum')
    if isinstance(value, dict):
        properties = schema.get('properties', {})
        for key in schema.get('required', []):
            if key not in value:
                errors.append(f'{path}.{key}: required by the advertised schema')
        for key, item in value.items():
            if key in properties:
                errors.extend(argument_errors(item, properties[key], f'{path}.{key}'))
            elif schema.get('additionalProperties') is False:
                errors.append(f'{path}.{key}: not permitted by the advertised schema')
    elif isinstance(value, list) and isinstance(schema.get('items'), dict):
        for index, item in enumerate(value):
            errors.extend(argument_errors(item, schema['items'], f'{path}[{index}]'))
    return errors


def validate_plan(plan, catalog):
    if not isinstance(plan, dict) or plan.get('schema_version') != 1:
        raise BridgeError('Execution plan requires schema_version 1')
    tools = catalog.get('tools', [])
    if catalog.get('catalog_sha256') != digest(tools):
        raise BridgeError('Catalog digest mismatch')
    if plan.get('catalog_sha256') != catalog['catalog_sha256']:
        raise BridgeError('Plan is not pinned to this advertised tool catalog')
    steps = plan.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 64:
        raise BridgeError('Plan requires between one and 64 concrete steps')
    by_name = {item['name']: item for item in tools}
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise BridgeError(f'Step {index}: malformed record')
        name = step.get('tool_name')
        if name not in by_name:
            raise BridgeError(f'Step {index}: tool is absent from the live advertised catalog')
        schema = by_name[name]['inputSchema']
        if step.get('input_schema_sha256') != digest(schema):
            raise BridgeError(f'Step {index}: tool schema changed or was not pinned')
        arguments = step.get('arguments')
        if not isinstance(arguments, dict):
            raise BridgeError(f'Step {index}: arguments must be an object')
        errors = argument_errors(arguments, schema)
        if errors:
            raise BridgeError(f'Step {index}: ' + '; '.join(errors))
    return steps


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def execute_plan(client, plan, catalog, evidence_path):
    steps = validate_plan(plan, catalog)
    evidence = {'schema_version': 1, 'endpoint': client.url, 'started_at_utc': timestamp(),
                'catalog_sha256': catalog['catalog_sha256'], 'server_initialize': catalog['server_initialize'],
                'acceptance_claim': 'not_assessed', 'records': []}
    write_json(evidence_path, evidence)
    for index, step in enumerate(steps):
        record = {'step_index': index, 'tool_name': step['tool_name'], 'arguments': step['arguments'],
                  'input_schema_sha256': step['input_schema_sha256'], 'started_at_utc': timestamp(),
                  'requested_purpose': step.get('requested_purpose', '')}
        try:
            result = client.call(step['tool_name'], step['arguments'])
            if not isinstance(result, dict):
                raise BridgeError('MCP tools/call returned malformed result')
            record['result'] = result
            record['transport_status'] = 'tool_error' if result.get('isError') else 'response_received'
        except BridgeError as error:
            record['transport_status'], record['error'] = 'transport_error', str(error)
        record['finished_at_utc'] = timestamp()
        evidence['records'].append(record)
        write_json(evidence_path, evidence)
        if record['transport_status'] != 'response_received':
            raise BridgeError(f'Execution stopped at step {index}; actual failure is saved in {evidence_path}')
    evidence['finished_at_utc'] = timestamp()
    write_json(evidence_path, evidence)
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000/mcp')
    parser.add_argument('--timeout', type=float, default=15)
    commands = parser.add_subparsers(dest='command', required=True)
    discover = commands.add_parser('discover')
    discover.add_argument('--out', required=True)
    validate = commands.add_parser('validate-plan')
    validate.add_argument('--catalog', required=True)
    validate.add_argument('--plan', required=True)
    run = commands.add_parser('run-plan')
    run.add_argument('--plan', required=True)
    run.add_argument('--evidence', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'validate-plan':
            catalog = json.loads(Path(args.catalog).read_text())
            plan = json.loads(Path(args.plan).read_text())
            validate_plan(plan, catalog)
            print('Plan matches the saved advertised schemas. No editor request was sent.')
            return 0
        client = EditorMCP(args.url, args.timeout)
        catalog = client.discover()
        if args.command == 'discover':
            write_json(args.out, catalog)
            print(f'Discovered {len(catalog["tools"])} actual tools; schemas saved to {args.out}.')
        else:
            plan = json.loads(Path(args.plan).read_text())
            evidence = execute_plan(client, plan, catalog, args.evidence)
            print(f'Recorded {len(evidence["records"])} tool responses in {args.evidence}; engine acceptance remains not_assessed.')
        return 0
    except (BridgeError, OSError, ValueError) as error:
        print(f'UEFN MCP bridge failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
