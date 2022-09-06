import aiohttp
from discord import SelectOption

async def get_waifu_im_tags(sese: int, session: aiohttp.ClientSession):
    async with session.get("https://api.waifu.im/tags/?full=on") as r:
        tags = await r.json()
    choices = []
    for tag in tags["versatile"]:
        choices.append(SelectOption(label=tag["name"]))
    if sese == 1:
        for tag in tags["nsfw"]:
            choices.append(SelectOption(label=tag["name"]))
    return choices