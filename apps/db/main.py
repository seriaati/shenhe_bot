import asyncpg

import apps.db.tables as tables


class Leaderboard:
    """Leaderboard"""

    def __init__(self, pool: asyncpg.Pool):
        self.abyss_character = tables.AbyssCharacterLeaderboard(pool)
        """Abyss character usage leaderboard"""
        self.abyss = tables.AbyssLeaderboard(pool)
        """Abyss leaderboard"""


class Database:
    """Database"""

    def __init__(self, pool: asyncpg.Pool):
        self.users = tables.UserAccountTable(pool)
        """User account"""
        self.settings = tables.UserSettingsTable(pool)
        """User settings"""
        self.leaderboard = Leaderboard(pool)
        """Leaderboard"""
