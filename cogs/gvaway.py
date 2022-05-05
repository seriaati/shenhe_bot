import random
from typing import Optional
import discord
from discord.ext import commands
from discord import Role, app_commands
from utility.FlowApp import flow_app

from utility.utils import defaultEmbed, errEmbed, log, openFile, saveFile


class GiveAwayCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    class GiveAwayView(discord.ui.View):
        def __init__(self, i: discord.Interaction):
            super().__init__(timeout=None)
            self.i = i

        def ticket_flow_check(self, user_id: int, ticket: int):
            users = openFile('flow')
            if users[user_id]['flow'] < ticket:
                msg = errEmbed(
                    '你目前擁有的flow幣不夠!', f'你現在擁有: {users[user_id]["flow"]}\n參加需要: {ticket} flow')
                return False, msg
            else:
                return True, None

        def join_giveaway(self, user_id: int, ticket: int, gv_msg_id: int):
            gv = openFile('giveaways')
            flow_app.transaction(user_id, -int(ticket))
            gv[gv_msg_id]['current'] += ticket
            if ticket < 0:
                gv[gv_msg_id]['members'].remove(user_id)
            else:
                gv[gv_msg_id]['members'].append(user_id)
            saveFile(gv, 'giveaways')

        async def update_gv_msg(self, gv_msg_id: int, role: discord.Role = None):
            channel = self.i.client.get_channel(965517075508498452)
            gv_msg = await channel.fetch_message(gv_msg_id)
            gv = openFile('giveaways')
            if role is not None:
                embed = defaultEmbed(
                    ":tada: 抽獎啦!!!",
                    f"獎品: {gv[gv_msg_id]['prize']}\n"
                    f"目前flow幣: {gv[gv_msg_id]['current']}/{gv[gv_msg_id]['goal']}\n"
                    f"參加抽獎要付的flow幣: {gv[gv_msg_id]['ticket']}\n"
                    f"此抽獎專屬於: {role.mention}成員")
            else:
                embed = defaultEmbed(
                    ":tada: 抽獎啦!!!",
                    f"獎品: {gv[gv_msg_id]['prize']}\n"
                    f"目前flow幣: {gv[gv_msg_id]['current']}/{gv[gv_msg_id]['goal']}\n"
                    f"參加抽獎要付的flow幣: {gv[gv_msg_id]['ticket']}")
            await gv_msg.edit(embed=embed)

        async def check_gv_finish(self, gv_msg_id: int, i: discord.Interaction):
            gv = openFile('giveaways')
            if gv[gv_msg_id]['current'] == gv[gv_msg_id]['goal']:
                channel = i.client.get_channel(965517075508498452)
                lulurR = i.client.get_user(665092644883398671)
                winner_id = random.choice(gv[gv_msg_id]['members'])
                winner = i.client.get_user(int(winner_id))
                embed = defaultEmbed(
                    "抽獎結果",
                    f"恭喜{winner.mention}獲得價值{gv[gv_msg_id]['goal']} flow幣的 {gv[gv_msg_id]['prize']} !")
                await channel.send(f"{lulurR.mention} {winner.mention}")
                await channel.send(embed=embed)
                del gv[gv_msg_id]
                saveFile(gv, 'giveaways')

        @discord.ui.button(label='參加抽獎',
                           style=discord.ButtonStyle.green)
        async def participate(self, i: discord.Interaction,
                              button: discord.ui.Button):
            msg = i.message
            check, msg = flow_app.checkFlowAccount(i.user.id)
            if check == False:
                await i.response.send_message(embed=msg, ephemeral=True)
                return
            gv = openFile('giveaways')
            ticket = gv[msg.id]['ticket']
            check, msg = self.ticket_flow_check(i.user.id, ticket)
            channel = i.client.get_channel(909595117952856084)
            if check == False:
                await i.response.send_message(embed=msg, ephemeral=True)
                return
            if msg.id in gv:
                if gv[msg.id]['role'] is not None:
                    guild = self.bot.get_guild(916838066117824553)
                    role = guild.get_role(gv[msg.id]['role'])
                    if role in i.user.roles:
                        self.join_giveaway(i.user.id, ticket, msg.id)
                        await i.response.send_message(f'參加抽獎成功, flow幣 -{ticket}')
                        await self.update_gv_msg(msg.id, role)
                        await channel.send(f"{i.user} 花了 {ticket} flow幣參加 {gv[msg.id]['prize']} 抽獎")
                        await self.check_gv_finish(msg.id, i)
                    else:
                        i.response.send_message(embed=errEmbed(
                            '非常抱歉', f'你不是{role.mention}的一員, 不能參加這個抽獎'), ephemeral=True)
                        return
                else:
                    self.join_giveaway(i.user.id, ticket, msg.id)
                    await i.response.send_message(f'參加抽獎成功, flow幣 -{ticket}')
                    await self.update_gv_msg(msg.id)
                    await channel.send(f"{i.user} 花了 {ticket} flow幣參加 {gv[msg.id]['prize']} 抽獎")
                    await self.check_gv_finish(msg.id, i)
            else:
                await i.response.send_message(embed=errEmbed('該抽獎不存在!', '(因為某些不明原因)'))

        @discord.ui.button(label='退出抽獎',
                           style=discord.ButtonStyle.red)
        async def quit(self, i: discord.Interaction,
                       button: discord.ui.Button):
            msg = i.message
            gv = openFile('giveaways')
            if msg.id in gv:
                ticket = -int(gv[msg.id]['ticket'])
                self.join_giveaway(i.user.id, ticket, msg.id)
                await i.response.send_message(f'退出抽獎成功, flow幣 +{-int(ticket)}')
                if gv[msg.id]['role'] is not None:
                    g = i.client.get_guild(916838066117824553)
                    role = g.get_role(gv[msg.id]['role'])
                    channel = i.client.get_channel(909595117952856084)
                    await self.update_gv_msg(msg.id, role)
                    await channel.send(f"{i.user} 收回了 {-int(ticket)} flow幣來取消參加 {gv[msg.id]['prize']} 抽獎")
                else:
                    await self.update_gv_msg(msg.id)
                    await channel.send(f"{i.user} 收回了 {-int(ticket)} flow幣來取消參加 {gv[msg.id]['prize']} 抽獎")

    @app_commands.command(name='giveaway', description='設置抽獎')
    @app_commands.checks.has_role('小雪團隊')
    @app_commands.rename(prize='獎品', goal='目標', ticket='參與金額', role='指定國籍')
    @app_commands.describe(
        prize='獎品是什麼?',
        goal='到達多少flow幣後進行抽獎?',
        ticket='參與者得花多少flow幣參與抽獎?')
    async def giveaway(
            self, interaction: discord.Interaction,
            prize: str, goal: int, ticket: int, role: Optional[Role] = None):
        print(log(False, False, 'giveaway',
              f'{interaction.user.id}: (prize={prize}, goal={goal}, ticket={ticket}, role={role})'))
        if role is not None:
            embed = defaultEmbed(
                ":tada: 抽獎啦!!!",
                f"獎品: {prize}\n"
                f"目前flow幣: 0/{goal}\n"
                f"參加抽獎要付的flow幣: {ticket}\n"
                f"此抽獎專屬於: {role.mention}成員")
        else:
            embed = defaultEmbed(
                ":tada: 抽獎啦!!!",
                f"獎品: {prize}\n"
                f"目前flow幣: 0/{goal}\n"
                f"參加抽獎要付的flow幣: {ticket}")
        channel = self.bot.get_channel(965517075508498452)
        view = self.GiveAwayView(i=interaction)
        await interaction.response.send_message(embed=embed, view=view)
        msg = interaction.original_message()
        if role is not None:
            await channel.send(role.mention)
            role_id = role.id
        else:
            g = self.bot.get_guild(916838066117824553)  # 緣神有你
            role = g.get_role(967035645610573834)  # 抽獎通知
            await channel.send(role.mention)
            role_id = None
        giveaways = openFile('giveaways')
        giveaways[msg.id] = {
            'authorID': int(interaction.user.id),
            'prize': str(prize),
            'goal': int(goal),
            'ticket': int(ticket),
            'current': 0,
            'members': [],
            'role': role_id
        }
        saveFile(giveaways, 'giveaways')

    @giveaway.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GiveAwayCog(bot))
