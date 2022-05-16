import asyncio
from datetime import datetime, timedelta

import discord
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from utility.GenshinApp import genshin_app
from utility.utils import defaultEmbed, errEmbed, log, openFile, saveFile


class Schedule(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.resin_check.start()
        self.claim_reward.start()

    @app_commands.command(
        name='schedule',
        description='設定自動化功能(Hoyolab每日簽到、樹脂額滿提醒)')
    @app_commands.rename(function='功能', switch='開關')
    @app_commands.describe(
        function='選擇要執行自動化的功能',
        switch='選擇開啟或關閉此功能')
    @app_commands.choices(
        function=[Choice(name='顯示使用說明', value='help'),
                  Choice(name='每日自動簽到', value='daily'),
                  Choice(name='樹脂額滿提醒', value='resin')],
        switch=[Choice(name='開啟功能', value=1),
                Choice(name='關閉功能', value=0)])
    async def slash_schedule(self, interaction: discord.Interaction, function: str, switch: int):
        self.resin_check.cancel()
        print(log(False, False, 'schedule',
              f'{interaction.user.id}: (function={function}, switch={switch})'))
        if function == 'help':
            embed = defaultEmbed(
                '自動化功能使用說明',
                '• 每日簽到：每日 1~2 點之間自動簽到\n'
                '設定前請先使用`/claim`指令確認申鶴能正確幫你簽到\n'
                '• 樹脂提醒：每一小時檢查一次，當樹脂超過 140 會發送提醒\n'
                '設定前請先用 `/check` 指令確認申鶴能讀到你的樹脂資訊')
            await interaction.response.send_message(embed=embed)
            return

        check, msg = genshin_app.checkUserData(interaction.user.id)
        if check == False:
            await interaction.response.send_message(embed=msg)
            return
        if function == 'daily':
            if switch == 1:
                self.add_user(interaction.user.id, 'daily_reward')
                await interaction.response.send_message('✅ 原神每日自動簽到已開啟', ephemeral=True)
            elif switch == 0:
                self.remove_user(interaction.user.id, 'daily_reward')
                await interaction.response.send_message('✅ 每日自動簽到已關閉', ephemeral=True)
        elif function == 'resin':
            if switch == 1:
                self.add_user(interaction.user.id, 'resin_check')
                await interaction.response.send_message('✅ 樹脂額滿提醒已開啟', ephemeral=True)
            elif switch == 0:
                self.remove_user(interaction.user.id, 'resin_check')
                await interaction.response.send_message('✅ 樹脂額滿提醒已關閉', ephemeral=True)
        self.resin_check.start()

    @app_commands.command(name='claimall', description='強制執行所有用戶簽到')
    async def claim_all(self, i: Interaction):
        print(log(False, False, 'Claim All', i.user.id))
        await i.response.send_message(embed=defaultEmbed('⏳ 簽到中', '請稍等'))
        claim_data = openFile('schedule_daily_reward')
        count = 0
        for user_id, value in claim_data.items():
            check, msg = genshin_app.checkUserData(user_id)
            if check == False:
                self.remove_user(user_id, 'daily_reward')
                continue
            result = await genshin_app.claimDailyReward(user_id)
            count += 1
        await i.followup.send(embed=defaultEmbed('✅ 簽到完成', ''))

    @tasks.loop(hours=1)  # 樹脂檢查
    async def resin_check(self):
        print(log(True, False, 'Schedule', 'Resin check started'))
        resin_data = openFile('schedule_resin_notification')
        count = 0
        for user_id, value in resin_data.items():
            user = self.bot.get_user(user_id)
            check, msg = genshin_app.checkUserData(user_id)
            if check == False:
                del resin_data[user_id]
                continue
            result = await genshin_app.getRealTimeNotes(user_id, True)
            count += 1
            if result == True:
                if resin_data[user_id] < 3:
                    print(log(True, False, 'Schedule',
                          f'notification sent for {user_id}'))
                    embed = errEmbed(f'危險!! 樹脂已經超過140!!!!',
                                     '詳情可以輸入`/check`來查看')
                    embed.set_author(name=user, icon_url=user.avatar)
                    g = self.bot.get_guild(916838066117824553)
                    t = g.get_thread(973746732976447508)
                    tedd = self.bot.get_user(272394461646946304)
                    await t.send(user.mention)
                    if user_id == 410036441129943050:
                        await t.send(tedd.mention)
                    await t.send(embed=embed)
                    resin_data[user_id] += 1
            else:
                resin_data[user_id] = 0
            await asyncio.sleep(2.0)
        saveFile(resin_data, 'schedule_resin_notification')
        print(log(True, False, 'Schedule',
              f'Resin check finished, {count} in total'))

    @tasks.loop(hours=24)
    async def claim_reward(self):
        print(log(True, False, 'Schedule', 'Auto claim started'))
        claim_data = openFile('schedule_daily_reward')
        count = 0
        for user_id, value in claim_data.items():
            check, msg = genshin_app.checkUserData(user_id)
            if check == False:
                del claim_data[user_id]
                continue
            result = await genshin_app.claimDailyReward(user_id)
            count += 1
            await asyncio.sleep(2.0)
        print(log(True, False, 'Schedule',
              f'Auto claim finished, {count} in total'))

    @resin_check.before_loop
    async def before_resin_check(self):
        await self.bot.wait_until_ready()

    @claim_reward.before_loop
    async def before_claiming_reward(self):
        now = datetime.now().astimezone()
        next_run = now.replace(hour=1, minute=0, second=0)  # 等待到早上1點
        if next_run < now:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)

    def add_user(self, user_id: int, function_type: str):
        print(log(True, False, 'Schedule', f'add_user(user_id={user_id})'))
        if function_type == 'daily_reward':
            daily_data = openFile('schedule_daily_reward')
            daily_data[user_id] = 0
            saveFile(daily_data, 'schedule_daily_reward')
        elif function_type == 'resin_check':
            resin_data = openFile('schedule_resin_notification')
            resin_data[user_id] = 0
            saveFile(resin_data, 'schedule_resin_notification')

    def remove_user(self, user_id: int, function_type: str):
        print(log(True, False, 'Schedule', f'remove_user(function = {function}, user_id={user_id})'))
        if function_type == 'daily_reward':
            daily_data = openFile('schedule_daily_reward')
            del daily_data[user_id]
            saveFile(daily_data, 'schedule_daily_reward')
        elif function_type == 'resin_check':
            resin_data = openFile('schedule_resin_notification')
            del resin_data[user_id]
            saveFile(resin_data, 'schedule_resin_notification')


async def setup(client: commands.Bot):
    await client.add_cog(Schedule(client))
