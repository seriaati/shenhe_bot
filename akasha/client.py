import logging
import typing

import aiohttp

from .endpoints import BASE_URL, Endpoint
from .model.build import Build
from .model.filter import Filter
from .model.response import AkashaResponse


class AkashaAPI:
    def __init__(self, session: aiohttp.ClientSession, *, debug: bool = False):
        self.session = session
        self.debug = debug
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)

    async def get_from_endpoint(
        self,
        endpoint: Endpoint,
        *,
        filters: typing.Optional[typing.List[Filter]] = None,
    ) -> typing.Dict[str, typing.Any]:
        logging.debug(f"Getting from {endpoint.value}, filters: {filters}")
        url = f"{BASE_URL}/{endpoint.value}"

        # format : [filter_name]filter_value
        if filters:
            url += "?filter="
            for filter in filters:
                url += f"[{filter.type.value}]{filter.value}"

        async with self.session.get(url) as r:
            return await r.json()

    async def get_builds(
        self, *, filters: typing.Optional[typing.List[Filter]] = None
    ) -> AkashaResponse[Build]:
        logging.debug("Getting builds")
        response = await self.get_from_endpoint(Endpoint.BUILDS, filters=filters)
        return AkashaResponse(**response)
