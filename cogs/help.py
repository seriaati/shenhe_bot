import discord
from discord.ext import commands
from discord import app_commands

from utility.utils import defaultEmbed, log

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
                value='設定原神帳號',
                inline=False
            )
            embed.add_field(
                name='`/setuid`',
                value='設置原神UID',
                inline=False
            )
            embed.add_field(
                name='`/check`',
                value='查看即時便籤, 例如樹脂、洞天寶錢、探索派遣',
                inline=False
            )
            embed.add_field(
                name='`/stats`',
                value='查看原神資料, 如活躍時間、神瞳數量、寶箱數量',
                inline=False
            )
            embed.add_field(
                name='`/area`',
                value='查看區域探索度',
                inline=False
            )
            embed.add_field(
                name='`/claim`',
                value='領取hoyolab登入獎勵',
                inline=False
            )
            embed.add_field(
                name='`/diary`',
                value='查看旅行者日記',
                inline=False
            )
            embed.add_field(
                name='`/log`',
                value='查看最近25筆原石或摩拉收入紀錄',
                inline=False
            )
            embed.add_field(
                name='`/users`',
                value='查看所有已註冊原神帳號',
                inline=False
            )
            embed.add_field(
                name='`/today`',
                value='查看今日原石與摩拉收入',
                inline=False
            )
            embed.add_field(
                name='`/abyss`',
                value='查看深境螺旋資料',
                inline=False
            )
            embed.add_field(
                name='`/char`',
                value='查看已擁有角色資訊',
                inline=False
            )
            embed.add_field(
                name='`/schedule`',
                value='設置自動化功能',
                inline=False
            )
            embed.add_field(
                name='`/setkey`',
                value='設置祈願紀錄',
                inline=False
            )
            embed.add_field(
                name='`/wish`',
                value='查看祈願紀錄',
                inline=False 
            )
            embed.add_field(
                name='/wishanalysis',
                value='祈願資料分析',
                inline=False
            )
        elif self.values[0] == '原神':
            embed = defaultEmbed(
                '原神相關',
                ''
            )
            embed.add_field(
                name='`/farm`',
                value='查看原神今日可刷素材',
                inline=False
            )
            embed.add_field(
                name='`/build`',
                value='查看角色推薦主詞條、畢業面板、不同配置等',
                inline=False
            )
            embed.add_field(
                name='`/rate`',
                value='(僅供參考用)非常不穩定的聖遺物評分器',
                inline=False
            )

        elif self.values[0] == '呼叫相關':
            embed = defaultEmbed(
                '呼叫相關',
                ''
            )
            embed.add_field(
                name='`/call`',
                value='呼叫群裡的某個人',
                inline=False
            )
            embed.add_field(
                name='`/snow`',
                value='小雪國萬歲!',
                inline=False
            )
        elif self.values[0] == 'flow系統':
            embed = defaultEmbed(
                'flow系統相關',
                ''
            )
            embed.add_field(
                name='`/acc`',
                value='查看flow帳戶',
                inline=False
            )
            embed.add_field(
                name='`/give`',
                value='給其他人flow幣',
                inline=False
            )
            embed.add_field(
                name='`/total`',
                value='查看目前群組帳號及銀行flow幣分配情況',
                inline=False
            )
            embed.add_field(
                name='`/flows`',
                value='查看群組內所有flow帳號',
                inline=False
            )
            embed.add_field(
                name='`/find`',
                value='發布委託',
                inline=False
            )
            embed.add_field(
                name='`/roll`',
                value='flow抽卡系統',
                inline=False
            )

        elif self.values[0] == '其他':  
            embed = defaultEmbed(
                '其他指令',
                ''
            )
            embed.add_field(
                name='`/ping`',
                value='查看機器人目前延遲',
                inline=False
            )
            embed.add_field(
                name='`/cute`',
                value='讓申鶴說某個人很可愛',
                inline=False
            )
            embed.add_field(
                name='`/flash`',
                value='防放閃機制',
                inline=False
            )
            embed.add_field(
                name='`/number`',
                value='讓申鶴從兩個數字間挑一個隨機的給你',
                inline=False
            )
            embed.add_field(
                name='`/marry`',
                value='結婚 💞',
                inline=False
            )
            embed.add_field(
                name='`!q`',
                value='語錄他人',
                inline=False
            )
            embed.add_field(
                name='`/members`',
                value='查看群組總人數',
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True) 

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help',description='獲得幫助')
    async def help(self, interaction:discord.Interaction):
        print(log(False, False, 'Help', interaction.user.id))
        view = DropdownView()
        await interaction.response.send_message(view=view, ephemeral=True)
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))