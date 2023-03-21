import asyncpg
import typing


async def get_profile_ver(user_id: int, pool: asyncpg.pool.Pool) -> int:
    return await pool.fetchval(
        "SELECT profile_ver FROM user_settings WHERE user_id = $1", user_id
    )


async def get_user_appearance_mode(user_id: int, pool: asyncpg.Pool) -> bool:
    dark_mode: typing.Optional[bool] = await pool.fetchval(
        "SELECT dark_mode FROM user_settings WHERE user_id = $1", user_id
    )
    if dark_mode is None:
        return False
    return dark_mode
