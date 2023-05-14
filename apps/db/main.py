import asyncpg

from .tables import UserAccountTable, UserSettingsTable


class Database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.users = UserAccountTable(pool)
        self.settings = UserSettingsTable(pool)
