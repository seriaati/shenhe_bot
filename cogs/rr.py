import yaml
import discord
from discord.ext import commands
from utility.utils import defaultEmbed, setFooter
from discord.ext.forms import Form
import re


class ReactionRoles(commands.Cog, name='rr', description='表情符號身份組產生器'):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        with open(f'data/rr.yaml', encoding='utf-8') as file:
            rr = yaml.full_load(file)
        if payload.message_id in rr and payload.emoji.id in rr[payload.message_id]:
            emoteID = payload.emoji.id
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, id=rr[payload.message_id][emoteID])
            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        with open(f'data/rr.yaml', encoding='utf-8') as file:
            rr = yaml.full_load(file)
        if payload.message_id in rr and payload.emoji.id in rr[payload.message_id]:
            emoteID = payload.emoji.id
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            role = discord.utils.get(guild.roles, id=rr[payload.message_id][emoteID])
            await member.remove_roles(role)

    @commands.command(name='reactionrole', aliases=['rr'], help='創建一個表符身份組訊息')
    @commands.has_role('小雪團隊')
    async def _reactionrole(self, ctx):
        with open(f'data/rr.yaml', encoding='utf-8') as file:
            rr = yaml.full_load(file)
        roles = []
        emotes = []
        form = Form(ctx, '表符身份組設置', cleanup=True)
        form.add_question('訊息的標題是什麼?', 'title')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        title = result.title
        while True:
            optionForm = Form(ctx, '表符身份組設置', cleanup=True)
            optionForm.add_question('請tag要給予的身份組, 完成時請打「done」', 'role')
            optionForm.edit_and_delete(True)
            optionForm.set_timeout(60)
            await optionForm.set_color("0xa68bd3")
            optionReseult = await optionForm.start()

            if optionReseult.role == "done":
                break
            else:
                roleID = int(re.search(r'\d+', optionReseult.role).group())
                roles.append(roleID)

            emoteForm = Form(ctx, '表符身份組設置', cleanup=True)
            emoteForm.add_question('該身份組要用什麼表情符號代表?', 'emote')
            emoteForm.edit_and_delete(True)
            emoteForm.set_timeout(60)
            await emoteForm.set_color("0xa68bd3")
            emoteResult = await emoteForm.start()

            if emoteResult.emote == "done":
                break
            else:
                emoteID = int(re.search(r'\d+', emoteResult.emote).group())
                emotes.append(emoteID)

        str = ""
        count = 0
        for roleID in roles:
            role = discord.utils.get(ctx.guild.roles, id=roleID)
            emote = self.bot.get_emoji(emotes[count])
            str += f"{emote} • {role.mention}\n"
            count += 1
        embed = defaultEmbed(title, str)
        setFooter(embed)
        rollEmbed = await ctx.send(embed=embed)
        count = 0
        for roleID in roles:
            emojiID = emotes[count]
            rr[rollEmbed.id] = {emojiID: roleID}
            with open(f'data/rr.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(rr, file)
        for emote in emotes:
            emoji = self.bot.get_emoji(emote)
            await rollEmbed.add_reaction(emoji)


def setup(bot):
    bot.add_cog(ReactionRoles(bot))
