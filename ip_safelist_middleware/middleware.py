import ipaddress
import logging
import time

import httpx
import pydantic
import pydantic_settings
from starlette import responses, types

from ip_safelist_middleware import __version__, models

LOGGER = logging.getLogger('ip_safelist_middleware')

_AWS_IP_URL = 'https://ip-ranges.amazonaws.com/ip-ranges.json'
_HTTP_HEADERS = {'User-Agent': f'ip-safelist-middleware/{__version__}'}

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
IPNetworks = ipaddress.IPv4Network | ipaddress.IPv6Network


class _Settings(pydantic_settings.BaseSettings):
    aws_enabled: bool = False
    aws_regions: list[str] = ['us-east-1', 'us-east-2']
    networks: set[IPNetworks] | None = None
    status_code: int = 403
    status_message: str = 'Forbidden'

    model_config = pydantic_settings.SettingsConfigDict(
        env_prefix='IP_SAFELIST_', case_sensitive=False)

    @pydantic.field_validator('networks', mode='before')
    @classmethod
    def parse_comma_separated_string(cls, value: str | None) \
            -> set[IPNetworks] | None:
        if isinstance(value, str):
            return {
                ipaddress.ip_network(item.strip())
                for item in value.split(',')
            }
        return value


class IPSafeListMiddleware:
    def __init__(self,
                 app: types.ASGIApp,
                 list_items: list[models.ListItem] | None = None,
                 aws_enabled: bool | None = None,
                 aws_regions: list[str] | None = None,
                 networks: set[str] | str | None = None,
                 status_code: int | None = None,
                 status_message: str | None = None) -> None:
        self._settings = _Settings()
        if isinstance(networks, str):
            networks = {networks}
        for key, value in {
                'aws_enabled': aws_enabled,
                'aws_regions': aws_regions,
                'networks': {
                    value
                    for value in {
                        self._convert_to_network(network)
                        for network in networks
                    } if value
                } if networks else networks,
                'status_code': status_code,
                'status_message': status_message
        }.items():
            if value is not None:
                self._settings.__setattr__(key, value)
        LOGGER.debug('Settings %r', self._settings.model_dump())
        self.app = app

        if not list_items:  # Default behavior if no list items passed
            list_items = [
                models.ListItem(
                    path=r"^/.*$",
                    type=models.ListType.env,
                )
            ]

        self._items = list_items
        if self._settings.aws_enabled:
            self._aws_list = self._load_from_amazon()
        else:
            self._aws_list = set()
        self._env_list = self._load_from_environment()

    async def __call__(self, scope: types.Scope, receive: types.Receive,
                       send: types.Send) -> None:
        """Validate the Client IP is in the Safelist"""
        if scope['type'] != 'http':  # pragma: nocover
            return await self.app(scope, receive, send)
        client_ip = self._get_request_address(scope['client'][0])
        if client_ip:
            for item in self._items:
                if item.regex.search(scope['path']) \
                        and self._is_in_safe_list(item, client_ip):
                    return await self.app(scope, receive, send)

        LOGGER.debug('Returning %s to %s', self._settings.status_code,
                     client_ip)
        response = responses.PlainTextResponse(
            self._settings.status_message,
            status_code=self._settings.status_code)
        await response(scope, receive, send)

    @staticmethod
    def _convert_to_network(value: str) -> IPNetworks | None:
        try:
            return ipaddress.ip_network(value)
        except ValueError as err:
            LOGGER.error('Error parsing IP network (%s): %s', value, err)
            return None

    def _is_in_safe_list(self, item: models.ListItem, client_ip: IPAddress) \
            -> bool:
        """Return True if the client IP is in the safe list."""
        safe_list = set()
        if isinstance(item.type, models.ListType):
            safe_list = self._get_safe_list(item.type)
        elif isinstance(item.type, list):
            for item_type in item.type:
                safe_list.update(self._get_safe_list(item_type))
        for network in safe_list:
            if client_ip in network:
                LOGGER.debug('%s is trusted in %s', client_ip, network)
                return True
        return False

    def _get_safe_list(self, item_type: models.ListType) -> set[IPNetworks]:
        """Return the safe list based on the type"""
        if item_type == models.ListType.aws:
            return self._aws_list
        return self._env_list

    @staticmethod
    def _get_request_address(addr: str) -> IPAddress | None:
        """Return the client IP address as an IPv4Address object."""
        try:
            return ipaddress.ip_address(addr)
        except ValueError as err:
            LOGGER.error('Error parsing IP address (%s): %s', addr, err)
            return None

    def _load_from_amazon(self, transport: httpx.BaseTransport | None = None) \
            -> set[IPNetworks]:
        """Load safe list from Amazon IP Ranges."""
        LOGGER.debug('Loading Safelist IP Ranges from Amazon (%s)',
                     self._settings.aws_regions)
        start = time.time()
        networks: set[IPNetworks] = set()

        # Use context manager to ensure client is properly closed
        with httpx.Client(headers=_HTTP_HEADERS,
                          transport=transport) as client:
            response = client.get(_AWS_IP_URL)
            response.raise_for_status()
            for prefix in response.json()['prefixes']:
                if prefix['region'] in self._settings.aws_regions:
                    networks.add(ipaddress.IPv4Network(prefix['ip_prefix']))
            for prefix in response.json()['ipv6_prefixes']:
                if prefix['region'] in self._settings.aws_regions:
                    networks.add(ipaddress.IPv6Network(prefix['ipv6_prefix']))

        LOGGER.debug('Loaded %i networks in %0.2f seconds', len(networks),
                     time.time() - start)
        return networks

    def _load_from_environment(self) -> set[IPNetworks]:
        """Load comma delimited safe list from environment variable."""
        LOGGER.debug('ENV Safelist: %r', self._settings.networks)
        return self._settings.networks or set()
