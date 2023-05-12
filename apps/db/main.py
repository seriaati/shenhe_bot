import asyncpg

from .tables.user_account import UserAccountTable


class Database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.users = UserAccountTable(pool)
