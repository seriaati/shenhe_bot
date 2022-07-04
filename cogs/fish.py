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


class FishCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.debug_toggle = self.bot.debug_toggle

    global fish, fish_name_list, adj_list 
    #Data
    fish = {
        '虱目魚': {
            'flow': 1,
            'flow_chance': 50,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://www.ocean-treasure.com/wp-content/uploads/2021/06/Milkfish.jpg'
        },
        '鮭魚': {
            'flow': 2,
            'flow_chance': 40,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://cdn.discordapp.com/avatars/329643343879471104/43da237aff2393e47d7187a2ba8b6827.png?size=1024'
        },
        '鱈魚': {
            'flow': 2,
            'flow_chance': 40,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://seafoodfriday.hk/wp-content/uploads/2021/08/Cod-Fillet-1.jpg'
        },
        '鮪魚': {
            'flow': 2,
            'flow_chance': 40,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://storage.googleapis.com/opinion-cms-cwg-tw/article/201806/article-5b2239595cee6.jpg'
        },
        '鰻魚': {
            'flow': 2,
            'flow_chance': 40,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://www.boilingtime.com/img/0630/f.jpg'
        },
        '企鵝': {
            'flow': 3,
            'flow_chance': 30,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://i.pinimg.com/originals/f2/38/ce/f238ce8da599e3beb5e3f85441083ea2.gif'
        },
        '兔兔': {
            'flow': 3,
            'flow_chance': 30,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://i.pinimg.com/236x/f6/de/7f/f6de7f2ec162913fa46704ccf9cb0bd6.jpg'
        },
        '雞雞': {
            'flow': 3,
            'flow_chance': 30,
            'type_0': True,
            'cute': False,
            'verb': None,
            'image_url': 'https://c.tenor.com/V4-1u-unJYkAAAAC/chicken-sad.gif'
        },
        '龍蝦': {
            'flow': 5,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '鉗到了',
            'image_url': 'https://seafoodfriday.hk/wp-content/uploads/2021/08/Red-Lobster-1-1536x1536.jpg'
        },
        '螃蟹': {
            'flow': 5,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '鉗到了',
            'image_url': 'https://www.freshexpressonline.com/media/catalog/product/cache/cce444513434d709cad419cac6756dc1/8/0/804001004.jpg'
        },
        '心海': {
            'flow': 7,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '打飛了',
            'image_url': 'https://assets2.rockpapershotgun.com/genshin-impact-sangonomiya-kokomi.jpg/BROK/thumbnail/1200x1200/quality/100/genshin-impact-sangonomiya-kokomi.jpg'
        },
        '大白鯊': {
            'flow': 10,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '咬到了',
            'image_url': 'https://static01.nyt.com/images/2020/08/12/multimedia/00xp-shark/00xp-shark-mediumSquareAt3X.jpg'
        },
        '大象': {
            'flow': 15,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '踩到了',
            'image_url': 'https://images.fineartamerica.com/images/artworkimages/mediumlarge/1/2-african-elephant-closeup-square-susan-schmitz.jpg'
        },
        '達達利鴨': {
            'flow': 20,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '踢了幾腳',
            'image_url': 'https://c.tenor.com/blHN79J-floAAAAd/ducktaglia-duck.gif'
        },
        '抹香鯨': {
            'flow': 20,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '鯨爆了',
            'image_url': 'https://i.natgeofe.com/n/8084965e-1dfc-47eb-b0c5-e4f86ee65c82/sperm-whale_thumb.jpg'
        },   
        '蝦蝦': {
            'flow': 25,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '鉗到了',
            'image_url': 'https://imgur.com/a/HHuKY9w'
        },
        '狗勾': {
            'flow': 25,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '咬到了',
            'image_url': 'http://pm1.narvii.com/7976/5fa6fb5fd68721c59702d97677b45a78692b0765r1-1050-1050v2_uhq.jpg'
        },
        '神子': {
            'flow': 25,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '調教了',
            'image_url': 'https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/0f0e05ad-e6a0-44a2-907b-bc681efe3066/dex25ww-10b366dd-7bd9-4656-a18f-33c4420b69c1.jpg/v1/fill/w_894,h_894,q_70,strp/chibi_yae_miko_fox_by_yohchii_dex25ww-pre.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTE4MSIsInBhdGgiOiJcL2ZcLzBmMGUwNWFkLWU2YTAtNDRhMi05MDdiLWJjNjgxZWZlMzA2NlwvZGV4MjV3dy0xMGIzNjZkZC03YmQ5LTQ2NTYtYTE4Zi0zM2M0NDIwYjY5YzEuanBnIiwid2lkdGgiOiI8PTExODEifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.n9BtnmHH_U3yJVIBKBHP6gX6kf0C2TazWhV6ZgTxcRQ'
        },
        '安妮亞': {
            'flow': 30,
            'flow_chance': None,
            'type_0': False,
            'cute': False,
            'verb': '揍了一拳',
            'image_url': 'https://img-9gag-fun.9cache.com/photo/aOQRZ66_460s.jpg'
        },
        '綾華': {
            'flow': 30,
            'flow_chance': None,
            'type_0': False,
            'cute': True,
            'verb': '扇了一巴',
            'image_url': 'https://i.pinimg.com/736x/df/b2/7a/dfb27a74b80ab17e975b8a2997d58faf.jpg'
        },
        '02': {
            'flow': 30,
            'flow_chance': None,
            'type_0': False,
            'cute': True,
            'verb': '調教了',
            'image_url': 'https://p.favim.com/orig/2018/12/11/02-kawaii-animw-Favim.com-6640354.jpg'
        },
    }
    
    fish_name_list = [
        '虱目魚', #0
        '鮭魚', #1
        '鱈魚', #2
        '鮪魚', #3
        '鰻魚', #4
        '企鵝', #5
        '兔兔', #6
        '雞雞',#7
        '龍蝦', #8
        '螃蟹', #9
        '心海', #10
        '大白鯊', #11
        '大象', #12
        '達達利鴨', #13
        '抹香鯨', #14
        '蝦蝦', #15
        '狗勾', #16
        '神子', #17
        '安妮亞', #18
        '綾華', #19
        '02', #20
        ]

    adj_list = ['可愛', '奇怪', '神奇', '變態', '色色', '野生', '開心', '傷心', '生氣']

    # fish_type = 1 扣幣
    # fish_type = 0 不扣幣

    def generate_fish_embed(self, index: int):  # 製造摸魚embed
        if fish[fish_name_list[index]] ['cute'] == True:
            fish_adj = '十分可愛'
            fish_type = 1
            flow = fish[fish_name_list[index]] ['flow']
            result = ayaakaaEmbed(
                fish_list[index],
                f'是**{fish_adj}的{fish_name_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_adj}的{fish_name_list[index]}**有機率獲得或損失 {flow} flow幣'
            )
                # e.g. 是野生的達達利鴨！要摸摸看嗎?
                #摸達達利鴨有機率獲得或損失 20 flow幣
        
        elif fish[fish_name_list[index]] ['type_0'] == True:
            fish_adj = random.choice(adj_list)
            fish_type = 0
            flow = fish[fish_name_list[index]] ['flow']
            result = ayaakaaEmbed(
                fish_name_list[index],
                f'是**{fish_adj}的{fish_name_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_adj}的{fish_name_list[index]}**有機率獲得 {flow} flow幣'
            )
            # e.g. 是可愛的鮭魚！要摸摸看嗎?
                #摸鮭魚有機率獲得 2 flow幣
        else:
            fish_adj = random.choice(adj_list)
            fish_type = 1
            flow = fish[fish_name_list[index]] ['flow']
            result = ayaakaaEmbed(
                fish_list[index],
                f'是**{fish_adj}的{fish_name_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_adj}的{fish_name_list[index]}**有機率獲得或損失 {flow} flow幣'
            )
                # e.g. 是野生的達達利鴨！要摸摸看嗎?
                #摸達達利鴨有機率獲得或損失 20 flow幣
        result.set_thumbnail(url=fish_image_list[index])
        return result, fish_adj, fish_type, flow

    class TouchFishButton(Button):  # 摸魚按鈕
        def __init__(self, index: int, db: aiosqlite.Connection, bot, fish_adj: str, fish_type: int, flow: int):
            super().__init__(style=ButtonStyle.blurple,
                             label=f'撫摸{fish_adj}的{fish_list[index]}')
            self.index = index
            self.flow_app = FlowApp(db, bot)
            self.fish_adj = fish_adj
            self.fish_type = fish_type
            self.flow = flow

        async def callback(self, interaction: Interaction):
            self.view.stop()
            self.disabled = True
            await interaction.response.edit_message(view=self.view)

            await interaction.channel.send(f'{interaction.user.mention} 摸到**{self.fish_adj}的{fish_name_list[self.index]}**了！')
            # e.g. @綾霞 摸到虱目魚了！

            value = randint(1, 100)  # Picks a random number from 1 - 100

            # 摸虱目魚有機率獲得 1 flow幣

            if self.fish_type == 1:
                verb = fish[fish_name_list[self.index]] [verb]
                if value <= 50:  # 50% Chance of increasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, int(flow))
                    await interaction.followup.send(f'摸**{self.fish_adj}的{fish_name_list[self.index]}**摸到 {flow} flow幣!', ephemeral=True)
                    # e.g. 摸抹香鯨摸到 20 flow幣!
                else:  # 50% Chance of decreasing flow amount by 20
                    await self.flow_app.transaction(interaction.user.id, -int(flow))
                    await interaction.followup.send(f'被**{self.fish_adj}的{fish_name_list[self.index]}**{verb}，損失了 {flow} flow幣 qwq', ephemeral=True)
                    # e.g. 抹香鯨 鯨爆了，損失了 20 flow幣 qwq

            else:
                if value <= int(fish_flow_chance_list[self.index]):
                    await self.flow_app.transaction(interaction.user.id, int(flow))
                    await interaction.followup.send(f'摸**{self.fish_adj}的{fish_name_list[self.index]}**摸到 {flow} flow幣!', ephemeral=True)
                    # e.g. 摸虱目魚摸到 1 flow幣!
                else:
                    await interaction.followup.send(f'單純的摸魚而已, 沒有摸到flow幣 qwq', ephemeral=True)

    class TouchFish(DefaultView):  # 摸魚view
        def __init__(self, index: str, db: aiosqlite.Connection, bot, fish_adj: str, fish_type: int, flow: int):
            super().__init__(timeout=None)
            self.add_item(FishCog.TouchFishButton(
                index, db, bot, fish_adj, fish_type, flow))

    def get_fish_choices():  # 取得所有魚種
        choices = []
        for fish in fish_name_list:
            choices.append(Choice(name=fish, value=fish_name_list.index(fish)))
        return choices

    @commands.Cog.listener()
    async def on_message(self, message):  # 機率放魚
        if message.author == self.bot.user:
            return
        random_number = randint(1, 100)
        if random_number == 1 and not isinstance(message.channel, Thread):
            index = randint(0, len(fish_name_list)-1)
            embed, fish_adj, fish_type, flow = self.generate_fish_embed(index)
            touch_fish_view = FishCog.TouchFish(
                index, self.bot.db, self.bot, fish_adj, fish_type, flow)
            await message.channel.send(embed=embed, view=touch_fish_view)

   # /releasefish
    @app_commands.command(name='releasefish放魚', description='緊急放出一條魚讓人摸')
    @app_commands.rename(fish_type='魚種')
    @app_commands.describe(fish_type='選擇要放出的魚種')
    @app_commands.choices(fish_type=get_fish_choices())
    @app_commands.checks.has_role('小雪團隊')
    async def release_fish(self, i: Interaction, fish_type: int):
        touch_fish_view = FishCog.TouchFish(fish_type, self.bot.db, self.bot)
        await i.response.send_message(embed=self.generate_fish_embed(fish_type), view=touch_fish_view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FishCog(bot))