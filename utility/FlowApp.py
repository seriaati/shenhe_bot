from datetime import datetime
from typing import Union

import aiosqlite
from discord import Embed

from utility.utils import errEmbed, log


class FlowApp:
    def __init__(self, db: aiosqlite.Connection, bot) -> None:
        self.db = db
        self.bot = bot

    async def register(self, user_id: int):
        await self.bot.log.send(log(True, False, 'Register', user_id))
        await self.transaction(user_id, 20, is_new_account=True)

    async def transaction(self, user_id: int, flow_for_user: int, time_state: str = None, is_new_account: bool = False, is_removing_account: bool = False):
        now = datetime.now()
        time_states = ['morning', 'noon', 'night']
        if is_removing_account:
            await self.bot.log.send(log(True, False, 'Removing Acc',
                                        f'{user_id}: (flow = {flow_for_user})'))
            c = await self.db.cursor()
            await c.execute('DELETE FROM flow_accounts WHERE user_id = ?', (user_id,))
            bank_flow = await self.get_bank_flow()
            await c.execute('UPDATE bank SET flow = ?', (bank_flow+flow_for_user,))
            await self.db.commit()
            return
        if is_new_account:
            default_time = datetime(year=now.year, month=now.month, day=now.day-1,
                                    hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
            c = await self.db.cursor()
            await c.execute('INSERT INTO flow_accounts(user_id) VALUES(?)', (user_id,))
            await c.execute(f'UPDATE flow_accounts SET flow = ? WHERE user_id = ?', (20, user_id))
            for time in time_states:
                await c.execute(f'UPDATE flow_accounts SET {time} = ? WHERE user_id = ?', (default_time, user_id))
            await self.db.commit()
        c = await self.db.cursor()
        user_flow = await self.get_user_flow(user_id)
        await c.execute('UPDATE flow_accounts SET flow = ? WHERE user_id = ?', (user_flow+flow_for_user, user_id))
        bank_flow = await self.get_bank_flow()
        await c.execute(f'UPDATE bank SET flow = ?', (bank_flow-flow_for_user,))
        if time_state is not None:
            for time in time_states:
                if time_state == time:
                    await c.execute(f'UPDATE flow_accounts SET {time} = ? WHERE user_id = ?', (now, user_id))
        await self.db.commit()
        user_log = '{0:+d}'.format(int(flow_for_user))
        bank_log = '{0:+d}'.format(-int(flow_for_user))
        await c.execute('UPDATE flow_accounts SET last_trans = ? WHERE user_id = ?', (now, user_id))
        await self.db.commit()
        tranasaction_log_msg = log(True, False, 'Transaction',
                                   f'user({user_id}): {user_log}, bank: {bank_log}')
        bank_flow = await self.get_bank_flow()
        await c.execute('SELECT SUM(flow) FROM flow_accounts')
        sum = await c.fetchone()
        current_log_msg = log(True, False, 'Current',
                              f"user_total: {sum[0]}, bank: {bank_flow}")
        total_log_msg = (log(True, False, 'Total', int(sum[0])+bank_flow))
        await self.bot.log.send(f'{tranasaction_log_msg}\n{current_log_msg}\n{total_log_msg}')

    async def checkFlowAccount(self, user_id: int) -> Union[bool, Embed]:
        c = await self.db.cursor()
        await c.execute('SELECT user_id FROM flow_accounts WHERE user_id = ?', (user_id,))
        result = await c.fetchone()
        if result is None:
            await self.register(user_id)
            embed = errEmbed(
                '找不到flow帳號!',
                f'<@{user_id}>\n現在申鶴已經創建了一個, 請重新執行操作')
            return False, embed
        else:
            return True, None

    async def get_user_flow(self, user_id: int) -> int:
        c = await self.db.cursor()
        await c.execute('SELECT flow FROM flow_accounts WHERE user_id = ?', (user_id,))
        flow = await c.fetchone()
        return flow[0]

    async def get_bank_flow(self) -> int:
        c = await self.db.cursor()
        await c.execute('SELECT flow FROM bank')
        bank_flow = await c.fetchone()
        return bank_flow[0]
