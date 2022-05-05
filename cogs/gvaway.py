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
        def __init__(self, interaction: discord.Interaction):
            super().__init__(timeout=None)
            self.interaction = interaction

        def ticket_flow_check(self, user_id: int, ticket: int):
            users = openFile('flow')
            if users[user_id]['flow'] < ticket:
                msg = errEmbed(
                    '你目前擁有的flow幣不夠!', f'你現在擁有: {users[user_id]["flow"]}\n參加需要: {ticket} flow')
                return False, msg
            else:
                return True, None

        def join_giveaway(self, user_id: int, ticket: int, gv_msg_id: int):
            print(log(True, False, __name__, f'(user_id={user_id}, ticket={ticket}, gv_msg_id={gv_msg_id})'))
            gv = openFile('giveaways')
            flow_app.transaction(user_id, -int(ticket))
            gv[gv_msg_id]['current'] += ticket
            if ticket < 0:
                gv[gv_msg_id]['members'].remove(user_id)
            else:
                gv[gv_msg_id]['members'].append(user_id)
            saveFile(gv, 'giveaways')

        async def update_gv_msg(self, gv_msg_id: int, role: discord.Role = None):
            channel = self.interaction.client.get_channel(965517075508498452)
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

        async def check_gv_finish(self, gv_msg_id: int, interaction: discord.Interaction):
            gv = openFile('giveaways')
            if gv[gv_msg_id]['current'] == gv[gv_msg_id]['goal']:
                channel = interaction.client.get_channel(965517075508498452)
                lulurR = interaction.client.get_user(665092644883398671)
                winner_id = random.choice(gv[gv_msg_id]['members'])
                winner = interaction.client.get_user(int(winner_id))
                embed = defaultEmbed(
                    "抽獎結果",
                    f"恭喜{winner.mention}獲得價值{gv[gv_msg_id]['goal']} flow幣的 {gv[gv_msg_id]['prize']} !")
                await channel.send(f"{lulurR.mention} {winner.mention}")
                await channel.send(embed=embed)
                print(log(True, False, 'Giveaway Ended', f'(gv_msg_id={gv_msg_id}, winner={winner_id})'))
                del gv[gv_msg_id]
                saveFile(gv, 'giveaways')

        def check_if_already_in_gv(self, user_id:int, gv_msg_id:int):
            gv = openFile('giveaways')
            if user_id in gv[gv_msg_id]['members']:
                embed = errEmbed('你已經參加過這個抽獎了','')
                return True, embed 
            else:
                embed = errEmbed('你沒有參加過這個抽獎','')
                return False, embed

        @discord.ui.button(label='參加抽獎',
                           style=discord.ButtonStyle.green)
        async def participate(self, interaction: discord.Interaction,
                              button: discord.ui.Button):
            msg = interaction.message
            check, check_msg = flow_app.checkFlowAccount(interaction.user.id)
            if check == False:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            gv = openFile('giveaways')
            ticket = gv[msg.id]['ticket']
            check, check_msg = self.ticket_flow_check(interaction.user.id, ticket)
            channel = interaction.client.get_channel(909595117952856084)
            if check == False:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            if msg.id in gv:
                if gv[msg.id]['role'] is not None:
                    guild = self.bot.get_guild(916838066117824553)
                    role = guild.get_role(gv[msg.id]['role'])
                    check, check_msg = self.check_if_already_in_gv(interaction.user.id, msg.id)
                    if check == True:
                        await interaction.response.send_message(embed=check_msg)
                        return
                    if role in interaction.user.roles:
                        self.join_giveaway(interaction.user.id, ticket, msg.id)
                        await interaction.response.send_message(embed=defaultEmbed(f'✅ 參加抽獎成功',f'flow幣 -{ticket}'), ephemeral=True)
                        await self.update_gv_msg(msg.id, role)
                        await channel.send(f"{interaction.user} 花了 {ticket} flow幣參加 {gv[msg.id]['prize']} 抽獎")
                        await self.check_gv_finish(msg.id, interaction)
                    else:
                        interaction.response.send_message(embed=errEmbed(
                            '非常抱歉', f'你不是{role.mention}的一員, 不能參加這個抽獎'), ephemeral=True)
                        return
                else:
                    check, check_msg = self.check_if_already_in_gv(interaction.user.id, msg.id)
                    if check == True:
                        await interaction.response.send_message(embed=check_msg)
                        return
                    self.join_giveaway(interaction.user.id, ticket, msg.id)
                    await interaction.response.send_message(embed=defaultEmbed(f'✅ 參加抽獎成功',f'flow幣 -{ticket}'), ephemeral=True)
                    await self.update_gv_msg(msg.id)
                    await channel.send(f"[抽獎][{interaction.user}] (ticket={ticket}, prize={gv[msg.id]['prize']})")
                    await self.check_gv_finish(msg.id, interaction)
            else:
                await interaction.response.send_message(embed=errEmbed('該抽獎不存在!', '(因為某些不明原因)'))

        @discord.ui.button(label='退出抽獎',
                           style=discord.ButtonStyle.grey)
        async def quit(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
            msg = interaction.message
            gv = openFile('giveaways')
            if msg.id in gv:
                ticket = -int(gv[msg.id]['ticket'])
                self.join_giveaway(interaction.user.id, ticket, msg.id)
                check, check_msg = self.check_if_already_in_gv(interaction.user.id, msg.id)
                if check == False:
                    await interaction.response.send_message(embed=check_msg)
                    return
                await interaction.response.send_message(embed=defaultEmbed(f'✅退出抽獎成功',f'flow幣 +{-int(ticket)}'), ephemeral=True)
                if gv[msg.id]['role'] is not None:
                    g = interaction.client.get_guild(916838066117824553)
                    role = g.get_role(gv[msg.id]['role'])
                    channel = interaction.client.get_channel(909595117952856084)
                    await self.update_gv_msg(msg.id, role)
                    await channel.send(f"{interaction.user} 收回了 {-int(ticket)} flow幣來取消參加 {gv[msg.id]['prize']} 抽獎")
                else:
                    await self.update_gv_msg(msg.id)
                    await channel.send(f"[抽獎][{interaction.user}] (ticket={-int(ticket)}, prize={gv[msg.id]['prize']})")

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
        view = self.GiveAwayView(interaction=interaction)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_message()
        if role is not None:
            await channel.send(role.mention)
            role_id = role.id
        else:
            g = self.bot.get_guild(916838066117824553)  # 緣神有你
            role = g.get_role(967035645610573834)  # 抽獎通知
            # await channel.send(role.mention)
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
