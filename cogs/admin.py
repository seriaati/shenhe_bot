import asyncio
import io
from datetime import datetime, time

from discord import (File, Interaction, Member, Message, NotFound, RawMessageDeleteEvent,
                     Status, TextChannel, app_commands)
from discord.ext import commands
from utility.utils import defaultEmbed, errEmbed, time_in_range


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.debug: bool = self.bot.debug_toggle

    @commands.Cog.listener()
    async def on_presence_update(self, before: Member, after: Member):
        # 可以你麻煩你程式到yuyu 10:45~7:00時上線就留記錄嗎?
        target_id = 410036441129943050 if self.bot.debug_toggle else 565171333684658177
        if before.id != target_id or after.id != target_id:
            return
        now = datetime.now().time()
        if not time_in_range(time(22, 45, 0), time(7, 0, 0), now):
            return
        channel = self.bot.get_channel(
            909595117952856084) if self.bot.debug_toggle else self.bot.get_channel(976840575254933504)
        if before.status == Status.offline and after.status == Status.online:
            await channel.send(f'{(self.bot.get_user(target_id)).mention} 偷偷起床了')

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.id == self.bot.user.id:
            return
        sese_channel = self.bot.get_channel(
            984792329426714677) if self.debug else self.bot.get_channel(965842415913152522)
        if message.channel == sese_channel and len(message.attachments) != 0:
            for attachment in message.attachments:
                if not attachment.is_spoiler():
                    try:
                        await message.delete()
                    except NotFound:
                        pass
                    async with self.bot.session.get(attachment.proxy_url) as resp:
                        bytes_obj = io.BytesIO(await resp.read())
                        file = File(
                            bytes_obj, filename=attachment.filename, spoiler=True)
                    await message.channel.send(content=f'由 <@{message.author.id}> 寄出', file=file)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
        c: TextChannel = self.bot.get_channel(
            988698669442269184) if not self.bot.debug_toggle else self.bot.get_channel(909595117952856084)
        if payload.cached_message is not None:
            if payload.cached_message.author.id == self.bot.user.id:
                return
            if payload.cached_message.content == '!q':
                return
            attachment_str = '(含有附件)' if len(
                payload.cached_message.attachments) != 0 else ''
            embed = defaultEmbed(
                '訊息刪除',
                f'「{payload.cached_message.content} {attachment_str}」\n\n'
                f'用戶: {payload.cached_message.author.mention}\n'
                f'頻道: {payload.cached_message.channel.mention}\n'
                f'時間: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}\n'
                f'附近訊息: {payload.cached_message.jump_url}'
            )
            embed.set_footer(
                text=f'用戶 ID: {payload.cached_message.author.id}\n')
            embed.set_author(name=payload.cached_message.author,
                             icon_url=payload.cached_message.author.avatar)
            await c.send(embed=embed)
            if len(payload.cached_message.attachments) != 0:
                for a in payload.cached_message.attachments:
                    await c.send(file=await a.to_file(use_cached=True))

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        c: TextChannel = self.bot.get_channel(
            988698669442269184) if not self.bot.debug_toggle else self.bot.get_channel(909595117952856084)
        embed = defaultEmbed(
            '進群',
            f'用戶: {member.mention}\n'
            f'時間: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}\n'
        )
        embed.set_author(name=member, icon_url=member.avatar)
        embed.set_footer(text=f'用戶 ID: {member.id}')
        await c.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        c: TextChannel = self.bot.get_channel(
            988698669442269184) if not self.bot.debug_toggle else self.bot.get_channel(909595117952856084)
        embed = defaultEmbed(
            '退群',
            f'用戶: {member.mention}\n'
            f'時間: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}\n'
        )
        embed.set_author(name=member, icon_url=member.avatar)
        embed.set_footer(text=f'用戶 ID: {member.id}')
        await c.send(embed=embed)

    @app_commands.command(name='mute', description='禁言')
    @app_commands.rename(member='成員', minute='分鐘數')
    @app_commands.describe(member='要被禁言的成員', minute='要被禁言的分鐘數')
    @app_commands.checks.has_any_role('管理員', '台主', '臨時台主(申鶴用途)')
    async def mute(self, i: Interaction, member: Member, minute: int):
        role = i.guild.get_role(
            994934185179488337) if not self.bot.debug_toggle else i.guild.get_role(994943569313935370)
        await member.add_roles(role)
        await i.response.send_message(embed=defaultEmbed(message=f'{member.mention} 已被 {i.user.mention} 禁言 {minute} 分鐘').set_author(name='禁言', icon_url=member.avatar))
        await asyncio.sleep(minute*60)
        await member.remove_roles(role)

    @app_commands.command(name='unmute', description='取消禁言')
    @app_commands.rename(member='成員')
    @app_commands.describe(member='要被取消禁言的成員')
    @app_commands.checks.has_any_role('管理員', '台主', '臨時台主(申鶴用途)')
    async def unmute(self, i: Interaction, member: Member):
        role = i.guild.get_role(
            994934185179488337) if not self.bot.debug_toggle else i.guild.get_role(994943569313935370)
        await member.remove_roles(role)
        await i.response.send_message(embed=defaultEmbed(message=f'{i.user.mention} 已取消 {member.mention} 的禁言').set_author(name='取消禁言', icon_url=member.avatar))

    @app_commands.command(name='say', description='用申鶴說話')
    @app_commands.checks.has_role('小雪團隊')
    async def say(self, i: Interaction, message: str):
        await i.response.send_message('success', ephemeral=True)
        await i.channel.send(message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
