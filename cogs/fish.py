import random
from random import randint

import aiosqlite
from debug import DefaultView
from discord import ButtonStyle, Interaction, Thread, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Button
from utility.apps.FlowApp import FlowApp
from utility.utils import ayaakaaEmbed
from data.fish.fish_data import fish_data


class FishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.debug_toggle = self.bot.debug_toggle

    global adj_list

    adj_list = ['可愛', '奇怪', '神奇', '變態', '色色', '野生', '開心', '傷心', '生氣', '長長', '短短', '大大', '小小']

    # fish_type = 1 扣幣
    # fish_type = 0 不扣幣

    def generate_fish_embed(self, fish: str):  # 製造摸魚embed
        flow = fish_data[fish]['flow']
        fish_adj = random.choice(
            adj_list) if not fish_data[fish]['cute'] else '十分可愛'
        if fish_data[fish]['type_0']:
            result = ayaakaaEmbed(
                fish,
                f'是**{fish_adj}的{fish}**！要摸摸看嗎?\n'
                f'摸**{fish_adj}的{fish}**有機率獲得 {flow} flow幣'
            )
            # e.g. 是可愛的鮭魚！要摸摸看嗎?
            # 摸鮭魚有機率獲得 2 flow幣
        else:
            result = ayaakaaEmbed(
                fish,
                f'是**{fish_adj}的{fish}**！要摸摸看嗎?\n'
                f'摸**{fish_adj}的{fish}**有機率獲得或損失 {flow} flow幣'
            )
            # e.g. 是野生的達達利鴨！要摸摸看嗎?
            # 摸達達利鴨有機率獲得或損失 20 flow幣
        result.set_thumbnail(url=fish_data[fish]['image_url'])
        return result, fish_adj

    class TouchFishButton(Button):  # 摸魚按鈕
        def __init__(self, fish: str, db: aiosqlite.Connection, fish_adj: str):
            self.fish = fish
            self.flow_app = FlowApp(db)
            self.fish_adj = fish_adj
            super().__init__(style=ButtonStyle.blurple,
                             label=f'撫摸{self.fish_adj}的{fish}')

        async def callback(self, interaction: Interaction):
            self.view.stop()
            self.disabled = True
            await interaction.response.edit_message(view=self.view)

            fish = fish_data[self.fish]
            flow = fish['flow']
            await interaction.channel.send(f'{interaction.user.mention} 摸到**{self.fish_adj}的{self.fish}**了！')
            # e.g. @綾霞 摸到虱目魚了！

            value = randint(1, 100)  # Picks a random number from 1 - 100
            # 摸虱目魚有機率獲得 1 flow幣

            if fish['type_0']:
                if value <= int(fish['flow_chance']):
                    await self.flow_app.transaction(interaction.user.id, int(flow))
                    await interaction.followup.send(f'摸**{self.fish_adj}的{self.fish}**摸到 {flow} flow幣!\n目前 flow 幣: {await self.flow_app.get_user_flow(interaction.user.id)}', ephemeral=True)
                    # e.g. 摸虱目魚摸到 1 flow幣!
                else:
                    await interaction.followup.send(f'單純的摸**{self.fish_adj}的{self.fish}**而已, 沒有摸到flow幣 qwq\n目前 flow 幣: {await self.flow_app.get_user_flow(interaction.user.id)}', ephemeral=True)
            else:
                verb = fish['verb']
                if value <= 50:  # 50% Chance of increasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, int(flow))
                    await interaction.followup.send(f'摸**{self.fish_adj}的{self.fish}**摸到 {flow} flow幣!\n目前 flow 幣: {await self.flow_app.get_user_flow(interaction.user.id)}', ephemeral=True)
                    # e.g. 摸抹香鯨摸到 20 flow幣!
                else:  # 50% Chance of decreasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, -int(flow))
                    await interaction.followup.send(f'被**{self.fish_adj}的{self.fish}**{random.choice(verb)}，損失了 {flow} flow幣 qwq\n目前 flow 幣: {await self.flow_app.get_user_flow(interaction.user.id)}', ephemeral=True)
                    # e.g. 抹香鯨 鯨爆了，損失了 20 flow幣 qwq

    class TouchFish(DefaultView):  # 摸魚view
        def __init__(self, index: str, db: aiosqlite.Connection, fish_adj: str):
            super().__init__(timeout=None)
            self.add_item(FishCog.TouchFishButton(
                index, db, fish_adj))

    def get_fish_choices():  # 取得所有魚種
        choices = []
        for fish in list(fish_data.keys()):
            choices.append(Choice(name=fish, value=fish))
        return choices

    @commands.Cog.listener()
    async def on_message(self, message):  # 機率放魚
        if message.author == self.bot.user:
            return
        random_number = randint(1, 100)
        if random_number == 1 and not isinstance(message.channel, Thread):
            fish = random.choice(list(fish_data.keys()))
            embed, fish_adj = self.generate_fish_embed(fish)
            view = FishCog.TouchFish(fish, self.bot.db, fish_adj)
            await message.channel.send(embed=embed, view=view)

   # /releasefish
    @app_commands.command(name='releasefish放魚', description='緊急放出一條魚讓人摸')
    @app_commands.rename(fish_type='魚種')
    @app_commands.describe(fish_type='選擇要放出的魚種')
    @app_commands.choices(fish_type=get_fish_choices())
    @app_commands.checks.has_role('小雪團隊')
    async def release_fish(self, i: Interaction, fish_type: str):
        embed, fish_adj = self.generate_fish_embed(fish_type)
        view = FishCog.TouchFish(fish_type, self.bot.db, fish_adj)
        await i.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FishCog(bot))
    #
