from random import randint

from discord import Interaction, Member, Message, Role, app_commands
from discord.ext import commands
from discord.ui import Button
from debug import DefaultView
from utility.FlowApp import FlowApp
from utility.utils import defaultEmbed, log


class OtherCMDCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.flow_app = FlowApp(self.bot.db, self.bot)
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
            value = randint(1, 100)
            await message.channel.send(f"{value}%")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "QuoteTimeWakuWaku":
            log(True, False, 'Quote', payload.user_id)
            member = self.bot.get_user(payload.user_id)
            channel = self.bot.get_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            channel = self.bot.get_channel(payload.channel_id)
            emoji = self.bot.get_emoji(payload.emoji.id)
            await msg.remove_reaction(emoji, member)
            await channel.send(f"<a:check_animated:982579879239352370> 語錄擷取成功", delete_after=3)
            embed = defaultEmbed(
                f"語錄", f"「{msg.content}」\n  -{msg.author.mention}\n\n[點我回到該訊息]({msg.jump_url})")
            embed.set_thumbnail(url=str(msg.author.avatar))
            channel = self.bot.get_channel(966549110540877875)
            await channel.send(embed=embed)

    @app_commands.command(name='ping', description='查看機器人目前延遲')
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message('🏓 Pong! {0}s'.format(round(self.bot.latency, 1)))

    @app_commands.command(
        name='cute',
        description='讓申鶴說某個人很可愛'
    )
    @app_commands.rename(person='某個人')
    async def cute(self, interaction: Interaction, person: str):
        await interaction.response.send_message(f"{person}真可愛~❤")

    @app_commands.command(
        name='flash',
        description='防放閃機制'
    )
    async def flash(self, interaction: Interaction):
        await interaction.response.send_message("https://media.discordapp.net/attachments/823440627127287839/960177992942891038/IMG_9555.jpg")

    @app_commands.command(name='number', description='讓申鶴從兩個數字間挑一個隨機的給你')
    @app_commands.rename(num_one='數字一', num_two='數字二')
    async def number(self, interaction: Interaction, num_one: int, num_two: int):
        value = randint(int(num_one), int(num_two))
        await interaction.response.send_message(str(value))

    @app_commands.command(name='marry', description='結婚 💞')
    @app_commands.rename(person_one='攻', person_two='受')
    async def marry(self, interaction: Interaction, person_one: str, person_two: str):
        await interaction.response.send_message(f"{person_one} ❤ {person_two}")

    @app_commands.command(name='getid', description='查看discord ID獲取教學')
    async def check(self, interaction: Interaction):
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
        log(True, False, 'Quote', ctx.author.id)
        await ctx.message.delete()
        msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        embed = defaultEmbed(
            f"語錄", f"「{msg.content}」\n  -{msg.author.mention}\n\n[點我回到該訊息]({msg.jump_url})")
        embed.set_thumbnail(url=str(msg.author.avatar))
        channel = self.bot.get_channel(966549110540877875)
        await ctx.send("<a:check_animated:982579879239352370> 語錄擷取成功", delete_after=3)
        await channel.send(embed=embed)

    @app_commands.command(
        name='cleanup',
        description='移除此頻道某個使用者發送的最近n個訊息'
    )
    @app_commands.rename(number='訊息數量', member='使用者')
    async def cleanup(self, interaction: Interaction, number: int, member: Member):
        await interaction.response.send_message(embed=defaultEmbed('<a:LOADER:982128111904776242> 刪除中'), ephemeral=True)

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
        log(True, False, 'Quote', i.user.id)
        embed = defaultEmbed(
            f"語錄", f"「{msg.content}」\n  -{msg.author.mention}\n\n[點我回到該訊息]({msg.jump_url})")
        embed.set_thumbnail(url=str(msg.author.avatar))
        channel = self.bot.get_channel(966549110540877875)
        await i.response.send_message("<a:check_animated:982579879239352370> 語錄擷取成功", ephemeral=True)
        await channel.send(embed=embed)

    @app_commands.command(name='rolemembers', description='查看一個身份組內的所有成員')
    @app_commands.rename(role='身份組')
    @app_commands.describe(role='請選擇要查看的身份組')
    async def role_members(self, i: Interaction, role: Role):
        if role is None:
            await i.response.send_message('找不到該身份組!', ephemeral=True)
            return
        memberStr = ''
        count = 0
        for member in role.members:
            count += 1
            memberStr += f'{count}. {member}\n'
        embed = defaultEmbed(role.name, memberStr)
        await i.response.send_message(embed=embed)

    @app_commands.command(name='avatar', description='查看一個用戶的頭像(並且偷偷下載)')
    @app_commands.rename(member='使用者')
    async def avatar(self, i: Interaction, member: Member):
        embed = defaultEmbed(member)
        view = DefaultView()
        view.add_item(Button(label="下載頭像", url=member.avatar.url))
        embed.set_image(url=member.avatar)
        await i.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OtherCMDCog(bot))
