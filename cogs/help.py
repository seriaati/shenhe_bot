from discord.ui import Select
from discord import SelectOption, app_commands, Interaction, Embed
from discord.ext import commands
from debug import DefaultView
from utility.utils import defaultEmbed


class Dropdown(Select):
    def __init__(self, bot: commands.Bot):
        options = [
            SelectOption(label='原神', description='註冊帳號即可使用',
                         emoji='🌟'),
            SelectOption(label='原神祈願(需註冊)',
                         description='需註冊+設置祈願紀錄', emoji='🌠'),
            SelectOption(label='原神計算',
                         description='計算原神角色、武器養成素材並加到代辦清單', emoji='<:CALCULATOR:999540912319369227>'),
            SelectOption(label='呼叫相關', description='呼叫群友', emoji='🔉'),
            SelectOption(label='flow系統', description='交易方式, 發布委託等',
                         emoji='🌊'),
            SelectOption(label='其他', description='其他指令', emoji='🙂'),
            SelectOption(label='語音台', description='語音台相關指令',
                         emoji='🎙️'),
            SelectOption(label='音樂系統', description='音樂系統相關指令',
                         emoji='🎵'),
            SelectOption(label='二次元圖片系統', description='香香的',
                         emoji='2️⃣'),
        ]
        super().__init__(placeholder='你想要什麼樣的幫助呢?', options=options)
        self.bot = bot

    async def callback(self, interaction: Interaction):
        cogs = ['genshin', 'wish', 'calc', 'call',
                'flow', 'other', 'vc', 'music', 'waifu']
        for index, option in enumerate(self.options):
            if option.value == self.values[0]:
                selected_option = option
                index = index
                break
        embed = defaultEmbed(
            f'{selected_option.emoji} {selected_option.label}', selected_option.description)
        commands = self.bot.get_cog(cogs[index]).__cog_app_commands__
        for command in commands:
            if len(command.checks) != 0:
                continue
            embed.add_field(
                name=f'`{command.name}`',
                value=command.description
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DropdownView(DefaultView):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.add_item(Dropdown(bot))


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def returnHelpEmbed(embed: Embed, commands: list[app_commands.Command]):
        embed = embed
        for command in commands:
            if len(command.checks) != 0:
                continue
            embed.add_field(
                name=f'`{command.name}`',
                value=command.description
            )
        return embed

    @app_commands.command(name='help幫助', description='獲得幫助')
    async def help(self, interaction: Interaction):
        view = DropdownView(self.bot)
        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
