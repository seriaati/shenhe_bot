import yaml
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from utility.utils import defaultEmbed
from discord import Role
import re


class ReactionRoles(commands.Cog, name='rr', description='表情符號身份組產生器'):
    def __init__(self, bot):
        self.bot = bot
        with open(f'data/rr.yaml', encoding='utf-8') as file:
            self.rr_dict = yaml.full_load(file)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        rr = dict(self.rr_dict)
        if payload.message_id in rr and payload.emoji.id in rr[payload.message_id]:
            emoteID = payload.emoji.id
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, id=rr[payload.message_id][emoteID])
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        rr = dict(self.rr_dict)
        if payload.message_id in rr and payload.emoji.id in rr[payload.message_id]:
            emoteID = payload.emoji.id
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, id=rr[payload.message_id][emoteID])
            await member.remove_roles(role)

    @app_commands.command(name='reactionrole', description='創建一個表符身份組訊息')
    @app_commands.rename(title='標題',role='身份組',emote='表情符號')
    @app_commands.checks.has_role('小雪團隊')
    async def reactionrole(self, interaction:discord.Interaction,title:str,role:Role,emote:str):
        rr = dict(self.rr_dict)
        emoteID = int(re.search(r'\d+', emote).group())
        emoteObj = self.bot.get_emoji(emoteID)
        embed = defaultEmbed(title, f"{emoteObj} • {role.mention}")
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_message()
        rr[msg.id] = {emoteID: role.id}
        with open(f'data/rr.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(rr, file)
        await msg.add_reaction(emoteObj)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
