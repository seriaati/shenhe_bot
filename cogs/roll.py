import asyncio
import discord
from discord.ext import commands
from random import randint
from discord import app_commands
from utility.FlowApp import flow_app
from utility.utils import errEmbed, log, openFile, saveFile, defaultEmbed

global banner_pic, banner_name, blue_gif, purple_gif, gold_gif, air, blue_sleep, purple_sleep, gold_sleep, big_prize
banner_pic = 'https://i.imgur.com/q5q47o7.jpg'
blue_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962650001418/IMG_0482.gif'
purple_gif = 'https://media.discordapp.net/attachments/968783693814587423/970226962356391966/IMG_0477.gif'
gold_gif = 'https://c.tenor.com/Nc7Fgo43GLwAAAAC/genshin-gold-genshin-wish.gif'
banner_name = '星月交輝 - 限定祈願'
big_prize = '空月祝福 1個月'
air = '再接再厲!'
blue_sleep = 6.0
purple_sleep = 5.6
gold_sleep = 5.3


class RollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    class Menu(discord.ui.View):
        def __init__(self, author: discord.Member):
            super().__init__(timeout=None)
            self.author = author

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id

        class Confirm(discord.ui.View):
            def __init__(self, author: discord.Member, is_ten_pull: bool):
                super().__init__(timeout=None)
                self.author = author
                self.ten_pull = is_ten_pull

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user.id == self.author.id

            def animation_chooser(self, prize):
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

            def pull_card(self, is_ten_pull: bool, state:int):
                prize_pool = openFile('roll')
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

            def give_money(self, user_id:int, prize):
                if type(prize) is list:
                    for item in prize:
                        if item == '10 flow幣':
                            flow_app.transaction(user_id=user_id, flow_for_user=10)
                        elif item == '100 flow幣':
                            flow_app.transaction(user_id=user_id, flow_for_user=100)
                        elif item == '1000 flow幣':
                            flow_app.transaction(user_id=user_id, flow_for_user=1000)
                else:
                    if prize == '10 flow幣':
                        flow_app.transaction(user_id=user_id, flow_for_user=10)
                    elif prize == '100 flow幣':
                        flow_app.transaction(user_id=user_id, flow_for_user=100)
                    elif prize == '1000 flow幣':
                        flow_app.transaction(user_id=user_id, flow_for_user=1000)


            @discord.ui.button(label='確認', style=discord.ButtonStyle.green)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                history = openFile('pull_history')
                gu = openFile('pull_guarantee')
                if not self.ten_pull:
                    flow_app.transaction(user_id=interaction.user.id, flow_for_user=-10)
                else:
                    flow_app.transaction(user_id=interaction.user.id, flow_for_user=-100)
                if interaction.user.id not in history:
                    history[interaction.user.id] = {
                        big_prize: 0,
                        '10 flow幣': 0,
                        '100 flow幣': 0,
                        '1000 flow幣': 0,
                        air: 0
                    }
                if interaction.user.id not in gu:
                    gu[interaction.user.id] = {
                        big_prize: 0,
                        '10 flow幣': 0,
                        '100 flow幣': 0,
                        '1000 flow幣': 0,
                        air: 0
                    }
                sum = 0
                for item, count in gu[interaction.user.id].items():
                    sum += count
                if sum < 70:
                    prize = self.pull_card(self.ten_pull, 0)
                elif 70 <= sum < 80:
                    prize = self.pull_card(self.ten_pull, 1)
                elif 80 <= sum < 89:
                    prize = self.pull_card(self.ten_pull, 2)
                elif sum >= 89:
                    prize = self.pull_card(self.ten_pull, 3)
                    if type(prize) is not list:
                        prize = big_prize
                    else:
                        prize[0] = big_prize
                self.give_money(user_id=interaction.user.id, prize=prize)
                luluR = interaction.client.get_user(665092644883398671)
                if type(prize) is not list:
                    if prize == big_prize:
                        gu[interaction.user.id] = {
                            big_prize: 0,
                            '10 flow幣': 0,
                            '100 flow幣': 0,
                            '1000 flow幣': 0,
                            air: 0
                        }
                        print(log(True, False, 'Roll', f'{interaction.user.id} got big_prize'))
                        await luluR.send(embed=defaultEmbed(
                            '有人在抽卡裡抽到月卡了!',
                            f'ID: {interaction.user.id}\n'
                            '按ctrl+k並貼上ID即可查看使用者'))
                else:
                    if big_prize in prize:
                        gu[interaction.user.id] = {
                            big_prize: 0,
                            '10 flow幣': 0,
                            '100 flow幣': 0,
                            '1000 flow幣': 0,
                            air: 0
                        }
                    print(log(True, False, 'Roll', f'{interaction.user.id} got big_prize'))
                    await luluR.send(embed=defaultEmbed(
                        '有人在抽卡裡抽到月卡了!',
                        f'ID: {interaction.user.id}\n'
                        '按ctrl+k並貼上ID即可查看使用者'))
                saveFile(history, 'pull_history')
                saveFile(gu, 'pull_guarantee')
                history = openFile('pull_history')
                gu = openFile('pull_guarantee')
                if type(prize) is not list:
                    gif, sleep_time = self.animation_chooser(prize)
                    history[interaction.user.id][prize] += 1
                    if prize != big_prize:
                        gu[interaction.user.id][prize] += 1
                else:
                    gif, sleep_time = self.animation_chooser(prize)
                    prizeStr = ''
                    count = 0
                    for item in prize:
                        if item == air:
                            count += 1
                        history[interaction.user.id][item] += 1
                        if item != big_prize:
                            gu[interaction.user.id][item] += 1
                        prizeStr += f'• {item}\n'
                    prize = prizeStr
                    if count == 10:
                        prize = '10抽什麼都沒有, 太可惜了...'
                embed = defaultEmbed(banner_name, '')
                embed.set_image(url=gif)
                menu = RollCog.Menu(interaction.user)
                await interaction.response.edit_message(embed=embed, view=menu)
                await asyncio.sleep(sleep_time)
                embed = defaultEmbed('抽卡結果', f'{prize}')
                await interaction.followup.send(embed=embed, ephemeral=True)
                embed = defaultEmbed(banner_name, '')
                embed.set_image(url=banner_pic)
                await interaction.edit_original_message(embed=embed)
                saveFile(history, 'pull_history')
                saveFile(gu, 'pull_guarantee')

            @discord.ui.button(label='取消', style=discord.ButtonStyle.grey)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                menu = RollCog.Menu(interaction.user)
                await interaction.response.edit_message(view=menu)

        @discord.ui.button(label='詳情', style=discord.ButtonStyle.gray)
        async def detail_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = defaultEmbed('祈願詳情', '')
            embed.add_field(
                name=f'限定 UP - {big_prize}',
                value=
                "70抽之前: 0.6%\n"
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

        @discord.ui.button(label='歷史紀錄', style=discord.ButtonStyle.gray)
        async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            history = openFile('pull_history')
            gu = openFile('pull_guarantee')
            sum = 0
            gu_sum = 0
            result = ''
            if interaction.user.id not in history:
                result = '你還沒有在這期抽過卡!'
            else:
                for item, count in history[interaction.user.id].items():
                    sum += count
                    result += f'{item} • {count}次\n'
                for item, count in gu[interaction.user.id].items():
                    gu_sum += count
            embed = defaultEmbed(f'祈願紀錄(共{sum}抽, 目前距離保底{90-gu_sum}抽)', result)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='祈願1次', style=discord.ButtonStyle.blurple)
        async def one_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < 10:
                embed = errEmbed('你的flow幣不足!','1次祈願需花費10 flow幣')
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            confirm = self.Confirm(interaction.user, False)
            await interaction.response.edit_message(view=confirm)

        @discord.ui.button(label='祈願10次', style=discord.ButtonStyle.blurple)
        async def ten_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < 100:
                embed = errEmbed('你的flow幣不足!','10次祈願共需花費100 flow幣')
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            confirm = self.Confirm(interaction.user, True)
            await interaction.response.edit_message(view=confirm)

    @app_commands.command(name='roll', description='flow幣祈願系統')
    async def roll(self, interaction: discord.Interaction):
        check, msg = flow_app.checkFlowAccount(interaction.user.id)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        menu = self.Menu(interaction.user)
        embed = defaultEmbed(banner_name, '')
        embed.set_image(
            url='https://media.discordapp.net/attachments/968783693814587423/970552492096110612/c456a35b81c708c1c789d904065131e3.jpg?width=985&height=554')
        await interaction.response.send_message(embed=embed, view=menu)
        await menu.wait()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RollCog(bot))
