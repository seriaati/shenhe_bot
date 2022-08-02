import aiosqlite
from discord import Locale, Member
from utility.apps.text_map.utils import get_user_locale
from utility.apps.text_map.TextMap import text_map

from utility.utils import default_embed, get_material


async def get_todo_embed(db: aiosqlite.Connection, user: Member, locale: Locale):
    user_locale = await get_user_locale(user.id, db)
    c = await db.cursor()
    await c.execute('SELECT item, count FROM todo WHERE user_id = ?', (user.id,))
    todo = await c.fetchall()
    if len(todo) == 0:
        embed = default_embed(message=text_map.get(204, locale, user_locale))
        embed.set_author(name=text_map.get(
            202, locale, user_locale), icon_url=user.avatar)
        return embed, True
    message = ''
    for index, tuple in enumerate(todo):
        item = tuple[0]
        count = tuple[1]
        message += f'{get_material(item)["emoji"]} {text_map.get_material_name(item, locale, user_locale)} x{count}\n'
    embed = default_embed(message=message)
    embed.set_author(name=text_map.get(202, locale, user_locale), icon_url=user.avatar)
    return embed, False
