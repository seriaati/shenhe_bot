from debug import DefaultView
from discord import ButtonStyle, Interaction, SelectOption, app_commands
from discord.ext import commands
from discord.ui import Button, Select, button, select
from discord.utils import get
from utility.utils import defaultEmbed, errEmbed


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class RoleSelection(DefaultView):
        def __init__(self):
            super().__init__(timeout=None)

        class ButtonChoices(DefaultView):
            def __init__(self, role):
                super().__init__(timeout=None)
                self.role = role

            @button(label='獲取', style=ButtonStyle.green, custom_id='get_role_button')
            async def get_role_button(self, interaction: Interaction, button: Button):
                g = interaction.client.get_guild(916838066117824553)
                r = get(g.roles, name=self.role)
                if r in interaction.user.roles:
                    await interaction.response.edit_message(embed=errEmbed('<a:error_animated:982579472060547092> 你已經擁有這個身份組了!'))
                    return
                await interaction.user.add_roles(r)
                await interaction.response.edit_message(embed=defaultEmbed(f'<a:check_animated:982579879239352370> 已獲取 {r} 身份組'))

            @button(label='撤回', style=ButtonStyle.red, custom_id='remove_role_button')
            async def discard_role_button(self, interaction: Interaction, button: Button):
                g = interaction.client.get_guild(916838066117824553)
                r = get(g.roles, name=self.role)
                if r not in interaction.user.roles:
                    await interaction.response.edit_message(embed=errEmbed('<a:error_animated:982579472060547092> 你本來就沒有這個身份組!'))
                await interaction.user.remove_roles(r)
                await interaction.response.edit_message(embed=defaultEmbed(f'<a:check_animated:982579879239352370> 已撤回 {r} 身份組'))

        def get_role_options():
            roles = ['委託通知', '抽獎通知', '活動通知', '小雪通知']
            role_list = []
            for role in roles:
                role_list.append(SelectOption(label=role))
            return role_list

        class WorldLevelView(DefaultView):
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
                        await interaction.response.send_message(embed=defaultEmbed(f'<a:check_animated:982579879239352370> 已撤回世界等級{self.number}身份組'), ephemeral=True)
                    else:
                        await interaction.user.add_roles(r)
                        await interaction.response.send_message(embed=defaultEmbed(f'<a:check_animated:982579879239352370> 已給予世界等級{self.number}身份組'), ephemeral=True)

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
            '<:resin:982423477371953172> 身份組選擇器',
            '從選單中選擇你想要的身份組吧!')
        await i.response.send_message(embed=embed, view=role_selection_view)

    @app_commands.command(name='wrrole', description='世界等級身份組')
    @app_commands.checks.has_role('小雪團隊')
    async def wr_role(self, i: Interaction):
        wr_menu = ReactionRoles.RoleSelection.WorldLevelView()
        embed = defaultEmbed(
            '選擇你的原神世界等級',
            '按按鈕會給予對應身份組, 再按一次會撤回身份組')
        await i.response.send_message(embed=embed, view=wr_menu)

    class NationalityChooser(DefaultView):
        def __init__(self, num: list):
            super().__init__(timeout=None)
            self.add_item(ReactionRoles.NationalitySelect(num))

    class NationalitySelect(Select):
        def __init__(self, num: list):
            super().__init__(placeholder='選擇國籍', custom_id='nationality_select', options=[
                SelectOption(label='兔兔島', emoji='🍡', value=0,
                             description=f'目前人數: {num[0]}'),
                SelectOption(label='小雪國', emoji='❄️', value=1,
                             description=f'目前人數: {num[1]}'),
                SelectOption(label='羽嶼', emoji='💕', value=2,
                             description=f'目前人數: {num[2]}'),
                SelectOption(label='清除國籍', emoji='🗑️', value=3)])

        async def callback(self, i: Interaction):
            roles = [
                i.guild.get_role(954684157831823361),
                i.guild.get_role(938981834883227689),
                i.guild.get_role(946992082092982314)
            ]
            for r in roles:
                if r in i.user.roles:
                    await i.user.remove_roles(r)
            await i.user.add_roles(roles[int(self.values[0])])
            view = ReactionRoles.NationalityChooser(
                [len(roles[0].members), len(roles[1].members), len(roles[2].members)])
            await i.response.edit_message(view=view)

    @app_commands.command(name='nationality', description='國籍身份組')
    @app_commands.checks.has_role('小雪團隊')
    async def nation_role(self, i: Interaction):
        embed = defaultEmbed('國籍選擇', '選好玩的而已, 按照自己的直覺/心意選一個吧! (不選也是可以的哦)')
        embed.add_field(
            name=':dango: 兔兔島',
            value='在一片迷霧之中 隱藏了一座世外桃源的島嶼\n'
            '可愛活潑的兔島主會在聊天台和語音中歡迎你的到來\n\n'
            '熱情的的兔兔島民們非常歡迎每位新朋友來到這個脫離現實的美好世界\n'
            '島民都親如家人 和睦相處 相信你也會很快融入並成為其中的一份子\n\n'
            '兔兔島除了有帶你跑圖鋤地賺取摩拉的人外\n'
            '偶然也會舉辦小小的抽獎回饋各位島民的支持和陪伴\n'
            '還不出發到這座溫馨小島嗎?兔兔島萬歲!!',
            inline=False
        )
        embed.add_field(
            name=':snowflake: 小雪國',
            value='在遠方的冰天雪地 有一個國度 可愛與純真並重的小雪女皇：小雪國\n'
            '這是一個來自充滿雪花、由小雪女皇統治的一個大型群組，而且是一個群內知名的大國\n'
            '而小雪女皇是一個純真、可愛的女孩，這裡的申鶴機器人就是又她一手研發的\n'
            '但小雪國不只是知名於這些地方，小雪女皇不時也會發放國民福利，小雪國民是享有最多福利的群眾，很吸引人吧！\n'
            '快加入！你不會後悔的，\n'
            '「小雪國萬歲喵！」',
            inline=False
        )
        embed.add_field(
            name=':two_hearts: 羽嶼',
            value='一個寧靜平凡、與世無爭的小島\n'
            '島民的性格都跟這條介紹一樣懶散隨和\n'
            '是一個如同蒙德一樣自由的小漁村\n'
            '來羽嶼釣魚賞櫻吧～',
            inline=False
        )
        roles = [
            i.guild.get_role(954684157831823361),
            i.guild.get_role(938981834883227689),
            i.guild.get_role(946992082092982314)
        ]
        view = ReactionRoles.NationalityChooser(
            [len(roles[0].members), len(roles[1].members), len(roles[2].members)])
        await i.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRoles(bot))
