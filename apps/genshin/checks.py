from typing import Optional

import asqlite
from discord import Interaction, Member, User, app_commands

from apps.genshin.utils import get_uid
from apps.text_map.utils import get_user_locale
from exceptions import NoCookie, NoUID, NoWishHistory


def check_account():
    """
    Checks if the user has an account. If the user has an account, they will have a UID, but they might not have a Cookie.
    """

    async def predicate(i: Interaction) -> bool:
        return await check_account_predicate(i)

    return app_commands.check(predicate)


async def check_account_predicate(
    i: Interaction, member: Optional[User | Member] = None
):
    user = member or i.namespace.member or i.user

    pool: asqlite.Pool = i.client.pool  # type: ignore
    async with pool.acquire() as db:
        async with db.execute(
            "SELECT uid FROM user_accounts WHERE user_id = ?", (user.id,)
        ) as c:
            uid = await c.fetchone()
    if uid is None:
        if user.id == i.user.id:
            raise NoUID(True)
        else:
            raise NoUID(False)
    else:
        return True


def check_cookie():
    """Checks if the current user account has a cookie."""

    async def predicate(i: Interaction) -> bool:
        return await check_cookie_predicate(i)

    return app_commands.check(predicate)


def check_wish_history():
    """Checks if the current user account has a wish history."""

    async def predicate(i: Interaction) -> bool:
        user = i.namespace.membr or i.user

        pool: asqlite.Pool = i.client.pool  # type: ignore
        async with pool.acquire() as db:
            async with db.execute(
                "SELECT wish_id FROM wish_history WHERE user_id = ? AND uid = ?",
                (user.id, await get_uid(i.user.id, pool)),
            ) as c:
                data = await c.fetchone()

        if data is None:
            raise NoWishHistory
        else:
            return True

    return app_commands.check(predicate)


async def check_cookie_predicate(
    i: Interaction, member: Optional[User | Member] = None
):
    await check_account_predicate(i, member)
    user = member or i.namespace.member or i.user

    pool: asqlite.Pool = i.client.pool  # type: ignore
    async with pool.acquire() as db:
        async with db.execute(
            "SELECT ltuid FROM user_accounts WHERE user_id = ? AND current = 1",
            (user.id,),
        ) as c:
            data = await c.fetchone()
            if data is None or data[0] is None:
                await c.execute(
                    "SELECT ltuid FROM user_accounts WHERE user_id = ? AND current = 0",
                    (user.id,),
                )
                if (await c.fetchone()) is None:
                    if user.id == i.user.id:
                        raise NoCookie(True, True)
                    else:
                        raise NoCookie(False, True)
                else:
                    if user.id == i.user.id:
                        raise NoCookie(True, False)
                    else:
                        raise NoCookie(False, False)
            else:
                return True
