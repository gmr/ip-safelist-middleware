"""Tests for IPSafeListMiddleware using unittest."""
import ipaddress
import json
import logging
import pathlib
import unittest
from unittest import mock

import fastapi
import httpx
from starlette import (
    applications,
    middleware,
    requests,
    responses,
    routing,
    testclient,
)

import ip_safelist_middleware

LOGGER = logging.getLogger(__name__)
DATA = pathlib.Path(__file__).parent / 'data'


def ok_endpoint(request: requests.Request) -> responses.PlainTextResponse:
    LOGGER.debug('Request: %r', request)
    return responses.PlainTextResponse('OK', status_code=200)


class TestCase(unittest.TestCase):
    def setUp(self):
        self.aws_ranges = self._aws_ranges()
        self.app = self._setup_app()

    def _aws_ranges(
            self) -> set[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        with (DATA / 'ip-ranges.json').open('r') as handle:
            data = json.load(handle)
        ranges: set[ipaddress.IPv4Network | ipaddress.IPv6Network] = {
            ipaddress.IPv4Network(prefix['ip_prefix'])
            for prefix in data['prefixes'] if prefix['region'] == 'us-east-1'
        }
        self.assertGreater(len(ranges), 0)
        return ranges

    def _new_client(self,
                    app: applications.Starlette | None = None,
                    base_url: str = 'http://testserver',
                    raise_server_exceptions: bool = True,
                    root_path: str = '',
                    cookies: httpx._types.CookieTypes | None = None,
                    headers: dict[str, str] | None = None,
                    follow_redirects: bool = True,
                    client: tuple[str, int] = ('127.0.0.1', 50000)):
        return testclient.TestClient(
            app=app or self.app,
            base_url=base_url,
            raise_server_exceptions=raise_server_exceptions,
            root_path=root_path,
            cookies=cookies,
            headers=headers,
            follow_redirects=follow_redirects,
            client=client)

    def _setup_app(self) -> applications.Starlette:
        with mock.patch(
                'ip_safelist_middleware.'
                'IPSafeListMiddleware._load_from_amazon') as load_from_amazon:
            load_from_amazon.return_value = self.aws_ranges

            app = applications.Starlette(
                routes=[
                    routing.Route('/api/test', endpoint=ok_endpoint),
                    routing.Route('/health', endpoint=ok_endpoint)
                ],
                middleware=[
                    middleware.Middleware(
                        ip_safelist_middleware.IPSafeListMiddleware,
                        list_items=[
                            ip_safelist_middleware.ListItem(
                                path=r'^/api/.*$',
                                type=[
                                    ip_safelist_middleware.ListType.aws,
                                    ip_safelist_middleware.ListType.env
                                ]),
                            ip_safelist_middleware.ListItem(
                                path=r'^/health.*$',
                                type=[ip_safelist_middleware.ListType.env]),
                        ],
                        aws_enabled=True,
                        aws_regions=['us-east-1'],
                        networks=['10.0.0.0/8', '192.168.0.0/24'])
                ])
        return app

    def test_default_setup(self):
        with mock.patch(
                'ip_safelist_middleware.'
                'IPSafeListMiddleware._load_from_amazon') as load_from_amazon:
            load_from_amazon.side_effect = RuntimeError('Should not load')
            ip_safelist = ip_safelist_middleware.IPSafeListMiddleware(
                app=mock.MagicMock(spec=fastapi.FastAPI),
                aws_enabled=False,
                networks={'10.0.0.0/8', '192.168.0.0/24'})

        self.assertEqual(len(ip_safelist._items), 1)
        self.assertEqual(ip_safelist._items[0].path, r'^/.*$')
        self.assertEqual(ip_safelist._items[0].type,
                         ip_safelist_middleware.ListType.env)

    def test_complex_setup(self):
        with mock.patch(
                'ip_safelist_middleware.'
                'IPSafeListMiddleware._load_from_amazon') as load_from_amazon:
            load_from_amazon.return_value = self._aws_ranges()
            ip_safelist = ip_safelist_middleware.IPSafeListMiddleware(
                app=mock.MagicMock(spec=fastapi.FastAPI),
                list_items=[
                    ip_safelist_middleware.ListItem(
                        path=r'^/api/.*$',
                        type=[
                            ip_safelist_middleware.ListType.aws,
                            ip_safelist_middleware.ListType.env
                        ]),
                    ip_safelist_middleware.ListItem(
                        path=r'^/health.*$',
                        type=ip_safelist_middleware.ListType.env),
                ],
                aws_enabled=True,
                aws_regions=['us-east-1'],
                networks={'10.0.0.0/8', '192.168.0.0/24'})

        self.assertEqual(len(ip_safelist._items), 2)
        self.assertEqual(len(ip_safelist._items[0].type), 2)  # type: ignore[arg-type]
        self.assertIsInstance(ip_safelist._items[1].type,
                              ip_safelist_middleware.ListType)

        result = ip_safelist._get_safe_list(
            ip_safelist_middleware.ListType.aws)
        self.assertSetEqual(result, self.aws_ranges)

        env_ranges = {
            ipaddress.IPv4Network('10.0.0.0/8'),
            ipaddress.IPv4Network('192.168.0.0/24')
        }
        result = ip_safelist._get_safe_list(
            ip_safelist_middleware.ListType.env)
        self.assertSetEqual(result, env_ranges)

    def test_env_only_setup(self):
        with mock.patch(
                'ip_safelist_middleware.'
                'IPSafeListMiddleware._load_from_amazon') as load_from_amazon:
            load_from_amazon.side_effect = RuntimeError('Should not load')
            ip_safelist = ip_safelist_middleware.IPSafeListMiddleware(
                app=mock.MagicMock(spec=fastapi.FastAPI),
                list_items=[
                    ip_safelist_middleware.ListItem(
                        path=r'^/health.*$',
                        type=ip_safelist_middleware.ListType.env)
                ],
                aws_enabled=False,
                networks={'10.0.0.0/8', '192.168.0.0/24'})

        self.assertEqual(len(ip_safelist._items), 1)
        self.assertEqual(ip_safelist._items[0].type,
                         ip_safelist_middleware.ListType.env)
        self.assertEqual(len(ip_safelist._env_list), 2)

    def test_env_bad_network(self):
        ip_safelist = ip_safelist_middleware.IPSafeListMiddleware(
            app=mock.MagicMock(spec=fastapi.FastAPI),
            list_items=[
                ip_safelist_middleware.ListItem(
                    path=r'^/health.*$',
                    type=ip_safelist_middleware.ListType.env)
            ],
            aws_enabled=False,
            networks={'576', '192.168.0.0/24'})
        self.assertEqual(len(ip_safelist._items), 1)
        self.assertEqual(ip_safelist._items[0].type,
                         ip_safelist_middleware.ListType.env)
        self.assertEqual(len(ip_safelist._env_list), 1)

    def test_env_single_network(self):
        app = applications.Starlette(
            routes=[
                routing.Route('/api/test', endpoint=ok_endpoint),
                routing.Route('/health', endpoint=ok_endpoint)
            ],
            middleware=[
                middleware.Middleware(
                    ip_safelist_middleware.IPSafeListMiddleware,
                    list_items=[
                        ip_safelist_middleware.ListItem(
                            path=r'^/health.*$',
                            type=ip_safelist_middleware.ListType.env)
                    ],
                    aws_enabled=False,
                    networks='192.168.0.0/24')
            ])

        test_client = self._new_client(app, client=('192.168.0.200', 50000))
        response = test_client.get('/health')
        self.assertEqual(response.status_code, 200)

    def test_env_empty_networks(self):
        ip_safelist = ip_safelist_middleware.IPSafeListMiddleware(
            app=mock.MagicMock(spec=fastapi.FastAPI),
            list_items=[
                ip_safelist_middleware.ListItem(
                    path=r'^/health.*$',
                    type=ip_safelist_middleware.ListType.env)
            ],
            aws_enabled=False)
        self.assertEqual(len(ip_safelist._items), 1)
        self.assertEqual(ip_safelist._items[0].type,
                         ip_safelist_middleware.ListType.env)
        self.assertEqual(len(ip_safelist._env_list), 0)

    def test_request_from_localhost(self):
        test_client = self._new_client(client=('127.0.0.1', 50000))
        response = test_client.get('/api/test')
        self.assertEqual(response.status_code, 403)

    def test_request_from_local_network(self):
        test_client = self._new_client(client=('192.168.0.200', 50000))
        response = test_client.get('/api/test')
        self.assertEqual(response.status_code, 200)

    def test_request_from_aws_network(self):
        test_client = self._new_client(client=('3.237.175.77', 50000))
        response = test_client.get('/api/test')
        self.assertEqual(response.status_code, 200)
        response = test_client.get('/health')
        self.assertEqual(response.status_code, 403)

    def test_request_from_aws_network_403(self):
        test_client = self._new_client(client=('3.237.175.77', 50000))
        response = test_client.get('/health')
        self.assertEqual(response.status_code, 403)

    def test_request_from_bad_client(self):
        test_client = self._new_client(client=('fake-host', 50000))
        response = test_client.get('/health')
        self.assertEqual(response.status_code, 403)

    def test_allow_list_type_setup(self):
        with mock.patch(
                'ip_safelist_middleware.'
                'IPSafeListMiddleware._load_from_amazon') as load_from_amazon:
            load_from_amazon.side_effect = RuntimeError('Should not load')
            ip_safelist = ip_safelist_middleware.IPSafeListMiddleware(
                app=mock.MagicMock(spec=fastapi.FastAPI),
                list_items=[
                    ip_safelist_middleware.ListItem(
                        path=r'^/public/.*$',
                        type=ip_safelist_middleware.ListType.allow)
                ],
                aws_enabled=False)

        self.assertEqual(len(ip_safelist._items), 1)
        self.assertEqual(ip_safelist._items[0].type,
                         ip_safelist_middleware.ListType.allow)

    def test_allow_list_type_allows_any_ip(self):
        app = applications.Starlette(
            routes=[
                routing.Route('/public/data', endpoint=ok_endpoint),
                routing.Route('/private/data', endpoint=ok_endpoint)
            ],
            middleware=[
                middleware.Middleware(
                    ip_safelist_middleware.IPSafeListMiddleware,
                    list_items=[
                        ip_safelist_middleware.ListItem(
                            path=r'^/public/.*$',
                            type=ip_safelist_middleware.ListType.allow),
                        ip_safelist_middleware.ListItem(
                            path=r'^/private/.*$',
                            type=ip_safelist_middleware.ListType.env)
                    ],
                    aws_enabled=False,
                    networks='192.168.0.0/24')
            ])

        # Test that /public/* allows any IP address
        test_client = self._new_client(app, client=('1.2.3.4', 50000))
        response = test_client.get('/public/data')
        self.assertEqual(response.status_code, 200)

        # Test that /private/* still respects IP restrictions
        response = test_client.get('/private/data')
        self.assertEqual(response.status_code, 403)

        # Test that allowed IP can access both
        test_client = self._new_client(app, client=('192.168.0.200', 50000))
        response = test_client.get('/public/data')
        self.assertEqual(response.status_code, 200)
        response = test_client.get('/private/data')
        self.assertEqual(response.status_code, 200)

    def test_allow_list_type_mixed_with_other_types(self):
        with mock.patch(
                'ip_safelist_middleware.'
                'IPSafeListMiddleware._load_from_amazon') as load_from_amazon:
            load_from_amazon.side_effect = RuntimeError('Should not load')
            ip_safelist = ip_safelist_middleware.IPSafeListMiddleware(
                app=mock.MagicMock(spec=fastapi.FastAPI),
                list_items=[
                    ip_safelist_middleware.ListItem(
                        path=r'^/mixed/.*$',
                        type=[
                            ip_safelist_middleware.ListType.allow,
                            ip_safelist_middleware.ListType.env
                        ])
                ],
                aws_enabled=False,
                networks='192.168.0.0/24')

        # Verify setup
        self.assertEqual(len(ip_safelist._items), 1)
        self.assertEqual(len(ip_safelist._items[0].type), 2)  # type: ignore[arg-type]
        self.assertIn(ip_safelist_middleware.ListType.allow,
                      ip_safelist._items[0].type)  # type: ignore[arg-type]
        self.assertIn(ip_safelist_middleware.ListType.env,
                      ip_safelist._items[0].type)  # type: ignore[arg-type]

        # Test that mixed type with allow permits any IP
        app = applications.Starlette(
            routes=[routing.Route('/mixed/data', endpoint=ok_endpoint)],
            middleware=[
                middleware.Middleware(
                    ip_safelist_middleware.IPSafeListMiddleware,
                    list_items=[
                        ip_safelist_middleware.ListItem(
                            path=r'^/mixed/.*$',
                            type=[
                                ip_safelist_middleware.ListType.allow,
                                ip_safelist_middleware.ListType.env
                            ])
                    ],
                    aws_enabled=False,
                    networks='192.168.0.0/24')
            ])

        test_client = self._new_client(app, client=('1.2.3.4', 50000))
        response = test_client.get('/mixed/data')
        self.assertEqual(response.status_code, 200)
