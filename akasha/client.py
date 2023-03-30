import typing

import aiohttp
import asyncpg

from .endpoints import BASE_URL, Endpoint
from .model.build import Build
from .model.response import AkashaResponse


class AkashaAPI:
    def __init__(self, session: aiohttp.ClientSession, pool: asyncpg.Pool, debug: bool):
        self.session = session
        self.pool = pool
        self.debug = debug

    async def get_from_endpoint(
        self, endpoint: Endpoint
    ) -> typing.Dict[str, typing.Any]:
        async with self.session.get(f"{BASE_URL}/{endpoint.value}") as r:
            return await r.json()

    async def get_builds(self) -> AkashaResponse[Build]:
        response = await self.get_from_endpoint(Endpoint.BUILDS)
        return AkashaResponse(**response)
