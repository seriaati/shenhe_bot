from discord import ButtonStyle, Interaction, SelectOption, app_commands
from discord.ext import commands
from discord.ui import Button, Select, View, button, select
from discord.utils import get
from utility.utils import defaultEmbed, errEmbed


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class RoleSelection(View):
        def __init__(self):
            super().__init__(timeout=None)

        class ButtonChoices(View):
            def __init__(self, role):
                super().__init__(timeout=None)
                self.role = role

            @button(label='獲取', style=ButtonStyle.green, custom_id='get_role_button')
            async def get_role_button(self, interaction: Interaction, button: Button):
                g = interaction.client.get_guild(916838066117824553)
                r = get(g.roles, name=self.role)
                if r in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed('你已經擁有這個身份組了!', ''), ephemeral=True)
                    return
                await interaction.user.add_roles(r)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ 已獲取 {r} 身份組', ''), ephemeral=True)

            @button(label='撤回', style=ButtonStyle.red, custom_id='remove_role_button')
            async def discard_role_button(self, interaction: Interaction, button: Button):
                g = interaction.client.get_guild(916838066117824553)
                r = get(g.roles, name=self.role)
                if r not in interaction.user.roles:
                    await interaction.response.send_message(embed=errEmbed('你本來就沒有這個身份組!', ''), ephemeral=True)
                await interaction.user.remove_roles(r)
                await interaction.response.send_message(embed=defaultEmbed(f'✅ 已撤回 {r} 身份組', ''), ephemeral=True)

        def get_role_options():
            roles = ['委託通知', '抽獎通知', '活動通知', '小雪通知']
            role_list = []
            for role in roles:
                role_list.append(SelectOption(label=role))
            return role_list

        class WorldLevelView(View):
            def __init__(self):
                super().__init__(timeout=None)
                for x in range(1, 9):
                    y = 0 if x <= 4 else 1
                    self.add_item(self.WorldLevelButton(x, y))

            class WorldLevelButton(Button):
                def __init__(self, number: int, row: int):
                    super().__init__(style=ButtonStyle.blurple, label=number,
                                     row=row, custom_id=f'world_level_button_{number}')
                    self.number = number

                async def callback(self, interaction: Interaction):
                    g = interaction.client.get_guild(916838066117824553)
                    r = get(g.roles, name=f'W{self.number}')
                    if r in interaction.user.roles:
                        await interaction.user.remove_roles(r)
                        await interaction.response.send_message(embed=defaultEmbed(f'✅ 已撤回世界等級{self.number}身份組', ''), ephemeral=True)
                    else:
                        await interaction.user.add_roles(r)
                        await interaction.response.send_message(embed=defaultEmbed(f'✅ 已給予世界等級{self.number}身份組', ''), ephemeral=True)

        @select(options=get_role_options(), placeholder='請選擇身份組', min_values=1, max_values=1, custom_id='role_selection_select')
        async def role_chooser(self, interaction: Interaction, select: Select):
            choice = select.values[0]
            action_menu = self.ButtonChoices(choice)
            embed = defaultEmbed(
                f'你選擇了 {select.values[0]} 身份組', '要獲取還是撤回該身份組?')
            await interaction.response.send_message(embed=embed, view=action_menu, ephemeral=True)

    @app_commands.command(name='role', description='取得身份組')
    @app_commands.checks.has_role('小雪團隊')
    async def get_role(self, i: Interaction):
        role_selection_view = ReactionRoles.RoleSelection()
        embed = defaultEmbed(
            '⭐ 身份組選擇器',
            '從選單中選擇你想要的身份組吧!'
        )
        await i.response.send_message(embed=embed, view=role_selection_view)

    @get_role.error
    async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            channel = self.bot.get_channel(962311051683192842)
            await interaction.response.send_message(f'請至 {channel.mention} 獲取身份組哦', ephemeral=True)

    @app_commands.command(name='wrrole', description='世界等級身份組')
    @app_commands.checks.has_role('小雪團隊')
    async def wr_role(self, i: Interaction):
        wr_menu = ReactionRoles.RoleSelection.WorldLevelView()
        embed = defaultEmbed(
            '選擇你的原神世界等級',
            '按按鈕會給予對應身份組, 再按一次會撤回身份組')
        await i.response.send_message(embed=embed, view=wr_menu)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
