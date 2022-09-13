import aiosqlite
import sentry_sdk
from apps.genshin.genshin_app import GenshinApp
from apps.genshin.user_model import ShenheUser
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from discord import Interaction, app_commands, User, Member
from utility.utils import error_embed, log

import genshin


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
    if (await c.fetchone()) is None:
        await i.response.send_message(
            embed=error_embed(message=text_map.get(572, locale)).set_author(
                name=text_map.get(571, locale), icon_url=user.display_avatar.url
            ),
            ephemeral=True,
        )
        return False
    else:
        check = await validate_account(i, True)
        return check


def check_cookie():
    """Checks if the current user account has a cookie."""

    async def predicate(i: Interaction) -> bool:
        check = await check_cookie_predicate(i)
        return check

    return app_commands.check(predicate)


async def check_cookie_predicate(i: Interaction, user: User | Member = None) -> bool:
    check = await check_account_predicate(i)
    if not check:
        return False
    user = user or i.user
    locale = (await get_user_locale(i.user.id, i.client.db)) or i.locale
    c: aiosqlite.Cursor = await i.client.db.cursor()
    await c.execute(
        "SELECT ltuid FROM user_accounts WHERE user_id = ? AND current = 1",
        (user.id,),
    )
    if (await c.fetchone())[0] is None:
        await c.execute(
            "SELECT ltuid FROM user_accounts WHERE user_id = ? AND current = 0",
            (user.id,),
        )
        if (await c.fetchone()) is None:
            await i.response.send_message(
                embed=error_embed(message=text_map.get(572, locale)).set_author(
                    name=text_map.get(573, locale),
                    icon_url=user.display_avatar.url,
                ),
                ephemeral=True,
            )
        else:
            await i.response.send_message(
                embed=error_embed(message=text_map.get(575, locale)).set_author(
                    name=text_map.get(574, locale),
                    icon_url=user.display_avatar.url,
                ),
                ephemeral=True,
            )
        return False
    else:
        check = await validate_account(i, False)
        return check


async def validate_account(i: Interaction, only_uid: bool, user: User | Member = None) -> bool:
    """Checks if the user has a valid Cookie and the data is public."""
    user = user or i.user
    genshin_app = GenshinApp(i.client.db, i.client)
    user_locale = await get_user_locale(i.user.id, i.client.db)
    locale = user_locale or i.locale
    if only_uid:
        shenhe_user = ShenheUser(
            client=i.client.genshin_client,
            uid= await genshin_app.get_user_uid(i.user.id),
            discord_user=user,
            user_locale=user_locale,
            china=0,
        )
    else:
        shenhe_user = await genshin_app.get_user_cookie(user.id, i.locale)
    try:
        await shenhe_user.client.get_partial_genshin_user(shenhe_user.uid)
    except genshin.errors.DataNotPublic:
        await i.response.send_message(
            error_embed(
                message=text_map.get(21, locale, shenhe_user.user_locale)
            ).set_author(
                name=text_map.get(22, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
        )
        return False
    except genshin.errors.InvalidCookies:
        await i.response.send_message(
            error_embed(
                message=text_map.get(35, locale, shenhe_user.user_locale)
            ).set_author(
                name=text_map.get(36, locale, shenhe_user.user_locale),
                icon_url=shenhe_user.discord_user.display_avatar.url,
            )
        )
        return False
    except Exception as e:
        sentry_sdk.capture_exception(e)
        log.warning(f"An error occurred while validating account for {user.id}:\n{e}")
    return True
