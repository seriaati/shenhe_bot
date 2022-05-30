from discord import Member, VoiceChannel, app_commands, VoiceState
from discord.ext import commands


class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        vc: VoiceChannel = self.bot.get_channel(980772222148952064) if not self.bot.debug_toggle else self.bot.get_channel(980775512437837834)
        vc_role = member.guild.get_role(980774103344640000) if not self.bot.debug_toggle else member.guild.get_role(980774369771008051)
        old_channel: VoiceChannel = before.channel
        new_channel: VoiceChannel = after.channel
        if new_channel == vc:
            member_vc = await member.guild.create_voice_channel(name=f'{member.name}的語音台', category=vc.category)
            await member.move_to(member_vc)
            await member.add_roles(vc_role)
        if new_channel is None:
            await member.remove_roles(vc_role)
        if (new_channel is None or new_channel == vc) and old_channel is not None and len(old_channel.members) == 0:
            await old_channel.delete()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceChannel(bot))
