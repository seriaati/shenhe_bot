import asyncpg


async def get_profile_ver(user_id: int, pool: asyncpg.pool.Pool) -> int:
    return await pool.fetchval(
        "SELECT profile_ver FROM user_settings WHERE user_id = $1", user_id
    )
