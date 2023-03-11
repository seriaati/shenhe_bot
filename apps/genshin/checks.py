from typing import Optional

import asyncpg
from discord import Interaction, Member, User, app_commands

from apps.genshin.utils import get_uid
from exceptions import NoCookie, NoUID, NoWishHistory


def check_account():
    """Checks if the user has an account. If the user has an account, they will have a UID, but they might not have a Cookie."""

    async def predicate(i: Interaction) -> bool:
        return await check_account_predicate(i)

    return app_commands.check(predicate)


async def check_account_predicate(
    i: Interaction, member: Optional[User | Member] = None
):
    user = member or i.namespace.member or i.user

    pool: asyncpg.Pool = i.client.pool  # type: ignore
    uid = await pool.fetchval(
        "SELECT uid FROM user_accounts WHERE user_id = $1", user.id
    )
    if uid is None:
        if user.id == i.user.id:
            raise NoUID(True)
        raise NoUID(False)
    return True


def check_cookie():
    """Checks if the current user account has a cookie."""

    async def predicate(i: Interaction) -> bool:
        return await check_cookie_predicate(i)

    return app_commands.check(predicate)


def check_wish_history():
    """Checks if the current user account has a wish history."""

    async def predicate(i: Interaction) -> bool:
        user = i.namespace.member or i.user

        pool: asyncpg.Pool = i.client.pool  # type: ignore
        data = await pool.fetchval(
            "SELECT wish_id FROM wish_history WHERE user_id = $1 AND uid = $2",
            user.id,
            await get_uid(i.user.id, pool),
        )

        if data is None:
            raise NoWishHistory
        return True

    return app_commands.check(predicate)


async def check_cookie_predicate(
    i: Interaction, member: Optional[User | Member] = None
):
    await check_account_predicate(i, member)
    user = member or i.namespace.member or i.user

    pool: asyncpg.Pool = i.client.pool  # type: ignore
    ltuid = await pool.fetchval(
        "SELECT ltuid FROM user_accounts WHERE user_id = $1 AND current = true", user.id
    )
    if ltuid is None:
        ltuid = await pool.fetchval(
            "SELECT ltuid FROM user_accounts WHERE user_id = $1 AND current = false",
            user.id,
        )
        if ltuid is None:
            if user.id == i.user.id:
                raise NoCookie(True, True)
            raise NoCookie(False, True)
        if user.id == i.user.id:
            raise NoCookie(True, False)
        raise NoCookie(False, False)
    return True
