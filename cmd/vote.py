from discord.ext import commands
from cmd.asset.global_vars import defaultEmbed, setFooter
from discord.ext.forms import Form


class VoteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def vote(self, ctx):
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
            form = Form(ctx, '投票設置流程', cleanup=True)
            form.add_question('請輸入投票選項, 完成時請打「done」', 'option')
            form.edit_and_delete(True)
            form.set_timeout(60)
            await form.set_color("0xa68bd3")
            result = await form.start()

            if result.option == "done":
                break
            else:
                options.append(result.option)

            form = Form(ctx, '投票設置流程', cleanup=True)
            form.add_question('該選項要用什麼表情符號代表?', 'emote')
            form.edit_and_delete(True)
            form.set_timeout(60)
            await form.set_color("0xa68bd3")
            result = await form.start()

            if result.option == "done":
                break
            else:
                emotes.append(result.emote)

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
