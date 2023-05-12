import typing

import asyncpg


async def create_user_settings(user_id: int, pool: asyncpg.pool.Pool) -> None:
    await pool.execute(
        "INSERT INTO user_settings (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
        user_id,
    )


async def get_profile_ver(user_id: int, pool: asyncpg.pool.Pool) -> int:
    ver: typing.Optional[int] = await pool.fetchval(
        "SELECT profile_ver FROM user_settings WHERE user_id = $1", user_id
    )
    if ver is None:
        return 2
    return ver


async def get_user_theme(user_id: int, pool: asyncpg.Pool) -> bool:
    dark_mode: typing.Optional[bool] = await pool.fetchval(
        "SELECT dark_mode FROM user_settings WHERE user_id = $1", user_id
    )
    if dark_mode is None:
        return False
    return dark_mode


async def get_user_lang(user_id: int, pool: asyncpg.Pool) -> typing.Optional[str]:
    user_locale = await pool.fetchval(
        "SELECT lang FROM user_settings WHERE user_id = $1", user_id
    )
    return user_locale


async def get_user_notif(user_id: int, pool: asyncpg.Pool) -> bool:
    notification: typing.Optional[bool] = await pool.fetchval(
        "SELECT notification FROM user_settings WHERE user_id = $1", user_id
    )
    if notification is None:
        return True
    return notification


async def get_user_auto_redeem(user_id: int, pool: asyncpg.Pool) -> bool:
    auto_redeem: typing.Optional[bool] = await pool.fetchval(
        "SELECT auto_redeem FROM user_settings WHERE user_id = $1", user_id
    )
    if auto_redeem is None:
        return False
    return auto_redeem