import yaml
import discord
from discord.ext import commands
import asset.global_vars as Global
from asset.global_vars import defaultEmbed, setFooter
from discord.ext.forms import Form
import re


class Cog(commands.Cog, name='rr', description='表情符號身份組產生器'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='reactionrole', aliases=['rr'], help='創建一個表符身份組訊息')
    @commands.has_role('小雪團隊')
    async def _reactionrole(self, ctx):
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

            if optionReseult.option == "done":
                break
            else:
                roleID = int(re.search(r'\d+', result.role).group())
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
                emoteID = int(re.search(r'\d+', result.emote).group())
                emotes.append(emoteID)

        str = ""
        count = 0
        for roleID in roles:
            role = self.bot.get_role(roleID)
            emote = self.bot.get_emoji(emotes[count])
            str += f"{emote}: {role}\n"
            count += 1
        embed = defaultEmbed(title, str)
        setFooter(embed)
        rollEmbed = await ctx.send(embed=embed)
        for emote in emotes:
            emoji = self.bot.get_emoji(emote)
            await rollEmbed.add_reaction(emoji)


def setup(bot):
    bot.add_cog(Cog(bot))
