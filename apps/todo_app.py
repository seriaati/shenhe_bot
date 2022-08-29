from io import BytesIO
from typing import List, Tuple

import aiohttp
import aiosqlite
from discord import Embed, Interaction, Locale, Member
from utility.paginator import GeneralPaginator
from utility.utils import default_embed

from apps.draw import draw_todo_card
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale


async def get_todo_embed(
    db: aiosqlite.Connection,
    user: Member,
    locale: Locale,
    session: aiohttp.ClientSession,
) -> Tuple[Embed | List[BytesIO], bool]:
    user_locale = await get_user_locale(user.id, db)
    c = await db.cursor()
    await c.execute("SELECT item, count FROM todo WHERE user_id = ?", (user.id,))
    todo = await c.fetchall()
    if len(todo) == 0:
        embed = default_embed(message=text_map.get(204, locale, user_locale))
        embed.set_author(
            name=text_map.get(202, locale, user_locale), icon_url=user.display_avatar.url
        )
        return embed, True
    else:
        todo_cards = await draw_todo_card(todo, user_locale or locale, session)
        return todo_cards, False


async def return_todo(
    result: Embed | List[BytesIO],
    i: Interaction,
    view,
    db: aiosqlite.Connection,
):
    interacted = i.response.is_done()
    if isinstance(result, Embed):
        if interacted:
            await i.edit_original_response(embed=result, view=view, attachments=[])
        else:
            await i.response.edit_message(embed=result, view=view, files=[])
    else:
        embeds = []
        for index in range(len(result)):
            embed = default_embed()
            embed.set_image(url=f"attachment://{index}.jpeg")
            embeds.append(embed)
        await GeneralPaginator(
            i, embeds, db, custom_children=view.children, files=result
        ).start(edit=interacted)
    view.message = await i.original_response()
