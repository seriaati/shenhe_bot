from discord.ext import commands
from utility.utils import defaultEmbed, setFooter
from discord.ext.forms import Form


class VoteCog(commands.Cog, name='vote', description='投票'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='vote', aliases=['v'], help='發起投票')
    async def _vote(self, ctx):
        await ctx.message.delete()
        options = []
        emotes = []
        form = Form(ctx, '投票設置流程', cleanup=True)
        form.add_question('是關於什麼的投票?', 'title')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        title = result.title
        while True:
            optionForm = Form(ctx, '投票設置流程', cleanup=True)
            optionForm.add_question('請輸入投票選項, 完成時請打「done」', 'option')
            optionForm.edit_and_delete(True)
            optionForm.set_timeout(60)
            await optionForm.set_color("0xa68bd3")
            optionReseult = await optionForm.start()

            if optionReseult.option == "done":
                break
            else:
                options.append(optionReseult.option)

            emoteForm = Form(ctx, '投票設置流程', cleanup=True)
            emoteForm.add_question('該選項要用什麼表情符號代表?', 'emote')
            emoteForm.edit_and_delete(True)
            emoteForm.set_timeout(60)
            await emoteForm.set_color("0xa68bd3")
            emoteResult = await emoteForm.start()

            if emoteResult.emote == "done":
                break
            else:
                emotes.append(emoteResult.emote)

        optionStr = ""
        count = 0
        for option in options:
            optionStr += f"{emotes[count]}: {option}\n"
            count += 1
        embed = defaultEmbed(title, optionStr)
        setFooter(embed)
        poll = await ctx.send(embed=embed)
        for emote in emotes:
            await poll.add_reaction(emote)


def setup(bot):
    bot.add_cog(VoteCog(bot))
