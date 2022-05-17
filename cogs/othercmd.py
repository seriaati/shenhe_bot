import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import Interaction, app_commands
from random import randint
from utility.FlowApp import flow_app
from utility.utils import defaultEmbed, ayaakaaEmbed, log


class OtherCMDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quote_ctx_menu = app_commands.ContextMenu(
            name='語錄',
            callback=self.quote_context_menu
        )
        self.bot.tree.add_command(self.quote_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.quote_ctx_menu.name, type=self.quote_ctx_menu.type)

# Touch Fish

# List of Fishes
# 1 flow
# [0]  虱目魚

# 2 flow
# [1]  鮭魚
# [2]  鱈魚
# [3]  鮪魚
# [4]  鰻魚

# 5 flow
# [5]  龍蝦
# [6]  螃蟹
# [7]  大王具足蟲

# 10 flow
# [8]  大白鯊

# 20 flow
# [9]  達達利鴨

    global fish_list, fish_flow_list, fish_image_list
    fish_flow_list = ['1', '2', '2', '2', '2', '5', '5', '5', '10', '20']
    fish_list = ['虱目魚', '鮭魚', '鱈魚', '鮪魚', '鰻魚',
                    '龍蝦', '螃蟹', '大王具足蟲', '大白鯊', '達達利鴨']
    fish_image_list = [
        'https://www.ocean-treasure.com/wp-content/uploads/2021/06/Milkfish.jpg',
        'https://cdn-fgbal.nitrocdn.com/KhVbtyNBpSvxGKkBoxbcDIRslLpQdgCA/assets/static/optimized/wp-content/uploads/2021/08/1daf341ee1fca75bef8327e080fa5b21.Salmon-Fillet-1-1-1536x1536.jpg',
        'https://seafoodfriday.hk/wp-content/uploads/2021/08/Cod-Fillet-1.jpg',
        'https://cdn-fgbal.nitrocdn.com/KhVbtyNBpSvxGKkBoxbcDIRslLpQdgCA/assets/static/optimized/wp-content/uploads/2021/08/327f113f6c4342a982213da7e1dfd5d8.Tuna-Fillet-1.jpg',
        'https://www.boilingtime.com/img/0630/f.jpg',
        'https://seafoodfriday.hk/wp-content/uploads/2021/08/Red-Lobster-1-1536x1536.jpg',
        'https://www.freshexpressonline.com/media/catalog/product/cache/cce444513434d709cad419cac6756dc1/8/0/804001004.jpg',
        'https://img.ruten.com.tw/s3/a2d/3e3/hobbycubic/e/69/b7/22034159596983_953.jpg',
        'https://static01.nyt.com/images/2020/08/12/multimedia/00xp-shark/00xp-shark-mediumSquareAt3X.jpg',
        'https://c.tenor.com/blHN79J-floAAAAd/ducktaglia-duck.gif'
    ]

    def generate_fish_embed(self, index: int):
        if 0 <= index <= 4:
            result = ayaakaaEmbed(
                fish_list[index],
                f'是可愛的**{fish_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_list[index]}**有機率獲得{fish_flow_list[index]}flow幣'
            )
            # e.g. 是可愛的鮭魚！要摸摸看嗎?
            #     摸鮭魚有機率獲得 2 flow幣
            result.set_image(url=fish_image_list[index])
        else:
            result = ayaakaaEmbed(
                fish_list[index],
                f'是野生的**{fish_list[index]}**！要摸摸看嗎?\n'
                f'摸**{fish_list[index]}**有機率獲得或損失{fish_flow_list[index]}flow幣'
            )
            # e.g. 是野生的達達利鴨！要摸摸看嗎?
            #     摸達達利鴨有機率獲得或損失 20 flow幣
            result.set_image(url=fish_image_list[index])
        return result

    class TouchFishButton(Button):
        def __init__(self, index:int):
            super().__init__(style=discord.ButtonStyle.blurple, label=f'撫摸可愛的{fish_list[index]}')
            self.index = index
        
        async def callback(self, interaction: discord.Interaction):
            assert self.view is not None
            view = self.view
            view.stop()
            
            await interaction.channel.send(f'{interaction.user.mention} 摸到 {fish_list[self.index]} 了！')
            # e.g. @綾霞 摸到魚了！

            value = randint(1, 100)  # Picks a random number from 1 - 100

            # 摸虱目魚有機率獲得 1 flow幣

            if self.index == 0:  # [0] 虱目魚
                if value <= 60:  # 60% Chance of increasing flow amount by 1
                    flow_app.transaction(interaction.user.id, 1)
                    await interaction.response.send_message(f'摸**{fish_list[self.index]}**摸到 1 flow幣!', ephemeral=True)
                    # e.g. 摸虱目魚摸到 1 flow幣!
                else:
                    await interaction.response.send_message(f'單純的摸魚而已, 沒有摸到flow幣 qwq', ephemeral=True)

            # 摸鮭魚, 鱈魚, 鮪魚 或 鰻魚有機率獲得 2 flow幣
            # [1] 鮭魚, [2] 鱈魚, [3] 鮪魚, [4] 鰻魚
            elif self.index >= 1 and self.index <= 4:
                if value <= 30:  # 30% Chance of increasing flow amount by 2
                    flow_app.transaction(interaction.user.id, 2)
                    await interaction.response.send_message(f'摸**{fish_list[self.index]}**摸到 2 flow幣!', ephemeral=True)
                    # e.g. 摸鮭魚摸到 2 flow幣!
                else:
                    await interaction.response.send_message('單純的摸魚而已, 沒有摸到flow幣 qwq', ephemeral=True)

            # 摸龍蝦, 螃蟹 或 大王具足蟲有機率獲得或損失 5 flow幣
            # [5] 龍蝦, [6] 螃蟹, [7] 大王具足蟲
            elif self.index >= 5 and self.index <= 7:
                if value <= 50:  # 50% Chance of increasing flow amount by 5
                    flow_app.transaction(interaction.user.id, 5)
                    await interaction.response.send_message(f'摸**{fish_list[self.index]}**摸到 5 flow幣!', ephemeral=True)
                    # e.g. 摸龍蝦摸到 5 flow幣!
                else:  # 50% Chance of decreasing flow amount by 5
                    flow_app.transaction(interaction.user.id, -5)
                    await interaction.response.send_message(f'被**{fish_list[self.index]}**鉗到了，損失了 5 flow幣 qwq', ephemeral=True)
                    # e.g. 被龍蝦鉗到了，損失了 5 flow幣 qwq

            # 摸大白鯊有機率獲得或損失 10 flow幣
            elif self.index == 8:  # [8] 大白鯊
                if value <= 50:  # 50% Chance of increasing flow amount by 10
                    flow_app.transaction(interaction.user.id, 10)
                    await interaction.response.send_message(f'摸**{fish_list[self.index]}**摸到 10 flow幣!', ephemeral=True)
                    # e.g. 摸大白鯊 摸到 10 flow幣!
                else:  # 50% Chance of decreasing flow amount by 10
                    flow_app.transaction(interaction.user.id, -10)
                    await interaction.response.send_message(f'被**{fish_list[self.index]}**咬到了，損失了 10 flow幣 qwq', ephemeral=True)
                    # e.g. 被大白鯊咬到了，損失了 10 flow幣 qwq

            # 摸達達利鴨有機率獲得或損失 20 flow幣
            elif self.index == 9:  # [9] 達達利鴨
                if value <= 50:  # 50% Chance of increasing flow amount by 20
                    flow_app.transaction(interaction.user.id, 20)
                    await interaction.response.send_message(f'摸**{fish_list[self.index]}**摸到 20 flow幣!', ephemeral=True)
                    # e.g. 摸達達利鴨摸到 30 flow幣!
                else:  # 50% Chance of decreasing flow amount by 20
                    flow_app.transaction(interaction.user.id, -20)
                    await interaction.response.send_message(f'被**{fish_list[self.index]}**偷襲，損失了 20 flow幣 qwq', ephemeral=True)
                    # e.g. 被達達利鴨偷襲，損失了 30 flow幣 qwq
    
    class TouchFish(View):
        def __init__(self, index: str):
            super().__init__(timeout=None)
            self.add_item(OtherCMDCog.TouchFishButton(index))
        

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if "機率" in message.content:
            print(log(True, False, 'Random', message.author.id))
            value = randint(1, 100)
            await message.channel.send(f"{value}%")
        random_number = randint(1, 100)
        random_number = 1
        if random_number == 1:
            index = randint(0, len(fish_list)-1)
            touch_fish_view = OtherCMDCog.TouchFish(index)
            await message.channel.send(embed=self.generate_fish_embed(index), view=touch_fish_view)

   # /fish
    @app_commands.command(name='fish', description='緊急放出一條魚讓人摸')
    @app_commands.checks.has_role('小雪團隊')
    async def release_fish(self, i: Interaction):
        index = randint(0, len(fish_list)-1)
        touch_fish_view = OtherCMDCog.TouchFish(index)
        await i.response.send_message(embed=self.generate_fish_embed(index), view=touch_fish_view)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "QuoteTimeWakuWaku":
            print(log(True, False, 'Quote', payload.user_id))
            channel = self.bot.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            channel = self.bot.get_channel(payload.channel_id)
            emoji = self.bot.get_emoji(payload.emoji.id)
            await msg.remove_reaction(emoji)
            await channel.send(f"✅ 語錄擷取成功", delete_after=3)
            embed = defaultEmbed(
                f"語錄", f"「{msg.content}」\n  -{msg.author.mention}\n\n[點我回到該訊息]({msg.jump_url})")
            embed.set_thumbnail(url=str(msg.author.avatar))
            channel = self.bot.get_channel(966549110540877875)
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        public = self.bot.get_channel(916951131022843964)
        uid_channel = self.bot.get_channel(935111580545343509)
        embed = defaultEmbed(
            "重要事項",
            f"• 至{uid_channel.mention}輸入原神uid\n"
            "• 輸入`/role`指令選擇原神世界等級\n"
            "• 如果需要原神幫助, 可以使用`/find`指令\n"
            "• [什麼是flow幣?](https://discord.com/channels/916838066117824553/965964989875757156/966252132355424286)\n"
            "• 想在dc內直接查閱原神樹脂數量嗎? 輸入`/cookie`來設定你的帳號吧!\n"
            "• 最重要的, 祝你在這裡玩的開心! <:omg:969823101133160538>")
        embed.set_thumbnail(url=member.avatar)
        flow_app.register(member.id)
        await public.send(content=f"{member.mention}歡迎來到緣神有你!", embed=embed)

    @app_commands.command(
        name='ping',
        description='查看機器人目前延遲'
    )
    async def ping(self, interaction: discord.Interaction):
        print(log(True, False, 'Ping', interaction.user.id))
        await interaction.response.send_message('🏓 Pong! {0}s'.format(round(self.bot.latency, 1)))

    @app_commands.command(
        name='cute',
        description='讓申鶴說某個人很可愛'
    )
    @app_commands.rename(person='某個人')
    async def cute(self, interaction: discord.Interaction,
                   person: str
                   ):
        print(log(True, False, 'Cute', interaction.user.id))
        await interaction.response.send_message(f"{person}真可愛~❤")

    @app_commands.command(name='say', description='讓申鶴幫你說話')
    @app_commands.rename(msg='訊息')
    @app_commands.describe(msg='要讓申鶴幫你說的訊息')
    async def say(self, i: Interaction, msg: str):
        print(log(False, False, 'Say', i.user.id))
        channel = i.channel
        await i.response.send_message('已發送', ephemeral=True)
        await i.channel.send(msg)

    @app_commands.command(
        name='flash',
        description='防放閃機制'
    )
    async def flash(self, interaction: discord.Interaction):
        print(log(True, False, 'Flash', interaction.user.id))
        await interaction.response.send_message("https://media.discordapp.net/attachments/823440627127287839/960177992942891038/IMG_9555.jpg")

    @app_commands.command(
        name='number',
        description='讓申鶴從兩個數字間挑一個隨機的給你'
    )
    @app_commands.rename(num_one='數字一', num_two='數字二')
    async def number(self, interaction: discord.Interaction,
                     num_one: int, num_two: int
                     ):
        print(log(True, False, 'Random Number', interaction.user.id))
        value = randint(int(num_one), int(num_two))
        await interaction.response.send_message(str(value))

    @app_commands.command(
        name='marry',
        description='結婚 💞'
    )
    @app_commands.rename(person_one='攻', person_two='受')
    async def marry(self, interaction: discord.Interaction,
                    person_one: str, person_two: str
                    ):
        print(log(True, False, 'Marry', interaction.user.id))
        await interaction.response.send_message(f"{person_one} ❤ {person_two}")

    @app_commands.command(
        name='getid',
        description='查看discord ID獲取教學'
    )
    async def check(self, interaction: discord.Interaction):
        print(log(True, False, 'Get Discord ID', interaction.user.id))
        embed = defaultEmbed(
            "如何取得discord ID?",
            "1. 打開dc設定\n"
            "2.「進階」\n"
            "3. 把「開發者模式」打開\n"
            "4. 右鍵使用者頭像, 便可以看到「copy ID」"
        )
        await interaction.response.send_message(embed=embed)

    @commands.command(aliases=['q'])
    async def quote(self, ctx):
        print(log(True, False, 'Quote', ctx.author.id))
        await ctx.message.delete()
        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        embed = defaultEmbed(
            f"語錄", f"「{msg.content}」\n  -{msg.author.mention}\n\n[點我回到該訊息]({msg.jump_url})")
        embed.set_thumbnail(url=str(msg.author.avatar))
        channel = self.bot.get_channel(966549110540877875)
        await ctx.send("✅ 語錄擷取成功", delete_after=3)
        await channel.send(embed=embed)

    def is_me(self, m):
        return m.author == self.bot.user

    @app_commands.command(
        name='cleanup',
        description='移除此頻道申鶴發送的最近n個訊息'
    )
    @app_commands.rename(number='訊息數量')
    async def cleanup(self, interaction: discord.Interaction,
                      number: int
                      ):
        print(log(True, False, 'Cleanup', interaction.user.id))
        channel = interaction.channel
        deleted = await channel.purge(limit=int(number), check=self.is_me)
        await interaction.response.send_message('🗑️ 已移除 {} 個訊息'.format(len(deleted)), ephemeral=True)

    @app_commands.command(name='members', description='查看目前群組總人數')
    async def members(self, i: Interaction):
        g = i.user.guild
        await i.response.send_message(embed=defaultEmbed('群組總人數', f'目前共 {len(g.members)} 人'))

    async def quote_context_menu(self, i: discord.Interaction, msg: discord.Message) -> None:
        print(log(True, False, 'Quote', i.user.id))
        embed = defaultEmbed(
            f"語錄", f"「{msg.content}」\n  -{msg.author.mention}\n\n[點我回到該訊息]({msg.jump_url})")
        embed.set_thumbnail(url=str(msg.author.avatar))
        channel = self.bot.get_channel(966549110540877875)
        await i.response.send_message("✅ 語錄擷取成功", ephemeral=True)
        await channel.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OtherCMDCog(bot))
