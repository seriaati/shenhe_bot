from typing import List
from apps.genshin.custom_model import AbyssChamber, AbyssEnemy, AbyssFloor, AbyssHalf
from bs4 import BeautifulSoup
import aiohttp


async def get_abyss_enemies(session: aiohttp.ClientSession) -> List[AbyssFloor]:
    result = []
    async with session.get(
        "https://genshin-impact.fandom.com/wiki/Spiral_Abyss/Floors"
    ) as resp:
        html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    for floor_num in range(1, 13):
        f = soup.find(id=f"Floor_{floor_num}")
        if f is None:
            continue
        l_d = f.parent.next_sibling.next_sibling
        ley_line_disorders = []
        for li in l_d.li.ul.findAll("li"):
            ley_line_disorders.append(li.text)
        table = l_d.next_sibling.next_sibling.tbody
        chambers = []
        chamber_offset = 4 if floor_num <= 4 else 5
        for chamber_num in range(1, 4):
            chamber = AbyssChamber(
                num=chamber_num,
                enemy_level=int(
                    table.findAll("tr")[1 + chamber_offset * (chamber_num - 1)].td.text
                ),
                challenge_target=table.findAll("tr")[
                    2 + chamber_offset * (chamber_num - 1)
                ].td.text,
                halfs=[],
            )
            tables = []
            tables.append(table.findAll("tr")[3 + chamber_offset * (chamber_num - 1)].td)
            if chamber_offset == 5:
                tables.append(
                    table.findAll("tr")[4 + chamber_offset * (chamber_num - 1)].td
                )
            for index, enemy_table in enumerate(tables):
                half = AbyssHalf(num=index+1, enemies=[])
                for div in enemy_table.findAll(
                    "div", {"class": "card_with_caption hidden"}
                ):
                    card_caption = div.find("div", {"class": "card_caption"})
                    name = card_caption.text
                    card_text = div.find("div", {"class": "card_text"})
                    num = card_text.text
                    half.enemies.append(AbyssEnemy(name=name, num=num))
                chamber.halfs.append(half)
            chambers.append(chamber)
        result.append(
            AbyssFloor(
                num=floor_num, ley_line_disorders=ley_line_disorders, chambers=chambers
            )
        )
    return result
