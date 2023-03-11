import aiohttp
from typing import List


async def find_codes(session: aiohttp.ClientSession) -> List[str]:
    """Find redeem codes from Gaurav's API."""
    url = "https://genshin-redeem-code.vercel.app/codes"
    async with session.get(url) as r:
        data = await r.json()
        return [d["code"] for d in data]
