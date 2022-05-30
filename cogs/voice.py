from discord import Member, VoiceChannel, app_commands, VoiceState
from discord.ext import commands


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState):
        vc: VoiceChannel = self.bot.get_channel(980622022277214278)
        old_channel: VoiceChannel = before.channel
        new_channel: VoiceChannel = after.channel
        if new_channel is None and len(old_channel.members) == 0: 
            await old_channel.delete()
        if new_channel == vc:
            member_vc = await member.guild.create_voice_channel(name=member.name, category=vc.category)
            await member.move_to(member_vc)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
