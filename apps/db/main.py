import asyncpg

import apps.db.tables as tables


class Leaderboard:
    """Leaderboard"""

    def __init__(self, pool: asyncpg.Pool):
        self.abyss_character = tables.AbyssCharaBoard(pool)
        """Abyss character usage leaderboard"""
        self.abyss = tables.AbyssBoard(pool)
        """Abyss leaderboard"""


class Notif:
    """Notifications"""

    def __init__(self, pool: asyncpg.Pool):
        self.resin = tables.ResinNotifTable(pool)
        """Resin notifications"""
        self.pot = tables.PotNotifTable(pool)
        """Pot notifications"""
        self.pt = tables.PTNotifTable(pool)
        """Parametric transformer notifications"""
        self.talent = tables.TalentNotifTable(pool)
        """Talent notifications"""
        self.weapon = tables.WeaponNotifTable(pool)
        """Weapon notifications"""


class Database:
    """Database"""

    def __init__(self, pool: asyncpg.Pool):
        self.users = tables.UserAccountTable(pool)
        """User account"""
        self.settings = tables.UserSettingsTable(pool)
        """User settings"""
        self.leaderboard = Leaderboard(pool)
        """Leaderboard"""
        self.notifs = Notif(pool)
        """Notifications"""
        self.codes = tables.GenshinCodes(pool)
        """Genshin codes"""
        self.redeemed = tables.RedeemedCodeTable(pool)
