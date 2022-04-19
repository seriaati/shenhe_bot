from discord.ext.forms import Form
from discord.ext import commands
import yaml
from cmd.asset.global_vars import defaultEmbed, setFooter
import random

with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)
with open(f'cmd/asset/bank.yaml', encoding='utf-8') as file:
    bank = yaml.full_load(file)
with open(f'cmd/asset/giveaways.yaml', encoding='utf-8') as file:
    giveaways = yaml.full_load(file)


class FlowGiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reactor = self.bot.get_user(payload.user_id)
        if payload.message_id == 965143582178705459 or payload.message_id == 963972447600771092:
            return
        if payload.emoji.name == "🎉" and payload.user_id != self.bot.user.id:
            discordID = payload.user_id
            if payload.user_id not in users:
                user = self.bot.get_user(discordID)
                flowCog = self.bot.get_cog('FlowCog')
                await flowCog.register(channel, user, discordID)
                return
            if payload.message_id in giveaways:
                if users[discordID]['flow'] < giveaways[payload.message_id]['ticket']:
                    await channel.send(f"{reactor.mention} 你的flow幣數量不足以參加這項抽獎", delete_after=5)
                    return
                users[discordID]['flow'] -= giveaways[payload.message_id]['ticket']
                bank['flow'] += giveaways[payload.message_id]['ticket']
                giveaways[payload.message_id]['current'] += giveaways[payload.message_id]['ticket']
                giveaways[payload.message_id]['members'].append(payload.user_id)
                with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)
                with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(bank, file)
                with open(f'cmd/asset/giveaways.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(giveaways, file)
                giveawayMsg = await channel.fetch_message(payload.message_id)
                newEmbed = defaultEmbed(":tada: 抽獎啦!!!",
                                        f"獎品: {giveaways[payload.message_id]['prize']}\n目前flow幣: {giveaways[payload.message_id]['current']}/{giveaways[payload.message_id]['goal']}\n參加抽獎要付的flow幣: {giveaways[payload.message_id]['ticket']}\n\n註: 按🎉來支付flow幣並參加抽獎\n抽獎將會在目標達到後開始")
                await giveawayMsg.edit(embed=newEmbed)
                await channel.send(f"{reactor.mention} 花了 {giveaways[payload.message_id]['ticket']} flow幣參加 {giveaways[payload.message_id]['prize']} 抽獎", delete_after=5)
                if giveaways[payload.message_id]['current'] == giveaways[payload.message_id]['goal']:
                    memberList = giveaways[payload.message_id]['members']
                    winner = random.choice(memberList)
                    winnerID = int(winner)
                    winnerUser = self.bot.get_user(winnerID)
                    await giveawayMsg.delete()
                    embed = defaultEmbed(
                        "抽獎結果", f"恭喜{winnerUser.mention}獲得價值 {giveaways[payload.message_id]['goal']} flow幣的 {giveaways[payload.message_id]['prize']} !")
                    setFooter(embed)
                    await channel.send(embed=embed)
                    giveaways.remove(giveaways[payload.message_id])
                    with open(f'cmd/asset/giveaways.yaml', 'w', encoding='utf-8') as file:
                        yaml.dump(giveaways, file)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        reactor = self.bot.get_user(payload.user_id)
        if payload.message_id == 965143582178705459 or payload.message_id == 963972447600771092:
            return
        if payload.emoji.name == "🎉" and payload.user_id != self.bot.user.id and payload.message_id in giveaways:
            users[payload.user_id]['flow'] += giveaways[payload.message_id]['ticket']
            bank['flow'] -= giveaways[payload.message_id]['ticket']
            giveaways[payload.message_id]['current'] -= giveaways[payload.message_id]['ticket']
            giveaways[payload.message_id]['members'].remove(payload.user_id)
            with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(users, file)
            with open(f'cmd/asset/bank.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(bank, file)
            with open(f'cmd/asset/giveaways.yaml', 'w', encoding='utf-8') as file:
                yaml.dump(giveaways, file)
            giveawayMsg = await channel.fetch_message(payload.message_id)
            newEmbed = defaultEmbed(":tada: 抽獎啦!!!",
                                    f"獎品: {giveaways[payload.message_id]['prize']}\n目前flow幣: {giveaways[payload.message_id]['current']}/{giveaways[payload.message_id]['goal']}\n參加抽獎要付的flow幣: {giveaways[payload.message_id]['ticket']}\n\n註: 按🎉來支付flow幣並參加抽獎\n抽獎將會在目標達到後開始")
            await giveawayMsg.edit(embed=newEmbed)
            await channel.send(f"{reactor.mention} 收回了 {giveaways[payload.message_id]['ticket']} flow幣來取消參加 {giveaways[payload.message_id]['prize']} 抽獎", delete_after=5)

    @commands.command(aliases=['gv'])
    @commands.has_role("小雪團隊")
    async def giveaway(self, ctx):
        await ctx.message.delete()
        form = Form(ctx, '抽獎設置流程', cleanup=True)
        form.add_question('獎品是什麼?', 'prize')
        form.add_question('獎品價值多少flow幣?', 'goal')
        form.add_question('參與者得花多少flow幣參與抽獎?', 'ticket')
        form.edit_and_delete(True)
        form.set_timeout(60)
        await form.set_color("0xa68bd3")
        result = await form.start()
        embedGiveaway = defaultEmbed(
            ":tada: 抽獎啦!!!",
            f"獎品: {result.prize}\n目前flow幣: 0/{result.goal}\n參加抽獎要付的flow幣: {result.ticket}\n\n註: 按🎉來支付flow幣並參加抽獎\n抽獎將會在目標達到後開始")
        setFooter(embedGiveaway)
        await ctx.send("✅ 抽獎設置完成", delete_after=5)
        gvChannel = self.bot.get_channel(965517075508498452)
        giveawayMsg = await gvChannel.send(embed=embedGiveaway)
        await giveawayMsg.add_reaction('🎉')
        giveaways[giveawayMsg.id] = {
            'authorID': int(ctx.author.id),
            'prize': str(result.prize),
            'goal': int(result.goal),
            'ticket': int(result.ticket),
            'current': 0,
            'members': []
        }
        with open(f'cmd/asset/giveaways.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(giveaways, file)


def setup(bot):
    bot.add_cog(FlowGiveawayCog(bot))
