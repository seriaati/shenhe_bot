from datetime import datetime
from typing import Optional
from discord.ext import commands
from discord.ui import View, Select
from discord import Interaction, Member, SelectOption, app_commands, Message
from discord.utils import format_dt
from random import randint
from utility.FlowApp import flow_app
from utility.WishPaginator import WishPaginator
from utility.utils import defaultEmbed, log, openFile, saveFile


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

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if "機率" in message.content:
            print(log(True, False, 'Random', message.author.id))
            value = randint(1, 100)
            await message.channel.send(f"{value}%")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "QuoteTimeWakuWaku":
            print(log(True, False, 'Quote', payload.user_id))
            member = self.bot.get_user(payload.user_id)
            channel = self.bot.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            channel = self.bot.get_channel(payload.channel_id)
            emoji = self.bot.get_emoji(payload.emoji.id)
            await msg.remove_reaction(emoji, member)
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

    feature = app_commands.Group(name="feature", description="為申鶴提供建議")

    @feature.command(name='request', description='為申鶴提供建議')
    @app_commands.rename(request_name='建議名稱', desc='詳情')
    @app_commands.describe(request_name='為申鶴提供各式建議! 這能有效的幫助申鶴改進, 並漸漸變成大家喜歡的模樣', desc='如果打不下的話, 可以在這裡輸入建議的詳情')
    async def feature_request(self, i: Interaction, request_name: str, desc: Optional[str] = None):
        print(log(False, False, 'Feature Request',
              f'{i.user.id}: (request_name={request_name}, desc={desc})'))
        today = datetime.today()
        features = openFile('feature')
        desc = desc or '(沒有敘述)'
        features[request_name] = {
            'desc': desc,
            'time': today,
            'author': i.user.id
        }
        saveFile(features, 'feature')
        timestamp = format_dt(today)
        embed = defaultEmbed(
            request_name,
            f'{desc}\n'
            f'由{i.user.mention}提出\n'
            f'於{timestamp}')
        await i.response.send_message(
            content='✅ 建議新增成功, 內容如下',
            embed=embed,
            ephemeral=True
        )

    @feature.command(name='list', description='查看所有建議')
    @app_commands.checks.has_role('小雪團隊')
    async def feature_list(self, i: Interaction):
        print(log(False, False, 'Feature List', i.user.id))
        await i.response.defer()
        features = openFile('feature')
        if not bool(features):
            await i.followup.send(embed=defaultEmbed('目前還沒有任何建議呢!', '有想法嗎? 快使用`/feature request`指令吧!'))
            return
        embeds = []
        for feature_name, value in features.items():
            author = i.client.get_user(value['author'])
            timestamp = format_dt(value['time'])
            embed = defaultEmbed(
                feature_name,
                f'{value["desc"]}\n'
                f'由{author.mention}提出\n'
                f'於{timestamp}')
            embeds.append(embed)
        await WishPaginator(i, embeds).start(embeded=True)

    @feature_list.error
    async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    class FeatureSelector(Select):
        def __init__(self, feature_dict: dict):
            options = []
            for feature_name, value in feature_dict.items():
                options.append(SelectOption(
                    label=feature_name, value=feature_name))
            super().__init__(placeholder=f'選擇建議', min_values=1, max_values=1, options=options)

        async def callback(self, interaction: Interaction):
            features = openFile('feature')
            del features[self.values[0]]
            saveFile(features, 'feature')
            await interaction.response.send_message(
                embed=defaultEmbed(
                    '🎉 恭喜!',
                    f'完成了**{self.values[0]}**'
                )
            )

    class FeatureSelectorView(View):
        def __init__(self, feature_dict: dict):
            super().__init__(timeout=None)
            self.add_item(OtherCMDCog.FeatureSelector(feature_dict))

    @feature.command(name='complete', description='完成一項建議')
    @app_commands.checks.has_role('小雪團隊')
    async def feature_complete(self, i: Interaction):
        print(log(False, False, 'Feature Complete', i.user.id))
        features = openFile('feature')
        if not bool(features):
            await i.response.send_message(embed=defaultEmbed('目前沒有任何建議'))
            return
        view = OtherCMDCog.FeatureSelectorView(features)
        await i.response.send_message(view=view, ephemeral=True)

    @feature_complete.error
    async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @app_commands.command(
        name='ping',
        description='查看機器人目前延遲'
    )
    async def ping(self, interaction: Interaction):
        print(log(True, False, 'Ping', interaction.user.id))
        await interaction.response.send_message('🏓 Pong! {0}s'.format(round(self.bot.latency, 1)))

    @app_commands.command(
        name='cute',
        description='讓申鶴說某個人很可愛'
    )
    @app_commands.rename(person='某個人')
    async def cute(self, interaction: Interaction,
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
    async def flash(self, interaction: Interaction):
        print(log(True, False, 'Flash', interaction.user.id))
        await interaction.response.send_message("https://media.discordapp.net/attachments/823440627127287839/960177992942891038/IMG_9555.jpg")

    @app_commands.command(
        name='number',
        description='讓申鶴從兩個數字間挑一個隨機的給你'
    )
    @app_commands.rename(num_one='數字一', num_two='數字二')
    async def number(self, interaction: Interaction,
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
    async def marry(self, interaction: Interaction,
                    person_one: str, person_two: str
                    ):
        print(log(True, False, 'Marry', interaction.user.id))
        await interaction.response.send_message(f"{person_one} ❤ {person_two}")

    @app_commands.command(
        name='getid',
        description='查看discord ID獲取教學'
    )
    async def check(self, interaction: Interaction):
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

    @app_commands.command(
        name='cleanup',
        description='移除此頻道某個使用者發送的最近n個訊息'
    )
    @app_commands.rename(number='訊息數量', member='使用者')
    async def cleanup(self, interaction: Interaction, number: int, member: Member):
        print(log(True, False, 'Cleanup', interaction.user.id))
        await interaction.response.send_message(embed=defaultEmbed('⏳ 刪除中'), ephemeral=True)

        def is_me(m):
            return m.author == member
        channel = interaction.channel
        msg_count = 0
        limit = 0
        deleted = []
        while msg_count < number:
            while len(deleted) == 0:
                limit += 1
                deleted = await channel.purge(limit=limit, check=is_me)
            deleted = []
            limit = 0
            msg_count += 1
        await interaction.edit_original_message(embed=defaultEmbed(f'🗑️ 已移除來自 {member} 的 {number} 個訊息'))

    @app_commands.command(name='members', description='查看目前群組總人數')
    async def members(self, i: Interaction):
        g = i.user.guild
        await i.response.send_message(embed=defaultEmbed('群組總人數', f'目前共 {len(g.members)} 人'))

    async def quote_context_menu(self, i: Interaction, msg: Message) -> None:
        print(log(True, False, 'Quote', i.user.id))
        embed = defaultEmbed(
            f"語錄", f"「{msg.content}」\n  -{msg.author.mention}\n\n[點我回到該訊息]({msg.jump_url})")
        embed.set_thumbnail(url=str(msg.author.avatar))
        channel = self.bot.get_channel(966549110540877875)
        await i.response.send_message("✅ 語錄擷取成功", ephemeral=True)
        await channel.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OtherCMDCog(bot))
