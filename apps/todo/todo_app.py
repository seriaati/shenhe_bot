from io import BytesIO
from typing import List, Tuple

import aiohttp
import aiosqlite
from discord import Embed, Interaction, Locale, User
from ambr.client import AmbrTopAPI
from ambr.models import Material
from apps.text_map.convert_locale import to_ambr_top
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, divide_chunks, get_user_appearance_mode
from discord.errors import InteractionResponded
from yelan.draw import draw_big_material_card, draw_todo_card
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale


async def get_todo_embed(
    db: aiosqlite.Connection,
    user: User,
    locale: Locale | str,
    session: aiohttp.ClientSession,
) -> Tuple[Embed | List[BytesIO], bool]:
    user_locale = await get_user_locale(user.id, db)
    locale = user_locale or locale
    c = await db.cursor()
    await c.execute("SELECT item, count FROM todo WHERE user_id = ?", (user.id,))
    todo = await c.fetchall()
    ambr = AmbrTopAPI(session, to_ambr_top(locale))
    if not todo:
        embed = default_embed(message=text_map.get(204, locale, user_locale))
        embed.set_author(
            name=text_map.get(202, locale, user_locale),
            icon_url=user.display_avatar.url,
        )
        return embed, True

    all_materials = []
    for _, tpl in enumerate(todo):
        item_id = tpl[0]
        num = tpl[1]
        if not item_id.isdigit():
            material = Material(id=0, name=item_id, icon="https://cdn-icons-png.flaticon.com/512/5893/5893002.png")
        else:
            material = await ambr.get_material(int(item_id))
        if not isinstance(material, Material):
            raise TypeError("Material is not Material")
        all_materials.append((material, int(num)))

    todo_cards = []
    all_materials = list(divide_chunks(all_materials, 7))
    for all_mat in all_materials:
        todo_cards.append(
            await draw_big_material_card(
                all_mat,
                "",
                "#C5EDFF",
                session,
                await get_user_appearance_mode(user.id, db),
                locale,
                False,
            )
        )
    return todo_cards, False


async def return_todo(
    result: Embed | List[BytesIO],
    i: Interaction,
    view,
    db: aiosqlite.Connection,
):
    try:
        await i.response.defer()
    except InteractionResponded:
        pass
    if isinstance(result, Embed):
        view.message = await i.edit_original_response(
            embed=result, view=view, attachments=[]
        )
    else:
        embeds = []
        for index in range(len(result)):
            embed = default_embed()
            embed.set_image(url=f"attachment://{index}.jpeg")
            embeds.append(embed)
        await GeneralPaginator(
            i, embeds, db, custom_children=view.children, files=result
        ).start(edit=True)
