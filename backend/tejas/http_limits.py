"""Bound JSON before parsing and reject ambiguous bodies before mutation handlers.
Multipart uploads retain their route-level streamed PDF bound. Edge WAF limits remain separate.
"""
import json
from .contracts import error_response

MAX_JSON_BYTES = 1024 * 1024
MAX_DEPTH = 40


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON keys are not accepted.')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Non-finite JSON numbers are not accepted.')


class JsonBodyLimits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get('headers', []))
        if scope['type'] != 'http' or scope.get('method') not in ('POST', 'PUT', 'PATCH') or b'application/json' not in headers.get(b'content-type', b''):
            return await self.app(scope, receive, send)
        async def reject(message, status):
            await error_response(message, status, 'invalid_request_body')(scope, receive, send)
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await reject('Invalid request length.', 400)
        if length > MAX_JSON_BYTES:
            return await reject('JSON request exceeds the 1 MB limit.', 413)
        chunks, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            size += len(chunk)
            if size > MAX_JSON_BYTES:
                return await reject('JSON request exceeds the 1 MB limit.', 413)
            chunks.append(chunk)
            if not message.get('more_body', False):
                break
        body = b''.join(chunks)
        if body:
            try:
                value = json.loads(body, object_pairs_hook=unique_object, parse_constant=reject_constant)
                stack = [(value, 0)]
                while stack:
                    item, depth = stack.pop()
                    if depth > MAX_DEPTH:
                        raise ValueError('JSON is nested too deeply.')
                    if isinstance(item, dict):
                        stack.extend((v, depth + 1) for v in item.values())
                    elif isinstance(item, list):
                        stack.extend((v, depth + 1) for v in item)
            except (ValueError, RecursionError, UnicodeDecodeError):
                return await reject('Invalid JSON: check syntax, unique keys, finite numbers and nesting depth.', 400)
        delivered = False
        async def replay():
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {'type': 'http.request', 'body': body, 'more_body': False}
        await self.app(scope, replay, send)
