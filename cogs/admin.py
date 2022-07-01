from datetime import datetime

from discord import (Member, Message, RawMessageDeleteEvent, TextChannel)
from discord.ext import commands
from utility.utils import defaultEmbed, errEmbed


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.debug: bool = self.bot.debug_toggle
        self.c: TextChannel = self.bot.get_channel(
            988698669442269184) if not self.bot.debug_toggle else self.bot.get_channel(909595117952856084)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.id == self.bot.user.id:
            return
        sese_channel = self.bot.get_channel(
            984792329426714677) if self.debug else self.bot.get_channel(965842415913152522)
        if message.channel == sese_channel and len(message.attachments) != 0:
            for attachment in message.attachments:
                if not attachment.is_spoiler():
                    await message.delete()
                    await message.channel.send(embed=errEmbed('在色色台發圖片請spoiler!'), delete_after=3)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent):
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
            await self.c.send(embed=embed)
            if len(payload.cached_message.attachments) != 0:
                for a in payload.cached_message.attachments:
                    await self.c.send(file=await a.to_file(use_cached=True))

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        embed = defaultEmbed(
            '進群',
            f'用戶: {member.mention}\n'
            f'時間: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}\n'
        )
        embed.set_author(name=member, icon_url=member.avatar)
        embed.set_footer(text=f'用戶 ID: {member.id}')
        await self.c.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        embed = defaultEmbed(
            '退群',
            f'用戶: {member.mention}\n'
            f'時間: {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}\n'
        )
        embed.set_author(name=member, icon_url=member.avatar)
        embed.set_footer(text=f'用戶 ID: {member.id}')
        await self.c.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
