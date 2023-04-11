import asyncio
from typing import Dict

import dev.models as model
from dev.enum import CheckInAPI


class DailyCheckin:
    def __init__(self, bot: model.BotModel) -> None:
        self.bot = bot
        self.total: Dict[CheckInAPI, int] = {}

    async def start(self):
        rows = await self.bot.pool.execute(
            """
            SELECT * FROM user_accounts
            WHERE daily_checkin = true 
            AND ltuid IS NOT NULL
            AND ltoken IT NOT NULL
            """
        )
        users = [model.User.from_row(row) for row in rows]

    async def _checkin_local(self):
        pass

    async def _checkin_api(self):
        pass

    async def _notify_user(self):
        pass

    async def _notify_results(self):
        pass
