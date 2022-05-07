import yaml
import asyncio
import discord
from datetime import datetime
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from utility.utils import can_dm_user, defaultEmbed, errEmbed, log
from utility.GenshinApp import genshin_app

class Schedule(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.__daily_reward_filename = 'data/schedule_daily_reward.yaml'
        self.__resin_notifi_filename = 'data/schedule_resin_notification.yaml'
        with open(self.__daily_reward_filename, 'r', encoding='utf-8') as f:
            self.__daily_dict = yaml.full_load(f)
        with open(self.__resin_notifi_filename, 'r', encoding='utf-8') as f:
            self.__resin_dict = yaml.full_load(f)
        
        self.schedule.start()

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
        check, check_msg = can_dm_user(interaction.user)
        if check == False:
            await interaction.response.send_message(embed=check_msg, ephemeral=True)
            return
        self.schedule.stop()
        print(log(False, False, 'schedule', f'{interaction.user.id}: (function={function}, switch={switch})'))
        if function == 'help': # 排程功能使用說明
            embed = defaultEmbed(
            '自動化功能使用說明',
            '• 每日簽到：每日 1~2 點之間自動簽到\n'
            '設定前請先使用`/claim`指令確認申鶴能正確幫你簽到\n'
            '• 樹脂提醒：每一小時檢查一次，當樹脂超過 140 會發送提醒\n'
            '設定前請先用 `/check` 指令確認申鶴能讀到你的樹脂資訊')
            await interaction.response.send_message(embed=embed)
            return
        # 確認使用者Cookie資料
        check, msg = await genshin_app.checkUserData(interaction.user.id)
        if check == False:
            await interaction.response.send_message(embed=msg)
            return
        if function == 'daily': # 每日自動簽到
            if switch == 1: # 開啟簽到功能
                # 新增使用者
                self.__add_user(interaction.user.id, self.__daily_dict, self.__daily_reward_filename)
                await interaction.response.send_message('原神每日自動簽到已開啟')
            elif switch == 0: # 關閉簽到功能
                self.__remove_user(interaction.user.id, self.__daily_dict, self.__daily_reward_filename)
                await interaction.response.send_message('每日自動簽到已關閉')
        elif function == 'resin': # 樹脂額滿提醒
            if switch == 1: # 開啟檢查樹脂功能
                self.__add_user(interaction.user.id, self.__resin_dict, self.__resin_notifi_filename)
                await interaction.response.send_message('樹脂額滿提醒已開啟')
            elif switch == 0: # 關閉檢查樹脂功能
                self.__remove_user(interaction.user.id, self.__resin_dict, self.__resin_notifi_filename)
                await interaction.response.send_message('樹脂額滿提醒已關閉')
        self.schedule.start()
        
    loop_interval = 10
    @tasks.loop(minutes=loop_interval)
    async def schedule(self):
        now = datetime.now()
        if now.hour == 1 and now.minute < self.loop_interval:
        # if True:
            print(log(True, False, 'Schedule', 'Auto claim started'))
            claim_data = self.getClaimData()
            count = 0
            for user_id, value in claim_data.items():
                channel = self.bot.get_channel(957268464928718918)
                check, msg = genshin_app.checkUserData(user_id)
                if check == False:
                    self.__remove_user(user_id, self.__daily_dict, self.__daily_reward_filename)
                    continue
                result = await genshin_app.claimDailyReward(user_id)
                count += 1
                user = self.bot.get_user(user_id)
                await channel.send(f'[自動簽到] {user}簽到成功')
                await asyncio.sleep(2.0)
            print(log(True, False, 'Schedule', f'Auto claim finished, {count} in total'))
        
        if abs(now.hour - 1) % 2 == 1 and now.minute < self.loop_interval:
        # if True:
            print(log(True, False, 'Schedule','Resin check started'))
            resin_data = self.getResinData()
            count = 0
            for user_id, value in resin_data.items():
                user = self.bot.get_user(user_id)
                check, msg = genshin_app.checkUserData(user_id)
                if check == False:
                    self.__remove_user(user_id, self.__resin_dict, self.__resin_notifi_filename)
                    continue
                result = await genshin_app.getRealTimeNotes(user_id, True)
                count += 1
                if result == True:
                    if resin_data[user_id] < 3:
                        try:
                            embed = errEmbed('危險!! 樹脂已經超過140!!!!','詳情可以輸入`/check`來查看')
                            await user.send(embed=embed)
                            if user_id == 410036441129943050:
                                user = self.bot.get_user(272394461646946304)
                                await user.send(embed=embed)
                            resin_data[user_id] += 1
                            self.__saveScheduleData(resin_data, self.__resin_notifi_filename)
                        except:
                            self.__remove_user(user_id, self.__resin_dict, self.__resin_notifi_filename)
                elif result==False:
                    resin_data[user_id] = 0
                await asyncio.sleep(2.0)
            print(log(True, False, 'Schedule',f'Resin check finished, {count} in total'))

    @schedule.before_loop
    async def before_schedule(self):
        await self.bot.wait_until_ready()

    def getClaimData(self):
        with open(self.__daily_reward_filename, 'r', encoding='utf-8') as f:
            return yaml.full_load(f)

    def getResinData(self):
        with open(self.__resin_notifi_filename, 'r', encoding='utf-8') as f:
            return yaml.full_load(f)

    def __add_user(self, user_id: str, data: dict, filename: str) -> None:
        data[user_id] = 0
        self.__saveScheduleData(data, filename)

    def __remove_user(self, user_id: int, data: dict, filename: str) -> None:
        try:
            del data[user_id]
        except:
            print(log(True, True, 'Schedule', f'remove_user(user_id={user_id}): user does not exist'))
        else:
            self.__saveScheduleData(data, filename)
    
    def __saveScheduleData(self, data: dict, filename: str):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                yaml.dump(data, f)
        except:
            print(log(True, True, 'Schedule', f'saveScheduleData(filename={filename}): file does not exist'))

async def setup(client: commands.Bot):
    await client.add_cog(Schedule(client))