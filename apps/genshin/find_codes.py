import aiohttp
from bs4 import BeautifulSoup
from typing import List

async def find_codes() -> List[str]:
    result: List[str] = []
    
    async with aiohttp.ClientSession() as session:
        url = "https://www.pockettactics.com/genshin-impact/codes"
        async with session.get(url) as r:
            soup = BeautifulSoup(await r.text(), "html.parser")
            uls = soup.find("div", {"class": "entry-content"})
            if uls is None:
                return result
            for ul in uls.findAll("ul"):
                for code in ul.findAll("strong"):
                    if code.text.strip().isupper():
                        result.append(code.text.strip())
                        
    return result