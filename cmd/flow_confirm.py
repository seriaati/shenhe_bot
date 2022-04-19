from discord.ext import commands
import yaml
from cmd.asset.global_vars import defaultEmbed, setFooter

with open(f'cmd/asset/flow.yaml', encoding='utf-8') as file:
    users = yaml.full_load(file)
with open(f'cmd/asset/confirm.yaml', encoding='utf-8') as file:
    confirms = yaml.full_load(file)


class FlowConfirmCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        with open(f'cmd/asset/confirm.yaml', encoding='utf-8') as file:
            confirms = yaml.full_load(file)
        if payload.message_id == 965143582178705459 or payload.message_id == 963972447600771092:
            return
        if payload.emoji.name == '🆗' and payload.user_id != self.bot.user.id:
            print("detected OK")
            if payload.message_id in confirms:
                authorID = confirms[payload.message_id]['authorID']
                receiverID = confirms[payload.message_id]['receiverID']
                flow = confirms[payload.message_id]['flow']
                type = confirms[payload.message_id]['type']
                title = confirms[payload.message_id]['title']
                if type == 4:
                    if authorID in users:
                        users[authorID]['flow'] += flow
                    if receiverID in users:
                        users[receiverID]['flow'] -= flow
                else:
                    if authorID in users:
                        users[authorID]['flow'] -= flow
                    if receiverID in users:
                        users[receiverID]['flow'] += flow

                author = self.bot.get_user(authorID)
                receiver = self.bot.get_user(receiverID)
                if type == 4:
                    embed = defaultEmbed("🆗 結算成功",
                                        f"幫忙名稱: {title}\n幫助人: {author.mention} **+{flow} flow幣**\n被幫助人: {receiver.mention} **-{flow} flow幣**")
                else:
                    embed = defaultEmbed("🆗 結算成功",
                                        f"委託名稱: {title}\n委託人: {author.mention} **-{flow} flow幣**\n接收人: {receiver.mention} **+{flow} flow幣**")
                setFooter(embed)
                await author.send(embed=embed)
                await receiver.send(embed=embed)
                del confirms[payload.message_id]
                with open(f'cmd/asset/confirm.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(confirms, file)
                with open(f'cmd/asset/flow.yaml', 'w', encoding='utf-8') as file:
                    yaml.dump(users, file)


def setup(bot):
    bot.add_cog(FlowConfirmCog(bot))
