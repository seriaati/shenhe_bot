import asyncio
import discord
from discord.ext import commands
from random import randint
from discord import app_commands
from utility.FlowApp import flow_app
from utility.utils import errEmbed, log, openFile, saveFile, defaultEmbed

global blue_gif, purple_gif, gold_gif, air, blue_sleep, purple_sleep, gold_sleep, big_prize
blue_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962650001418/IMG_0482.gif'
purple_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962356391966/IMG_0477.gif'
gold_gif = 'https://c.tenor.com/Nc7Fgo43GLwAAAAC/genshin-gold-genshin-wish.gif'
air = '再接再厲!'
blue_sleep = 6.0
purple_sleep = 5.6
gold_sleep = 5.3


class RollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    class Menu(discord.ui.View):
        def __init__(self, author: discord.Member, banner: str):
            super().__init__(timeout=None)
            banners = openFile('roll')
            self.author = author
            self.banner = banner
            self.banner_pic = banners[banner]['banner_pic']
            self.big_prize = banners[banner]['big_prize']

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id

        class Confirm(discord.ui.View):
            def __init__(self, author: discord.Member, is_ten_pull: bool, banner: str):
                super().__init__(timeout=None)
                banners = openFile('roll')
                self.author = author
                self.banner = banner
                self.ten_pull = is_ten_pull
                self.banner_pic = banners[banner]['banner_pic']
                self.big_prize = banners[banner]['big_prize']

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user.id == self.author.id

            def animation_chooser(self, prize, banner: str):
                banners = openFile('roll')
                big_prize = banners[banner]['big_prize']
                if type(prize) is list:
                    for item in prize:
                        if item == big_prize:
                            result = gold_gif, gold_sleep
                            break
                        elif item == '100 flow幣':
                            result = purple_gif, purple_sleep
                            break
                        else:
                            result = blue_gif, blue_sleep
                else:
                    if prize == air or prize == '10 flow幣':
                        result = blue_gif, blue_sleep
                    elif prize == '100 flow幣':
                        result = purple_gif, purple_sleep
                    elif prize == big_prize:
                        result = gold_gif, gold_sleep
                return result

            def pull_card(self, is_ten_pull: bool, state: int, banner: str):
                banners = openFile('roll')
                big_prize = banners[banner]['big_prize']
                prize_pool = banners[self.banner]['prizes']
                count = 0
                prize_pool_list = []
                for item, num in prize_pool.items():
                    for i in range(int(num)):
                        count += 1
                        prize_pool_list.append(item)
                if state == 0:
                    for i in range(1000-count):
                        prize_pool_list.append(air)
                elif state == 1:
                    for i in range(1000-count-44):
                        prize_pool_list.append(air)
                    for i in range(44):
                        prize_pool_list.append(big_prize)
                elif state == 2:
                    for i in range(1000-count-94):
                        prize_pool_list.append(air)
                    for i in range(94):
                        prize_pool_list.append(big_prize)
                else:
                    for i in range(1000-count):
                        prize_pool_list.append(air)
                if not is_ten_pull:
                    index = randint(0, 999)
                    return prize_pool_list[index]
                else:
                    result = []
                    for i in range(10):
                        index = randint(0, 999)
                        result.append(prize_pool_list[index])
                    return result

            def give_money(self, user_id: int, prize):
                if type(prize) is list:
                    for item in prize:
                        if item == '10 flow幣':
                            flow_app.transaction(
                                user_id=user_id, flow_for_user=10)
                        elif item == '100 flow幣':
                            flow_app.transaction(
                                user_id=user_id, flow_for_user=100)
                        elif item == '1000 flow幣':
                            flow_app.transaction(
                                user_id=user_id, flow_for_user=1000)
                else:
                    if prize == '10 flow幣':
                        flow_app.transaction(user_id=user_id, flow_for_user=10)
                    elif prize == '100 flow幣':
                        flow_app.transaction(
                            user_id=user_id, flow_for_user=100)
                    elif prize == '1000 flow幣':
                        flow_app.transaction(
                            user_id=user_id, flow_for_user=1000)

            def check_user_data(self, user_id: int, banner: str):
                banners = openFile('roll')
                history = openFile('pull_history')
                gu = openFile('pull_guarantee')
                if user_id not in history:
                    history[user_id] = {}
                if user_id not in gu:
                    gu[user_id] = {}
                if banner not in history[user_id]:
                    history[user_id][banner] = {}
                    for item, count in banners[banner]['prizes'].items():
                        history[user_id][banner][item] = 0
                    history[user_id][banner][air] = 0
                if banner not in gu[user_id]:
                    gu[user_id][banner] = {}
                    for item, count in banners[banner]['prizes'].items():
                        gu[user_id][banner][item] = 0
                    gu[user_id][banner][air] = 0
                saveFile(history, 'pull_history')
                saveFile(gu, 'pull_guarantee')

            def gu_system(self, user_id: int, banner: str):
                gu = openFile('pull_guarantee')
                sum = 0
                for item, count in gu[user_id][banner].items():
                    sum += count
                if sum < 70:
                    prize = self.pull_card(self.ten_pull, 0, self.banner)
                elif 70 <= sum < 80:
                    prize = self.pull_card(self.ten_pull, 1, self.banner)
                elif 80 <= sum < 89:
                    prize = self.pull_card(self.ten_pull, 2, self.banner)
                elif sum >= 89:
                    prize = self.pull_card(self.ten_pull, 3, self.banner)
                    if type(prize) is not list:
                        prize = big_prize
                    else:
                        prize[0] = big_prize
                return prize

            def check_big_prize(self, user_id: int, prize, banner: str):
                gu = openFile('pull_guarantee')
                banners = openFile('roll')
                big_prize = banners[banner]['big_prize']
                msg = defaultEmbed(
                    '有人在抽卡裡抽到月卡了!',
                    f'ID: {user_id}\n'
                    '按ctrl+k並貼上ID即可查看使用者')
                if type(prize) is not list:
                    if prize == big_prize:
                        gu[user_id][banner] = {
                            big_prize: 0,
                            '10 flow幣': 0,
                            '100 flow幣': 0,
                            '1000 flow幣': 0,
                            air: 0
                        }
                        print(log(True, False, 'Roll',
                              f'{user_id} got big_prize'))
                        saveFile(gu, 'pull_guarantee')
                        return True, msg
                    else:
                        return False, None
                else:
                    if big_prize in prize:
                        gu[user_id][banner] = {
                            big_prize: 0,
                            '10 flow幣': 0,
                            '100 flow幣': 0,
                            '1000 flow幣': 0,
                            air: 0
                        }
                        print(log(True, False, 'Roll',
                              f'{user_id} got big_prize'))
                        saveFile(gu, 'pull_guarantee')
                        return True, msg
                    else:
                        return False, None

            def write_history_and_gu(self, user_id: int, prize, banner: str):
                banners = openFile('roll')
                history = openFile('pull_history')
                gu = openFile('pull_guarantee')
                big_prize = banners[banner]['big_prize']
                if type(prize) is not list:
                    history[user_id][banner][prize] += 1
                    if prize != big_prize:
                        gu[user_id][banner][prize] += 1
                else:
                    prizeStr = ''
                    count = 0
                    for item in prize:
                        if item == air:
                            count += 1
                        history[user_id][banner][item] += 1
                        if item != big_prize:
                            gu[user_id][banner][item] += 1
                        prizeStr += f'• {item}\n'
                    prize = prizeStr
                    if count == 10:
                        prize = '10抽什麼都沒有, 太可惜了...'
                saveFile(history, 'pull_history')
                saveFile(gu, 'pull_guarantee')
                return prize

            @discord.ui.button(label='確認', style=discord.ButtonStyle.green, row=0)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not self.ten_pull:
                    flow_app.transaction(
                        user_id=interaction.user.id, flow_for_user=-10)
                else:
                    flow_app.transaction(
                        user_id=interaction.user.id, flow_for_user=-100)
                self.check_user_data(interaction.user.id, self.banner)
                prize = self.gu_system(interaction.user.id, self.banner)
                self.give_money(interaction.user.id, prize)
                luluR = interaction.client.get_user(665092644883398671)
                check, msg = self.check_big_prize(
                    interaction.user.id, prize, self.banner)
                if check == True:
                    await luluR.send(embed=msg)
                gif, sleep_time = self.animation_chooser(prize, self.banner)
                result = self.write_history_and_gu(
                    interaction.user.id, prize, self.banner)
                embed = defaultEmbed(self.banner, '')
                embed.set_image(url=gif)
                menu = RollCog.Menu(
                    author=interaction.user, banner=self.banner)
                await interaction.response.edit_message(embed=embed, view=menu)
                await asyncio.sleep(sleep_time)
                embed = defaultEmbed('抽卡結果', result)
                await interaction.followup.send(embed=embed, ephemeral=True)
                embed = defaultEmbed(self.banner, '')
                embed.set_image(url=self.banner_pic)
                await interaction.edit_original_message(embed=embed)

            @discord.ui.button(label='取消', style=discord.ButtonStyle.grey, row=0)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                menu = RollCog.Menu(interaction.user, self.banner)
                await interaction.response.edit_message(view=menu)

        @discord.ui.button(label='詳情', style=discord.ButtonStyle.gray, row=0)
        async def detail_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = defaultEmbed('祈願詳情', '')
            embed.add_field(
                name=f'限定 UP - {self.big_prize}',
                value="70抽之前: 0.6%\n"
                "70-80抽: 5%\n"
                "80-90抽: 10%\n"
                "90抽: 100%",
                inline=False
            )
            embed.add_field(
                name='其他獎品',
                value='10 Flow幣: 10%\n'
                '100 Flow: 3%\n'
                '1000 Flow: 0.1%',
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='歷史紀錄', style=discord.ButtonStyle.gray, row=0)
        async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            history = openFile('pull_history')
            gu = openFile('pull_guarantee')
            sum = 0
            gu_sum = 0
            result = ''
            if self.banner not in history[interaction.user.id]:
                result = '你還沒有在這期抽過卡!'
            else:
                for item, count in history[interaction.user.id][self.banner].items():
                    sum += count
                    result += f'{item} • {count}次\n'
                for item, count in gu[interaction.user.id][self.banner].items():
                    gu_sum += count
            embed = defaultEmbed(f'祈願紀錄(共{sum}抽, 目前距離保底{90-gu_sum}抽)', result)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='祈願1次', style=discord.ButtonStyle.blurple, row=0)
        async def one_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < 10:
                embed = errEmbed('你的flow幣不足!', '1次祈願需花費10 flow幣')
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            confirm = self.Confirm(
                author=interaction.user, is_ten_pull=False, banner=self.banner)
            await interaction.response.edit_message(view=confirm)

        @discord.ui.button(label='祈願10次', style=discord.ButtonStyle.blurple, row=0)
        async def ten_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < 100:
                embed = errEmbed('你的flow幣不足!', '10次祈願共需花費100 flow幣')
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            confirm = self.Confirm(
                author=interaction.user, is_ten_pull=True, banner=self.banner)
            await interaction.response.edit_message(view=confirm)

        def get_banner_options():
            banners = openFile('roll')
            banner_list = []
            for banner, value in banners.items():
                banner_list.append(discord.SelectOption(label=banner))
            return banner_list

        @discord.ui.select(options=get_banner_options(), row=1, placeholder='請選擇你想要抽取的獎品池', min_values=1, max_values=1)
        async def banner_chooser(self, interaction: discord.Interaction, select: discord.ui.Select):
            banners = openFile('roll')
            banner = select.values[0]
            menu = RollCog.Menu(interaction.user, banner)
            embed = defaultEmbed(banner, '')
            embed.set_image(url=banners[banner]['banner_pic'])
            await interaction.response.edit_message(embed=embed, view=menu)

    @app_commands.command(name='roll', description='flow幣祈願系統')
    async def roll(self, interaction: discord.Interaction):
        check, msg = flow_app.checkFlowAccount(interaction.user.id)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        banners = openFile('roll')
        banner = '星月交輝 - 限定祈願'
        menu = self.Menu(interaction.user, banner)
        embed = defaultEmbed(banner, '')
        embed.set_image(url=banners[banner]['banner_pic'])
        await interaction.response.send_message(embed=embed, view=menu)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RollCog(bot))
