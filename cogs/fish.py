from random import randint
import aiosqlite

from discord import ButtonStyle, Interaction, app_commands, Thread
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Button, View
from utility.FlowApp import FlowApp
from utility.utils import ayaakaaEmbed, log

class FishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.debug_toggle = self.bot.debug_toggle

    global fish_list, fish_flow_list, fish_image_list
    fish_flow_list = ['1', '2', '2', '2', '2', '5', '5', '7', '10', '20', '15', '20']
    fish_list = ['虱目魚', '鮭魚', '鱈魚', '鮪魚', '鰻魚',
                 '龍蝦', '螃蟹', '心海', '大白鯊', '達達利鴨', '大象', '抹香鯨']
    fish_image_list = [
        'https://www.ocean-treasure.com/wp-content/uploads/2021/06/Milkfish.jpg',
        'https://cdn-fgbal.nitrocdn.com/KhVbtyNBpSvxGKkBoxbcDIRslLpQdgCA/assets/static/optimized/wp-content/uploads/2021/08/1daf341ee1fca75bef8327e080fa5b21.Salmon-Fillet-1-1-1536x1536.jpg',
        'https://seafoodfriday.hk/wp-content/uploads/2021/08/Cod-Fillet-1.jpg',
        'https://cdn-fgbal.nitrocdn.com/KhVbtyNBpSvxGKkBoxbcDIRslLpQdgCA/assets/static/optimized/wp-content/uploads/2021/08/327f113f6c4342a982213da7e1dfd5d8.Tuna-Fillet-1.jpg',
        'https://www.boilingtime.com/img/0630/f.jpg',
        'https://seafoodfriday.hk/wp-content/uploads/2021/08/Red-Lobster-1-1536x1536.jpg',
        'https://www.freshexpressonline.com/media/catalog/product/cache/cce444513434d709cad419cac6756dc1/8/0/804001004.jpg',
        'https://assets2.rockpapershotgun.com/genshin-impact-sangonomiya-kokomi.jpg/BROK/thumbnail/1200x1200/quality/100/genshin-impact-sangonomiya-kokomi.jpg',
        'https://static01.nyt.com/images/2020/08/12/multimedia/00xp-shark/00xp-shark-mediumSquareAt3X.jpg',
        'https://c.tenor.com/blHN79J-floAAAAd/ducktaglia-duck.gif',
        'https://images.fineartamerica.com/images/artworkimages/mediumlarge/1/2-african-elephant-closeup-square-susan-schmitz.jpg',
        'https://i.natgeofe.com/n/8084965e-1dfc-47eb-b0c5-e4f86ee65c82/sperm-whale_thumb.jpg'
    ]

    def generate_fish_embed(self, index: int):  # 製造摸魚embed
        if index >= 0 and index <= 4 or index == 7:
            result = ayaakaaEmbed(
                fish_list[index],
                f'是可愛的**{fish_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_list[index]}**有機率獲得 {fish_flow_list[index]} flow幣'
            )
            # e.g. 是可愛的鮭魚！要摸摸看嗎?
            #     摸鮭魚有機率獲得 2 flow幣
        else:
            result = ayaakaaEmbed(
                fish_list[index],
                f'是野生的**{fish_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_list[index]}**有機率獲得或損失 {fish_flow_list[index]} flow幣'
            )
            # e.g. 是野生的達達利鴨！要摸摸看嗎?
            #     摸達達利鴨有機率獲得或損失 20 flow幣
        result.set_thumbnail(url=fish_image_list[index])
        return result

    class TouchFishButton(Button):  # 摸魚按鈕
        def __init__(self, index: int, db: aiosqlite.Connection, bot):
            super().__init__(style=ButtonStyle.blurple,
                             label=f'撫摸可愛的{fish_list[index]}')
            self.index = index
            self.flow_app = FlowApp(db, bot)

        async def callback(self, interaction: Interaction):
            self.view.stop()
            self.disabled = True
            await interaction.response.edit_message(view=self.view)

            await interaction.channel.send(f'{interaction.user.mention} 摸到**{fish_list[self.index]}**了！')
            # e.g. @綾霞 摸到虱目魚了！

            value = randint(1, 100)  # Picks a random number from 1 - 100

            # 摸虱目魚有機率獲得 1 flow幣

            if self.index == 0:  # [0] 虱目魚
                if value <= 60:  # 60% Chance of increasing flow amount by 1
                    await self.flow_app.transaction(interaction.user.id, 1)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 1 flow幣!', ephemeral=True)
                    # e.g. 摸虱目魚摸到 1 flow幣!
                else:
                    await interaction.followup.send(f'單純的摸魚而已, 沒有摸到flow幣 qwq', ephemeral=True)

            # 摸鮭魚, 鱈魚, 鮪魚 或 鰻魚有機率獲得 2 flow幣
            # [1] 鮭魚, [2] 鱈魚, [3] 鮪魚, [4] 鰻魚
            elif self.index >= 1 and self.index <= 4:
                if value <= 30:  # 30% Chance of increasing flow amount by 2
                    await self.flow_app.transaction(interaction.user.id, 2)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 2 flow幣!', ephemeral=True)
                    # e.g. 摸鮭魚摸到 2 flow幣!
                else:
                    await interaction.followup.send('單純的摸魚而已, 沒有摸到flow幣 qwq', ephemeral=True)

            # 摸龍蝦 或 螃蟹有機率獲得或損失 5 flow幣
            # [5] 龍蝦, [6] 螃蟹,
            elif self.index >= 5 and self.index <= 6:
                if value <= 50:  # 50% Chance of increasing flow amount by 5
                    await self.flow_app.transaction(interaction.user.id, 5)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 5 flow幣!', ephemeral=True)
                    # e.g. 摸龍蝦摸到 5 flow幣!
                else:  # 50% Chance of decreasing flow amount by 5
                    await self.flow_app.transaction(interaction.user.id, -5)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**鉗到了，損失了 5 flow幣 qwq', ephemeral=True)
                    # e.g. 被龍蝦鉗到了，損失了 5 flow幣 qwq

            # 摸心海有機率獲得或損失 7 flow幣
            # [7] 心海
            elif self.index == 7:
                if value <= 50:  # 50% Chance of increasing flow amount by 7
                    await self.flow_app.transaction(interaction.user.id, 7)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 7 flow幣!', ephemeral=True)
                    # e.g. 摸心海摸到 7 flow幣!
                else:  # 50% Chance of decreasing flow amount by 7
                    await self.flow_app.transaction(interaction.user.id, -7)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**打飛了，損失了 7 flow幣 qwq', ephemeral=True)
                    # e.g. 被心海打飛了，損失了 7 flow幣 qwq

            # 摸大白鯊有機率獲得或損失 10 flow幣
            elif self.index == 8:  # [8] 大白鯊
                if value <= 50:  # 50% Chance of increasing flow amount by 10
                    await self.flow_app.transaction(interaction.user.id, 10)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 10 flow幣!', ephemeral=True)
                    # e.g. 摸大白鯊 摸到 10 flow幣!
                else:  # 50% Chance of decreasing flow amount by 10
                    await self.flow_app.transaction(interaction.user.id, -10)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**咬到了，損失了 10 flow幣 qwq', ephemeral=True)
                    # e.g. 被大白鯊咬到了，損失了 10 flow幣 qwq

            # 摸達達利鴨有機率獲得或損失 20 flow幣
            elif self.index == 9:  # [9] 達達利鴨
                if value <= 50:  # 50% Chance of increasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, 20)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 20 flow幣!', ephemeral=True)
                    # e.g. 摸達達利鴨摸到 20 flow幣!
                else:  # 50% Chance of decreasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, -20)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**偷襲，損失了 20 flow幣 qwq', ephemeral=True)
                    # e.g. 被達達利鴨偷襲，損失了 20 flow幣 qwq
            
             # 摸大象有機率獲得或損失 15 flow幣
            elif self.index == 10:  # [10] 大象
                if value <= 50:  # 50% Chance of increasing flow amount by 15
                    await self.flow_app.transaction(interaction.user.id, 15)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 15 flow幣!', ephemeral=True)
                    # e.g. 摸大象摸到 15 flow幣!
                else:  # 50% Chance of decreasing flow amount by 15
                    await self.flow_app.transaction(interaction.user.id, -15)
                    await interaction.followup.send(f'被**{fish_list[self.index]}**踩到了，損失了 15 flow幣 qwq', ephemeral=True)
                    # e.g. 被大象踩到了，損失了 15 flow幣 qwq
            
             # 摸抹香鯨有機率獲得或損失 20 flow幣
            elif self.index == 10:  # [11] 抹香鯨
                if value <= 50:  # 50% Chance of increasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, 20)
                    await interaction.followup.send(f'摸**{fish_list[self.index]}**摸到 20 flow幣!', ephemeral=True)
                    # e.g. 摸抹香鯨摸到 20 flow幣!
                else:  # 50% Chance of decreasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, -20)
                    await interaction.followup.send(f'**{fish_list[self.index]}**抹香鯨 鯨爆了，損失了 20 flow幣 qwq', ephemeral=True)
                    # e.g. 抹香鯨 鯨爆了，損失了 20 flow幣 qwq

    class TouchFish(View):  # 摸魚view
        def __init__(self, index: str, db: aiosqlite.Connection, bot):
            super().__init__(timeout=None)
            self.add_item(FishCog.TouchFishButton(index, db, bot))

    def get_fish_choices():  # 取得所有魚種
        choices = []
        for fish in fish_list:
            choices.append(Choice(name=fish, value=fish_list.index(fish)))
        return choices

    @commands.Cog.listener()
    async def on_message(self, message):  # 機率放魚
        if message.author == self.bot.user:
            return
        random_number = randint(1, 100) if not self.debug_toggle else 1
        if random_number == 1 and not isinstance(message.channel, Thread):
            index = randint(0, len(fish_list)-1)
            touch_fish_view = FishCog.TouchFish(index, self.bot.db, self.bot)
            await message.channel.send(embed=self.generate_fish_embed(index), view=touch_fish_view)

   # /fish
    @app_commands.command(name='fish', description='緊急放出一條魚讓人摸')
    @app_commands.rename(fish_type='魚種')
    @app_commands.describe(fish_type='選擇要放出的魚種')
    @app_commands.choices(fish_type=get_fish_choices())
    @app_commands.checks.has_role('小雪團隊')
    async def release_fish(self, i: Interaction, fish_type: int):
        await self.bot.log.send(log(False, False, 'Release Fish', i.user.id))
        touch_fish_view = FishCog.TouchFish(fish_type, self.bot.db, self.bot)
        await i.response.send_message(embed=self.generate_fish_embed(fish_type), view=touch_fish_view)

    @release_fish.error
    async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FishCog(bot))
