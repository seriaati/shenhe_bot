from discord.ext import commands
import global_vars
import asyncio
import sys
import getpass

owner = getpass.getuser()

sys.path.append(f'C:/Users/{owner}/shenhe_bot/asset')


global_vars.Global()


class VoteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def vote(self, ctx):
        options = []  # 儲存選項
        emojis = []  # 儲存表情符號
        embedAsk = global_vars.defaultEmbed("是關於什麼的投票?",
                                            "例如: ceye的頭像要用什麼")
        global_vars.setFooter(embedAsk)
        embedAsk = await ctx.send(embed=embedAsk)  # 提問

        def check(m):  # 確認回答的跟打指令的是否同一人
            return m.author == ctx.author and m.channel == ctx.channel
        try:
            message = await self.bot.wait_for('message',
                                              timeout=30.0,
                                              check=check)  # 等待答案，最多30秒
        except asyncio.TimeoutError:
            await ctx.send(global_vars.timeOutErrorMsg)  # 傳送錯誤訊息（超過30秒
            return
        else:
            question = message.content
            await message.delete()
            done = False  # 還沒打done
            while done == False:  # 只要還沒打done，持續提問選項
                embed = global_vars.defaultEmbed("請輸入投票的選項，當完成時，請打done",
                                                 "例如: 看牙醫的胡桃")
                global_vars.setFooter(embed)
                await embedAsk.edit(embed=embed)  # 提問選項

                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel
                try:
                    message = await self.bot.wait_for('message',
                                                      timeout=30.0,
                                                      check=check)  # 等待答案，最多30秒
                except asyncio.TimeoutError:
                    await ctx.send(global_vars.timeOutErrorMsg)  # 傳送錯誤訊息（超過30秒
                    return
                else:
                    option = message.content
                    await message.delete()
                    if option == "done":  # 打done
                        done = True
                    else:
                        done = False
                        options.append(option)
                        embed = global_vars.defaultEmbed("該選項要使用什麼表情符號來代表?",
                                                         "註: 只能使用此群組所擁有的表情符號\n如要新增表情符號，請告知Tedd")
                        global_vars.setFooter(embed)
                        await embedAsk.edit(embed=embed)  # 提問表情符號

                        def check(m):
                            return m.author == ctx.author and m.channel == ctx.channel
                        try:
                            message = await self.bot.wait_for('message',
                                                              timeout=30.0,
                                                              check=check)  # 等待答案，最多30秒
                        except asyncio.TimeoutError:
                            # 傳送錯誤訊息（超過30秒
                            await ctx.send(global_vars.timeOutErrorMsg)
                            return
                        else:
                            emoji = message.content
                            await message.delete()
                            emojis.append(emoji)  # 將表情符號加入陣列
                            done = False
            optionStr = ""  # 選項字串
            count = 0
            for option in options:
                optionStr = optionStr + \
                    emojis[count] + " : " + option + "\n"  # 將選項一行一行打出來
                count = count + 1
            embedPoll = global_vars.defaultEmbed(question, optionStr)
            global_vars.setFooter(embedPoll)
            await embedAsk.delete()
            message = await ctx.send(embed=embedPoll)  # 投票!
            for emoji in emojis:
                await message.add_reaction(emoji)  # 附加表情符號


def setup(bot):
    bot.add_cog(VoteCog(bot))
