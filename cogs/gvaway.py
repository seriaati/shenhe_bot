import random
from typing import List, Optional
import discord
from discord.ext import commands
from discord import Interaction, Role, app_commands
from discord.app_commands import Choice
from utility.FlowApp import flow_app
from utility.utils import defaultEmbed, errEmbed, log, openFile, saveFile


class GiveAwayCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    def generate_gv_embed(self, gv_msg_id: int, i:Interaction):
        gv = openFile('giveaways')
        role = i.guild.get_role(gv[gv_msg_id]['role'])
        role_exclusive = f'此抽獎專屬於: {role.mention}成員' if role is not None else '任何人都可以參加這個抽獎'
        refund_state = '(會退款)' if gv[gv_msg_id]['refund_mode'] == True else '(不會退款)'
        embed = defaultEmbed(
            ":tada: 抽獎啦!!!",
            f"獎品: {gv[gv_msg_id]['prize']}\n"
            f"目前flow幣: {gv[gv_msg_id]['current']}/{gv[gv_msg_id]['goal']}\n"
            f"參加抽獎要付的flow幣: {gv[gv_msg_id]['ticket']}\n"
            f"{role_exclusive}\n"
            f'{refund_state}\n'
            f"輸入`/join`指令來參加抽獎")
        return embed

    @app_commands.command(name='giveaway', description='設置抽獎')
    @app_commands.checks.has_role('小雪團隊')
    @app_commands.rename(prize='獎品', goal='目標', ticket='參與金額', role='指定國籍', refund_mode='退款模式')
    @app_commands.describe(
        prize='獎品是什麼?',
        goal='到達多少flow幣後進行抽獎?',
        ticket='參與者得花多少flow幣參與抽獎?',
        role='只有哪些身份組擁有著可以參加抽獎?',
        refund_mode='是否要開啟退款模式?')
    @app_commands.choices(refund_mode=[
        Choice(name='是', value=0),
        Choice(name='否', value=1)
    ])
    async def giveaway(
            self, interaction: discord.Interaction,
            prize: str, goal: int, ticket: int, role: Optional[Role] = None, refund_mode: int = 1):
        print(log(False, False, 'giveaway',
              f'{interaction.user.id}: (prize={prize}, goal={goal}, ticket={ticket}, role={role}, refund_mode={refund_mode})'))
        channel = interaction.client.get_channel(965517075508498452)  # 抽獎台
        # channel = interaction.client.get_channel(909595117952856084) #測試抽獎台
        role_exclusive = f'此抽獎專屬於: {role.mention}成員' if role is not None else '任何人都可以參加這個抽獎'
        refund_state = '(會退款)' if refund_mode == 0 else '(不會退款)'
        await interaction.response.send_message(embed = defaultEmbed(
            ":tada: 抽獎啦!!!",
            f"獎品: {prize}\n"
            f"目前flow幣: 0/{goal}\n"
            f"參加抽獎要付的flow幣: {ticket}\n"
            f"{role_exclusive}\n"
            f'{refund_state}\n'
            f"輸入`/join`指令來參加抽獎"))
        refund_mode_toggle = True if refund_mode == 0 else False
        msg = await interaction.original_message()
        gv = openFile('giveaways')
        gv[msg.id] = {
            'authorID': int(interaction.user.id),
            'prize': str(prize),
            'goal': int(goal),
            'ticket': int(ticket),
            'current': 0,
            'members': [],
            'role': role.id,
            'refund_mode': refund_mode_toggle
        }
        saveFile(gv, 'giveaways')
        if role is not None:
            await channel.send(role.mention)
        else:
            await channel.send(role.mention)

    @giveaway.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    class GiveAwayView(discord.ui.View):
        def __init__(self, interaction: discord.Interaction, gv_msg_id: int):
            super().__init__(timeout=None)
            self.interaction = interaction
            self.msg_id = gv_msg_id

        def ticket_flow_check(self, user_id: int, ticket: int):
            users = openFile('flow')
            if users[user_id]['flow'] < ticket:
                msg = errEmbed(
                    '你目前擁有的flow幣不夠!', f'你現在擁有: {users[user_id]["flow"]}\n參加需要: {ticket} flow')
                return False, msg
            else:
                return True, None

        def join_giveaway(self, user_id: int, ticket: int, gv_msg_id: int):
            print(log(True, False, 'join giveaway',
                  f'(user_id={user_id}, ticket={ticket}, gv_msg_id={gv_msg_id})'))
            gv = openFile('giveaways')
            flow_app.transaction(user_id, -int(ticket))
            gv[gv_msg_id]['current'] += ticket
            if ticket < 0:
                gv[gv_msg_id]['members'].remove(user_id)
            else:
                gv[gv_msg_id]['members'].append(user_id)
            saveFile(gv, 'giveaways')

        async def update_gv_msg(self, input_gv_msg_id: int):
            channel = self.interaction.client.get_channel(965517075508498452) #抽獎台
            # channel = self.interaction.client.get_channel(909595117952856084) #測試抽獎台
            gv_msg = await channel.fetch_message(input_gv_msg_id)
            await gv_msg.edit(embed=GiveAwayCog.generate_gv_embed(self, gv_msg_id=input_gv_msg_id, i=self.interaction))

        async def check_gv_finish(self, gv_msg_id: int, i: Interaction):
            gv = openFile('giveaways')
            if gv[gv_msg_id]['current'] == gv[gv_msg_id]['goal']:
                channel = i.client.get_channel(965517075508498452)
                lulurR = i.client.get_user(665092644883398671)
                winner_id = random.choice(gv[gv_msg_id]['members'])
                winner = i.client.get_user(int(winner_id))
                embed = defaultEmbed(
                    "🎉 抽獎結果",
                    f"恭喜{winner.mention}獲得價值{gv[gv_msg_id]['goal']} flow幣的 {gv[gv_msg_id]['prize']} !")
                await channel.send(f"{lulurR.mention} {winner.mention}")
                await channel.send(embed=embed)
                if gv[gv_msg_id]['refund_mode'] == True: #進行退款
                    for user_id in gv[gv_msg_id]['members']:
                        if winner_id!=user_id: #如果該ID不是得獎者
                            flow_app.transaction(user_id, int(gv[gv_msg_id]['ticket'])/2) #退款入場費/2
                print(log(True, False, 'Giveaway Ended',
                      f'(gv_msg_id={gv_msg_id}, winner={winner_id})'))
                del gv[gv_msg_id]
                saveFile(gv, 'giveaways')

        def check_if_already_in_gv(self, user_id: int, gv_msg_id: int):
            gv = openFile('giveaways')
            if user_id in gv[gv_msg_id]['members']:
                embed = errEmbed('你已經參加過這個抽獎了', '')
                return True, embed
            if user_id not in gv[gv_msg_id]['members']:
                embed = errEmbed('你沒有參加過這個抽獎', '')
                return False, embed

        @discord.ui.button(label='參加抽獎',
                           style=discord.ButtonStyle.green)
        async def participate(self, interaction: discord.Interaction,
                              button: discord.ui.Button):
            msg_id = self.msg_id
            check, check_msg = flow_app.checkFlowAccount(interaction.user.id)
            if check == False:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            gv = openFile('giveaways')
            ticket = gv[msg_id]['ticket']
            check, check_msg = self.ticket_flow_check(
                interaction.user.id, ticket)
            if check == False:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            check, check_msg = self.check_if_already_in_gv(
                interaction.user.id, msg_id)
            if check == True:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            if msg_id in gv:
                r = interaction.guild.get_role(gv[msg_id]['role'])
                if r is not None and r not in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed(
                        '非常抱歉', f'你不是{r.mention}的一員, 不能參加這個抽獎'), ephemeral=True)
                    return
                self.join_giveaway(interaction.user.id, ticket, msg_id)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ 參加抽獎成功', f'flow幣 -{ticket}'), ephemeral=True)
                await interaction.followup.send(embed=GiveAwayCog.generate_gv_embed(self, gv_msg_id=msg_id, i=interaction), ephemeral=True)
                await self.update_gv_msg(msg_id)
                await self.check_gv_finish(gv_msg_id=msg_id, i=interaction)
            else:
                await interaction.response.send_message(embed=errEmbed('該抽獎不存在!', '(因為某些不明原因)'))

        @discord.ui.button(label='退出抽獎',
                           style=discord.ButtonStyle.grey)
        async def quit(self, interaction: discord.Interaction,
                       button: discord.ui.Button):
            msg_id = self.msg_id
            gv = openFile('giveaways')
            if msg_id in gv:
                ticket = -int(gv[msg_id]['ticket'])
                check, check_msg = self.check_if_already_in_gv(
                    interaction.user.id, msg_id)
                if check == False:
                    await interaction.response.send_message(embed=check_msg, ephemeral=True)
                    return
                self.join_giveaway(interaction.user.id, ticket, msg_id)
                await interaction.response.send_message(embed=defaultEmbed(f'✅退出抽獎成功', f'flow幣 +{-int(ticket)}'), ephemeral=True)
                await interaction.followup.send(embed=GiveAwayCog.generate_gv_embed(self, msg_id, interaction), ephemeral=True)
                await self.update_gv_msg(msg_id)

    def is_gv_option_valid(self, gv_option: str):
        if gv_option == '目前沒有任何進行中的抽獎':
            return False, errEmbed('真的沒有抽獎', '真的')
        gv = openFile('giveaways')
        found = False
        for gv_id, val in gv.items():
            if val['prize']==gv_option:
                found = True
        if found == False:
            return False, errEmbed('該抽獎不存在!', '')
        return True, None

    async def giveaway_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        gv = openFile('giveaways')
        if not gv:
            result = ['目前沒有任何進行中的抽獎']
        else:
            result = []
            for msg_id, val in gv.items():
                result.append(val['prize'])
        return [
            app_commands.Choice(name=gv, value=gv)
            for gv in result if current.lower() in gv.lower()
        ]

    @app_commands.command(name='join', description='參加抽獎')
    @app_commands.rename(gv_option='抽獎')
    @app_commands.describe(gv_option='請選擇想要參與的抽獎')
    @app_commands.autocomplete(gv_option=giveaway_autocomplete)
    async def join_giveaway(self, i: Interaction, gv_option: str):
        print(log(False, False, 'Join Giveaway', i.user.id))
        check, check_msg = self.is_gv_option_valid(gv_option)
        if check == False:
            await i.response.send_message(embed=check_msg, ephemeral=True)
            return
        gv = openFile('giveaways')
        for msg_id, value in gv.items():
            if value['prize'] == gv_option:
                gv_msg_id = msg_id
        view = self.GiveAwayView(interaction=i, gv_msg_id=gv_msg_id)
        await i.response.send_message(embed=self.generate_gv_embed(gv_msg_id=gv_msg_id, i=i), view=view, ephemeral=True)

    @app_commands.command(name='endgiveaway', description='強制結束抽獎並選出得獎者')
    @app_commands.rename(gv_option='抽獎')
    @app_commands.describe(gv_option='請選擇想要參與的抽獎')
    @app_commands.autocomplete(gv_option=giveaway_autocomplete)
    @app_commands.checks.has_role('小雪團隊')
    async def end_giveaway(self, interaction: discord.Interaction, gv_option: str):
        print(log(False, False, 'End Giveaway', interaction.user.id))
        check, check_msg = self.is_gv_option_valid(gv_option)
        if check == False:
            await interaction.response.send_message(embed=check_msg, ephemeral=True)
        gv = openFile('giveaways')
        for msg_id, value in gv.items():
            if value['prize'] == gv_option:
                gv_msg_id = msg_id
                break
        gv[msg_id]['current'] = gv[msg_id]['goal']
        saveFile(gv, 'giveaways')
        GiveAwayCog.GiveAwayView.check_gv_finish(gv_msg_id=msg_id, i=interaction)
        await interaction.response.send_message(embed=defaultEmbed('✅強制抽獎成功', f'獎品: {gv_option}'), ephemeral=True)

    @end_giveaway.error
    async def err_handle(self, interaction: discord.Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    @end_giveaway.autocomplete('gv_option')
    async def giveaway_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        gv = openFile('giveaways')
        if not gv:
            result = ['目前沒有任何進行中的抽獎']
        else:
            result = []
            for msg_id, val in gv.items():
                result.append(val['prize'])
        return [
            app_commands.Choice(name=gv, value=gv)
            for gv in result if current.lower() in gv.lower()
        ]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GiveAwayCog(bot))
