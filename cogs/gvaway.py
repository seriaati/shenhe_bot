import random
from typing import List, Optional
import discord
from discord import SelectOption
from discord.ext import commands
from discord import Interaction, Role, app_commands
from discord.app_commands import Choice
from discord.ui import Select, View
from utility.FlowApp import flow_app
from utility.utils import defaultEmbed, errEmbed, log, openFile, saveFile


class GiveAwayCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

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
    async def create_giveaway(
            self, interaction: Interaction,
            prize: str, goal: int, ticket: int, role: Optional[Role] = None, refund_mode: int = 1):
        print(log(False, False, 'giveaway',
              f'{interaction.user.id}: (prize={prize}, goal={goal}, ticket={ticket}, role={role}, refund_mode={refund_mode})'))
        # channel = interaction.client.get_channel(965517075508498452)  # 抽獎台
        channel = interaction.client.get_channel(909595117952856084)  # 測試抽獎台
        role = role or interaction.guild.get_role(967035645610573834)
        role_exclusive = f'此抽獎專屬於: {role.mention}成員' if role is not None else '任何人都可以參加這個抽獎'
        refund_state = '(會退款)' if refund_mode == 0 else '(不會退款)'
        giveaway_view = GiveAwayCog.GiveAwayView(interaction)
        await interaction.response.send_message(embed=defaultEmbed(
            ":tada: 抽獎啦!!!",
            f"獎品: {prize}\n"
            f"目前flow幣: 0/{goal}\n"
            f"參加抽獎要付的flow幣: {ticket}\n"
            f"{role_exclusive}\n"
            f'{refund_state}'), view=giveaway_view)
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

    # @create_giveaway.error
    # async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
    #     if isinstance(e, app_commands.errors.MissingRole):
    #         await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)

    class GiveAwayView(View):
        def __init__(self, interaction: Interaction = None):
            super().__init__(timeout=None)
            self.interaction = interaction

        def generate_gv_embed(self, gv_msg_id: int, interaction: Interaction):
            gv = openFile('giveaways')
            role = interaction.guild.get_role(gv[gv_msg_id]['role'])
            role_exclusive = f'此抽獎專屬於: {role.mention}成員' if role is not None else '任何人都可以參加這個抽獎'
            refund_state = '(會退款)' if gv[gv_msg_id]['refund_mode'] == True else '(不會退款)'
            embed = defaultEmbed(
                ":tada: 抽獎啦!!!",
                f"獎品: {gv[gv_msg_id]['prize']}\n"
                f"目前flow幣: {gv[gv_msg_id]['current']}/{gv[gv_msg_id]['goal']}\n"
                f"參加抽獎要付的flow幣: {gv[gv_msg_id]['ticket']}\n"
                f"{role_exclusive}\n"
                f'{refund_state}')
            return embed

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

        async def update_gv_msg(self, input_gv_msg_id: int, interaction: Interaction):
            # channel = interaction.client.get_channel(965517075508498452)  # 抽獎台
            channel = interaction.client.get_channel(
                909595117952856084)  # 測試抽獎台
            gv_msg = await channel.fetch_message(input_gv_msg_id)
            await gv_msg.edit(embed=GiveAwayCog.GiveAwayView.generate_gv_embed(self, input_gv_msg_id, interaction))

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
                if gv[gv_msg_id]['refund_mode'] == True:  # 進行退款
                    for user_id in gv[gv_msg_id]['members']:
                        if winner_id != user_id:  # 如果該ID不是得獎者
                            flow_app.transaction(user_id, int(
                                gv[gv_msg_id]['ticket'])/2)  # 退款入場費/2
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

        @discord.ui.button(label='參加抽獎', style=discord.ButtonStyle.green, custom_id='join_give_away_button')
        async def join_giveaway_callback(self, interaction: Interaction, button: discord.ui.Button):
            msg = interaction.message
            check, check_msg = flow_app.checkFlowAccount(interaction.user.id)
            if check == False:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            gv = openFile('giveaways')
            ticket = gv[msg.id]['ticket']
            check, check_msg = self.ticket_flow_check(
                interaction.user.id, ticket)
            if check == False:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            check, check_msg = self.check_if_already_in_gv(
                interaction.user.id, msg.id)
            if check == True:
                await interaction.response.send_message(embed=check_msg, ephemeral=True)
                return
            if msg.id in gv:
                r = interaction.guild.get_role(gv[msg.id]['role'])
                if r is not None and r not in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed(
                        '非常抱歉', f'你不是{r.mention}的一員, 不能參加這個抽獎'), ephemeral=True)
                    return
                self.join_giveaway(interaction.user.id, ticket, msg.id)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ 參加抽獎成功', f'你的flow幣 -{ticket}'), ephemeral=True)
                await self.update_gv_msg(msg.id, interaction)
                await self.check_gv_finish(gv_msg_id=msg.id, i=interaction)
            else:
                await interaction.response.send_message(embed=errEmbed('該抽獎不存在!', '(因為某些不明原因)'))

        @discord.ui.button(label='退出抽獎', style=discord.ButtonStyle.grey, custom_id='leave_giveaway_button')
        async def leave_giveaway_callback(self, interaction: Interaction, button: discord.ui.Button):
            msg = interaction.message
            gv = openFile('giveaways')
            if msg.id in gv:
                ticket = -int(gv[msg.id]['ticket'])
                check, check_msg = self.check_if_already_in_gv(
                    interaction.user.id, msg.id)
                if check == False:
                    await interaction.response.send_message(embed=check_msg, ephemeral=True)
                    return
                self.join_giveaway(interaction.user.id, ticket, msg.id)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ 退出抽獎成功', f'你的flow幣 +{-int(ticket)}'), ephemeral=True)
                await self.update_gv_msg(msg.id, interaction)

    def is_gv_option_valid(self, gv_option: str):
        if gv_option == '目前沒有任何進行中的抽獎':
            return False, errEmbed('真的沒有抽獎', '真的')
        gv = openFile('giveaways')
        found = False
        for gv_id, val in gv.items():
            if val['prize'] == gv_option:
                found = True
        if found == False:
            return False, errEmbed('該抽獎不存在!', '')
        return True, None

    async def giveaway_autocomplete(self, interaction: Interaction, current: str) -> List[app_commands.Choice[str]]:
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

    class GiveawayDropdown(Select):
        def __init__(self, gv_dict: dict):
            options = []
            if not bool(gv_dict):
                super().__init__(placeholder='目前沒有進行中的抽獎', min_values=1, max_values=1,
                                 options=[SelectOption(label='disabled')], disabled=True)
            else:
                for msg_id, val in gv_dict.items():
                    options.append(SelectOption(
                        label=val['prize'], value=msg_id))
                super().__init__(placeholder='選擇要結束的抽獎', min_values=1, max_values=1, options=options)

        async def callback(self, i: Interaction):
            print(log(False, False, 'End Giveaway',
                  f'{i.user.id}: (gv_msg_id = {self.values[0]})'))
            gv = openFile('giveaways')
            gv_msg_id = int(self.values[0])
            gv[gv_msg_id]['current'] = gv[gv_msg_id]['goal']
            saveFile(gv, 'giveaways')
            await GiveAwayCog.GiveAwayView.check_gv_finish(self, gv_msg_id=gv_msg_id, i=i)
            await i.response.send_message(embed=defaultEmbed('✅ 強制抽獎成功'), ephemeral=True)

    class GiveawayDropdownView(View):
        def __init__(self, gv_dict: dict):
            super().__init__(timeout=None)
            self.add_item(GiveAwayCog.GiveawayDropdown(gv_dict))

    @app_commands.command(name='endgiveaway', description='強制結束抽獎並選出得獎者')
    @app_commands.checks.has_role('小雪團隊')
    async def end_giveaway(self, interaction: Interaction):
        gv = openFile('giveaways')
        view = self.GiveawayDropdownView(gv)
        await interaction.response.send_message(view=view, ephemeral=True)

    @end_giveaway.error
    async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GiveAwayCog(bot))
