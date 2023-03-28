import json
from typing import Dict

import asyncpg


async def read_json(pool: asyncpg.Pool, file_name: str) -> Dict:
    """Reads a json file from the database and returns it as a dict"""
    val = await pool.fetchval("SELECT file FROM json WHERE file_name = $1", file_name)
    return json.loads(val)


async def write_json(pool: asyncpg.Pool, file_name: str, data: Dict):
    """Writes a json file to the database"""
    await pool.execute(
        "INSERT INTO json (file_name, file) VALUES ($1, $2) ON CONFLICT (file_name) DO UPDATE SET file = $2",
        file_name,
        json.dumps(data),
    )


async def delete_json(pool: asyncpg.Pool, file_name: str):
    """Deletes a json file from the database"""
    await pool.execute("DELETE FROM json WHERE file_name = $1", file_name)
