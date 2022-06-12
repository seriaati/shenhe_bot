from discord.ui import Select
from discord import SelectOption, app_commands, Interaction
from discord.ext import commands
from debug import DefaultView
from utility.utils import defaultEmbed


class Dropdown(Select):
    def __init__(self):
        options = [
            SelectOption(label='原神資料', description='需先/cookie註冊帳號後方可使用', emoji='✨'),
            SelectOption(label='原神', description='不須註冊帳號即可使用', emoji='🌟'),
            SelectOption(label='原神祈願', description='需註冊+設置祈願紀錄', emoji='🌠'),
            SelectOption(label='呼叫相關', description='呼叫群友', emoji='🔉'),
            SelectOption(label='flow系統', description='交易方式, 發布委託等', emoji='🌊'),
            SelectOption(label='其他', description='其他指令', emoji='🙂'),
            SelectOption(label='語音台', description='語音台相關指令', emoji='🎙️'),
            SelectOption(label='音樂系統', description='音樂系統相關指令', emoji='🎵'),
        ]
        super().__init__(placeholder='你想要什麼樣的幫助呢?',
                         min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
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
                name='`/calc character`',
                value='計算一個自己而擁有的角色所需養成素材',
                inline=False
            )
            embed.add_field(
                name='`/remind`',
                value='設置樹脂提醒功能',
                inline=False
            )
            embed.add_field(
                name='`/redeem`',
                value='兌換禮物碼',
                inline=False
            )
        elif self.values[0] == '原神':
            embed = defaultEmbed('原神相關','不須註冊即可使用')
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
                name='`/calc notown`',
                value='計算一個自己不擁有的角色所需養成素材',
                inline=False
            )
            embed.add_field(
                name='`/oculi`',
                value='查看不同地區的神瞳位置',
                inline=False
            )
            embed.add_field(
                name='`/profile`',
                value='透過 enka API 查看各式原神數據',
                inline=False
            )

        elif self.values[0] == '原神祈願':
            embed = defaultEmbed(
                '原神祈願',
                '需要使用`/cookie`設定帳號\n加上`/wish setkey`設定紀錄')
            embed.add_field(
                name='`/wish setkey`',
                value='設置祈願紀錄',
                inline=False
            )
            embed.add_field(
                name='`/wish history`',
                value='查看詳細祈願紀錄',
                inline=False
            )
            embed.add_field(
                name='`/wish luck`',
                value='根據祈願紀錄分析歐氣值',
                inline=False
            )
            embed.add_field(
                name='`/wish weapon`',
                value='預測抽到想要的UP武器的機率',
                inline=False
            )
            embed.add_field(
                name='`/wish character`',
                value='預測抽到想要UP角色的機率',
                inline=False
            )
            embed.add_field(
                name='`/wish overview`',
                value='查看祈願紀錄總覽',
                inline=False
            )

        elif self.values[0] == '呼叫相關':
            embed = defaultEmbed('呼叫相關')
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
            embed.add_field(
                name='`/rabbit`',
                value='兔兔島萬歲!',
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
                value='flow祈願系統',
                inline=False
            )

        elif self.values[0] == '其他':
            embed = defaultEmbed(
                '其他指令',
                ''
            )
            embed.add_field(
                name='`/help`',
                value='獲得幫助',
                inline=False
            )
            embed.add_field(
                name='`/tutorial`',
                value='群組系統教學',
                inline=False
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
            embed.add_field(
                name='`/rolemembers`',
                value='查看身份組總人數',
                inline=False
            )
            embed.add_field(
                name='`/say`',
                value='讓申鶴幫你說話',
                inline=False
            )
        elif self.values[0] == '語音台':
            embed = defaultEmbed('語音台指令')
            embed.add_field(
                name='/vc rename',
                value='重新命名語音台',
                inline=False
            )
            embed.add_field(
                name='/vc lock',
                value='鎖上語音台',
                inline=False
            )
            embed.add_field(
                name='/vc unlock',
                value='解鎖語音台',
                inline=False
            )
            embed.add_field(
                name='/vc transfer',
                value='移交房主權',
                inline=False
            )
        elif self.values[0] == '音樂系統':
            embed = defaultEmbed('音樂系統指令')
            embed.add_field(
                name='/play',
                value='播放音樂',
                inline=False
            )
            embed.add_field(
                name='/stop',
                value='停止播放器並清除待播放清單',
                inline=False
            )
            embed.add_field(
                name='/pause',
                value='暫停播放器',
                inline=False
            )
            embed.add_field(
                name='/resume',
                value='取消暫停',
                inline=False
            )
            embed.add_field(
                name='/disconnect',
                value='讓申鶴悄悄的離開目前所在的語音台',
                inline=False
            )
            embed.add_field(
                name='/player',
                value='查看目前播放狀況',
                inline=False
            )
            embed.add_field(
                name='/queue',
                value='查看目前待播放清單',
                inline=False
            )
            embed.add_field(
                name='/skip',
                value='跳過目前正在播放的歌曲',
                inline=False
            )
            embed.add_field(
                name='/clear',
                value='清除目前的待播放清單',
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class DropdownView(DefaultView):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='help', description='獲得幫助')
    async def help(self, interaction: Interaction):
        view = DropdownView()
        await interaction.response.send_message(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
