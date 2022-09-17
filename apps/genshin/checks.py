import aiosqlite
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import Interaction, app_commands, User, Member
from utility.utils import error_embed


def check_account():
    """
    Checks if the user has an account. If the user has an account, they will have a UID, but they might not have a Cookie.
    """

    async def predicate(i: Interaction) -> bool:
        check = await check_account_predicate(i)
        return check

    return app_commands.check(predicate)


async def check_account_predicate(i: Interaction, user: User | Member = None) -> bool:
    user = user or i.user
    locale = (await get_user_locale(i.user.id, i.client.db)) or i.locale
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute("SELECT uid FROM user_accounts WHERE user_id = ?", (user.id,))
    uid = await c.fetchone()
    if uid is None:
        await i.response.send_message(
            embed=error_embed(message=text_map.get(572, locale)).set_author(
                name=text_map.get(571 if user.id == i.user.id else 579, locale),
                icon_url=user.display_avatar.url,
            ),
            ephemeral=True
        )
        return False
    else:
        return True


def check_cookie():
    """Checks if the current user account has a cookie."""

    async def predicate(i: Interaction) -> bool:
        check = await check_cookie_predicate(i)
        return check

    return app_commands.check(predicate)


async def check_cookie_predicate(i: Interaction, user: User | Member = None) -> bool:
    check = await check_account_predicate(i, user or i.user)
    if not check:
        return False
    user = user or i.user
    locale = (await get_user_locale(i.user.id, i.client.db)) or i.locale
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute(
        "SELECT ltuid FROM user_accounts WHERE user_id = ? AND current = 1",
        (user.id,),
    )
    data = await c.fetchone()
    if data is None or data[0] is None:
        await c.execute(
            "SELECT ltuid FROM user_accounts WHERE user_id = ? AND current = 0",
            (user.id,),
        )
        if (await c.fetchone()) is None:
            await i.response.send_message(
                embed=error_embed(message=text_map.get(572, locale)).set_author(
                    name=text_map.get(573 if user.id == i.user.id else 580, locale),
                    icon_url=user.display_avatar.url,
                ),
                ephemeral=True,
            )
        else:
            await i.response.send_message(
                embed=error_embed(message=text_map.get(575, locale)).set_author(
                    name=text_map.get(574 if user.id == i.user.id else 581, locale),
                    icon_url=user.display_avatar.url,
                ),
                ephemeral=True,
            )
        return False
    else:
        return True