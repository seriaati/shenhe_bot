import discord
from discord.ext import commands
from discord.errors import Forbidden
from cmd.asset.global_vars import defaultEmbed, setFooter


async def send_embed(ctx, embed):
    try:
        await ctx.send(embed=embed)
    except Forbidden:
        try:
            await ctx.send("Hey, seems like I can't send embeds. Please check my permissions :)")
        except Forbidden:
            await ctx.author.send(
                f"Hey, seems like I can't send any message in {ctx.channel.name} on {ctx.guild.name}\n"
                f"May you inform the server team about this issue? :slight_smile: ", embed=embed)


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *input):
        prefix = "!"
        version = "v1.0.4"

        owner = 410036441129943050
        owner_name = "seria#5334"

        if not input:
            try:
                owner = ctx.guild.get_member(owner).mention

            except AttributeError as e:
                owner = owner

            emb = defaultEmbed(
                '指令與指令包', f'輸入 `{prefix}help <指令包名稱>` 來獲取關於該指令包的更多資訊 <:Ahhhhh:954017882021462066>')

            cogs_desc = ''
            for cog in self.bot.cogs:
                cogs_desc += f'`{cog}` {self.bot.cogs[cog].description}\n'

            emb.add_field(name='指令包', value=cogs_desc, inline=False)

            commands_desc = ''
            for command in self.bot.walk_commands():
                if not command.cog_name and not command.hidden:
                    commands_desc += f'{command.name} - {command.help}\n'

            if commands_desc:
                emb.add_field(name='不屬於任何指令包',
                              value=commands_desc, inline=False)

            emb.add_field(
                name="關於", value=f"這個機器人是小雪用python寫出來的\n有疑問、bug、或是功能意見都可以私訊她")
            emb.set_footer(text=f"目前版本: {version}")

        elif len(input) == 1:
            for cog in self.bot.cogs:
                if cog.lower() == input[0].lower():
                    emb = defaultEmbed(
                        f'{cog} - 指令', self.bot.cogs[cog].description)
                    for command in self.bot.get_cog(cog).get_commands():
                        if not command.hidden:
                            if not command.aliases:
                                emb.add_field(
                                    name=f"`{prefix}{command.name}`", value=command.help, inline=False)
                            else:
                                for a in command.aliases:
                                    emb.add_field(
                                        name=f"`{prefix}{command.name}`或`{prefix}{a}`", value=command.help, inline=False)

                    break
            else:
                emb = defaultEmbed("「這是什麼…？」",
                                   f"申鶴從來沒有聽過名為 `{input[0]}` 的指令包 :thinking:")
        elif len(input) > 1:
            emb = defaultEmbed("「太、太多了…」",
                               "請一次輸入最多一個指令包名稱")

        else:
            emb = discord.Embed(title="「這裡是哪裡…？」",
                                description="你是怎麼來到這裡的!?(小雪震驚\n請將此bug通報小雪, 謝謝",
                                color=discord.Color.red())
        await send_embed(ctx, emb)


def setup(bot):
    bot.add_cog(Help(bot))
