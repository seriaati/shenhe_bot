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
