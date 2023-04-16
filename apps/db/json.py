import json
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from apps.db.tables import Json


async def read_json(engine: AsyncEngine, file_name: str) -> Optional[Dict[str, Any]]:
    async with AsyncSession(engine) as s, s.begin():
        statement = select(Json).where(Json.file_name == file_name)
        result = await s.execute(statement)
        json_file = Json.from_orm(result.first())
    val = await pool.fetchval("SELECT file FROM json WHERE file_name = $1", file_name)
    if not val or val == "{}":
        return None
    return json.loads(val)


async def write_json(engine: AsyncEngine, file_name: str, data: Dict) -> None:
    """Writes a json file to the database"""
    await pool.execute(
        "INSERT INTO json (file_name, file) VALUES ($1, $2) ON CONFLICT (file_name) DO UPDATE SET file = $2",
        file_name,
        json.dumps(data),
    )


async def delete_json(engine: AsyncEngine, file_name: str) -> None:
    """Deletes a json file from the database"""
    await pool.execute("DELETE FROM json WHERE file_name = $1", file_name)
