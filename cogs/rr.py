import re
import discord
from discord import Interaction, app_commands
from discord.ext import commands
from utility.utils import defaultEmbed, errEmbed, log


class ReactionRoles(commands.Cog, name='rr', description='表情符號身份組產生器'):
    def __init__(self, bot):
        self.bot = bot

    class RoleSelection(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        class ButtonChoices(discord.ui.View):
            def __init__(self, role):
                super().__init__(timeout=None)
                self.role = role

            @discord.ui.button(label='獲取', style=discord.ButtonStyle.green)
            async def get_role_button(self, interaction: Interaction, button: discord.ui.Button):
                g = interaction.client.get_guild(916838066117824553)
                r = discord.utils.get(g.roles, name=self.role)
                if r in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed('你已經擁有這個身份組了!', ''), ephemeral=True)
                    return
                await interaction.user.add_roles(r)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ 已獲取 {r} 身份組', ''), ephemeral=True)

            @discord.ui.button(label='撤回', style=discord.ButtonStyle.red)
            async def discard_role_button(self, interaction: Interaction, button: discord.ui.Button):
                g = interaction.client.get_guild(916838066117824553)
                r = discord.utils.get(g.roles, name=self.role)
                if r not in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed('你本來就沒有這個身份組!', ''), ephemeral=True)
                await interaction.user.remove_roles(r)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ 已撤回 {r} 身份組', ''), ephemeral=True)

        def get_role_options():
            roles = ['原神世界等級', '委託通知', '抽獎通知', '活動通知', '小雪通知']
            role_list = []
            for role in roles:
                role_list.append(discord.SelectOption(label=role))
            return role_list

        class WorldLevelView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                for x in range(1, 9):
                    y = 0 if x <= 4 else 1
                    self.add_item(self.WorldLevelButton(x, y))

            class WorldLevelButton(discord.ui.Button):
                def __init__(self, number: int, row: int):
                    super().__init__(style=discord.ButtonStyle.blurple, label=number, row=row)
                    self.number = number

                async def callback(self, interaction: Interaction):
                    g = interaction.client.get_guild(916838066117824553)
                    user_wr_role = 0
                    wr_role_list = []
                    for i in range(1, 9):
                        role = discord.utils.get(g.roles, name=f'W{i}')
                        wr_role_list.append(role)
                    print(wr_role_list)
                    for role in wr_role_list:
                        if role in interaction.user.roles:
                            user_wr_role = re.findall(r'\d+', str(role.name))
                            print(user_wr_role)
                            break
                    if user_wr_role != 0 and self.number != user_wr_role[0]:
                        await interaction.response.send_message(embed=errEmbed('同時最多只能擁有一個世界等級身份組',''), ephemeral=True)
                        return
                    r = discord.utils.get(g.roles, name=f'W{self.number}')
                    if r in interaction.user.roles:
                        await interaction.user.remove_roles(r)
                        await interaction.response.send_message(embed=defaultEmbed(f'✅ 已撤回世界等級{self.number}身份組', ''), ephemeral=True)
                    else:
                        await interaction.user.add_roles(r)
                        await interaction.response.send_message(embed=defaultEmbed(f'✅ 已給予世界等級{self.number}身份組', ''), ephemeral=True)

        @discord.ui.select(options=get_role_options(), placeholder='請選擇身份組', min_values=1, max_values=1)
        async def role_chooser(self, interaction: Interaction, select: discord.ui.Select):
            choice = select.values[0]
            action_menu = self.ButtonChoices(choice)
            wr_menu = self.WorldLevelView()
            if select.values[0] == '原神世界等級':
                embed = defaultEmbed('選擇你的原神世界等級', '按按鈕會給予對應身份組, 再按一次會撤回身份組')
                await interaction.response.send_message(view=wr_menu, ephemeral=True)
            else:
                await interaction.response.send_message(view=action_menu, ephemeral=True)

    @app_commands.command(name='role', description='取得身份組')
    async def get_role(self, i: Interaction):
        print(log(False, False, 'Role', i.user.id))
        role_selection_view = self.RoleSelection()
        await i.response.send_message(view=role_selection_view, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
