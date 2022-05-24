import aiosqlite

class DbUtils():
    def __init__(self, db: aiosqlite.Connection) -> None:
        self.db = db

    async def table_exists(self, table_name: str):
        c = await self.db.cursor()
        await c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        result = await c.fetchone()
        if result is None:
            return False, c 
        else:
            return True, c
