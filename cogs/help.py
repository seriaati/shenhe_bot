import typing
import discord
from discord.ext import commands
from discord import app_commands

from utility.utils import defaultEmbed

class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='原神資料', description='需先註冊帳號後方可使用', emoji='✨'),
            discord.SelectOption(label='原神', description='不須註冊帳號即可使用', emoji='🌟'),
            discord.SelectOption(label='呼叫相關', description='呼叫!', emoji='🔉'),
            discord.SelectOption(label='flow系統', description='交易方式, 發布委託等', emoji='🌊'),
            discord.SelectOption(label='其他', description='其他指令', emoji='🙂'),
        ]
        super().__init__(placeholder='你想要什麼樣的幫助呢?', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == '原神資料':
            embed = defaultEmbed(
                '原神資料相關',
                '需要使用/cookie來設定帳號'
            )
            embed.add_field(
                name='`/cookie`',
                value='設定原神帳號'
            )
            embed.add_field(
                name='`/setuid`',
                value='設置原神UID'
            )
            embed.add_field(
                name='`/check`',
                value='查看即時便籤'
            )
            embed.add_field(
                name='`/stats`',
                value=''
            )
        elif self.values[0] == '原神':
            embed = defaultEmbed(
                '原神相關',
                ''
            )
        elif self.values[0] == '呼叫相關':
            embed = defaultEmbed(
                '呼叫相關',
                ''
            )
        elif self.values[0] == 'flow系統':
            embed = defaultEmbed(
                'flow系統相關',
                ''
            )
        elif self.values[0] == '其他':  
            embed = defaultEmbed(
                '其他指令',
                ''
            )
        await interaction.response.send_message(embed=embed) 

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help',description='獲得幫助')
    async def help(self, interaction:discord.Interaction):
        view = DropdownView()
        await interaction.response.send_message(view=view)
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))