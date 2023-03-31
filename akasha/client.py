import logging
import typing

import aiohttp

from .endpoints import BASE_URL, Endpoint
from .model.build import Build
from .model.option import Filter, Option, Page
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
        options: typing.Optional[typing.List[Option]] = None,
    ) -> typing.Dict[str, typing.Any]:
        logging.debug(f"Getting from {endpoint.value}, options: {options}")
        url = f"{BASE_URL}/{endpoint.value}"

        # format : ?filter=[name]Zhongli&p=lt|268.20999791693447
        if options:
            url += "?"
            for option in options:
                if f"{option.option_name}=" not in url and option.value is not None:
                    if isinstance(option, Filter):
                        url += f"{option.option_name}="
                    elif isinstance(option, Page):
                        url += f"&{option.option_name}="
                if isinstance(option, Filter):
                    url += f"[{option.type.value}]{option.value}"
                elif isinstance(option, Page) and option.value is not None:
                    url += f"{option.type.value}|{option.value}"

        logging.debug(f"URL: {url}")
        async with self.session.get(url) as r:
            return await r.json()

    async def get_builds(
        self, *, options: typing.Optional[typing.List[Option]] = None
    ) -> AkashaResponse[Build]:
        logging.debug("Getting builds")
        response = await self.get_from_endpoint(Endpoint.BUILDS, options=options)
        return AkashaResponse(**response)
