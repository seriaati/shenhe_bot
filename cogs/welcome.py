import random
import re

import aiosqlite
from discord import ButtonStyle, Interaction, Member, Message, app_commands
from discord.ext import commands
from discord.ui import Button, View, button
from utility.FlowApp import FlowApp
from utility.GenshinApp import GenshinApp
from utility.TutorialPaginator import TutorialPaginator
from utility.utils import defaultEmbed, log


class WelcomeCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: commands.Bot = bot
        self.flow_app = FlowApp(self.bot.db, self.bot)
        self.genshin_app = GenshinApp(self.bot.db, self.bot)

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        uid_channel_id = 978871680019628032 if not self.bot.debug_toggle else 909595117952856084
        if message.author.id == self.bot.user.id:
            return
        if message.channel.id == uid_channel_id:
            num = re.findall(r'\d+', str(message.content))
            if len(num) == 0:
                return
            uid = int(num[0])
            result, success = await self.genshin_app.setUID(message.author.id, uid)
            result.set_author(name=message.author,
                              icon_url=message.author.avatar)
            if not success:
                await message.channel.send(content=message.author.mention, embed=result, delete_after=5)
            else:
                await message.channel.send(content=message.author.mention, embed=result)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        await self.bot.log.send(log(True, False, 'On Member Join', member.id))
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('INSERT INTO guild_members (user_id) VALUES (?)', (member.id,))

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        await self.bot.log.send(log(True, False, 'On Member Remove', member.id))
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT flow FROM flow_accounts WHERE user_id = ?', (member.id,))
        result = await c.fetchone()
        if result is not None:
            flow = await self.flow_app.get_user_flow(member.id)
            await self.flow_app.transaction(member.id, flow, is_removing_account=True)

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if self.bot.debug_toggle:
            return
        r = before.guild.get_role(978532779098796042)
        if r not in before.roles and r in after.roles:
            await self.bot.log.send(log(True, False, 'New Traveler', after.id))
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            try:
                await c.execute('INSERT INTO flow_accounts (user_id) VALUES (?)', (after.id,))
            except:
                await self.bot.log.send(log(True, True, 'New Traveler', f'{after.id} already in flow_accounts'))
            await c.execute('SELECT * FROM guild_members WHERE user_id = ?', (after.id,))
            result = await c.fetchone()
            if result is None:
                await self.flow_app.register(after.id)
            public = self.bot.get_channel(916951131022843964)
            view = WelcomeCog.Welcome(after)
            welcome_strs = ['祝你保底不歪十連雙黃',
                            '祝你10連全武器 <:ehe:956180671620055050> <:ehe:956180671620055050>',
                            '希望你喜歡並享受這裡充滿歡笑和||變態||的氣氛',
                            '我們群中都是喜歡玩原神的||大課長||玩家!',
                            '歡迎你成為我們的一份子||(扣上鐵鏈)||',
                            '刻晴賽高!', '要好好跟大家相處唷~',
                            '你也是偽裝成萌新的大佬嗎?',
                            '七七喜歡你~',
                            '介紹一下兩位台主，<@224441463897849856> 叔叔和 <@272394461646946304> 哥哥 <:omg2:969823532420845668>']
            welcome_str = random.choice(welcome_strs)
            embed = defaultEmbed(
                f'歡迎 {after.name} !', f'歡迎來到緣神有你(๑•̀ω•́)ノ\n {welcome_str}')
            embed.set_thumbnail(url=after.avatar)
            await public.send(content=after.mention, embed=embed, view=view)

    class Welcome(View):
        def __init__(self, member: Member):
            self.member = member
            super().__init__(timeout=None)

        @button(label='歡迎~', style=ButtonStyle.blurple, custom_id='welcome_button')
        async def welcome(self, i: Interaction, button: Button):
            image_urls = [
                'https://media.discordapp.net/attachments/936772657536446535/978537906538954782/mhQ174-icc4ZdT1kSdw-dw.gif',
                'https://media.discordapp.net/attachments/630553822036623370/946061268828192829/don_genshin220223.gif',
                'https://media.discordapp.net/attachments/813430632347598882/821418716243427419/d6bf3d80f1151c55.gif',
                'https://media.discordapp.net/attachments/630553822036623370/811578439852228618/kq_genshin210217.gif',
                'https://media.discordapp.net/attachments/630553822036623370/810819929187155968/kq.gif',
                'https://media.discordapp.net/attachments/630553822036623370/865978275125264414/ayk_genshin210717.gif',
                'https://media.discordapp.net/attachments/630553822036623370/890615080381730836/kkm_genshin210923.gif',
                'https://media.discordapp.net/attachments/630553822036623370/840964488362590208/qq_genshin210509.gif',
                'https://media.discordapp.net/attachments/630553822036623370/920326390329516122/rid_genshin211214.gif',
                'https://media.discordapp.net/attachments/630553822036623370/866703863276240926/rdsg_genshin210719.gif']
            image_url = random.choice(image_urls)
            embed = defaultEmbed(
                f'{self.member.name} 歡迎歡迎~', '<:penguin_hug:978250194779000892>')
            embed.set_thumbnail(url=image_url)
            embed.set_author(name=i.user.name, icon_url=i.user.avatar)
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
            uid = await c.fetchone()
            if uid is not None:
                await i.response.send_message(embed=defaultEmbed('你已經做過入群導引啦', '不需要再做囉'), ephemeral=True)
                return
            await i.response.send_message(embed=embed)

    class AcceptRules(View):
        def __init__(self, db: aiosqlite.Connection):
            self.db = db
            super().__init__(timeout=None)

        @button(label='同意以上規則並開始入群導引', style=ButtonStyle.green, custom_id='accept_rule_button')
        async def accept_rules(self, i: Interaction, button: Button):
            embed = defaultEmbed(
                '入群導引',
                '申鶴將會快速的帶領你了解群內的主要系統\n'
                '請有耐心的做完唷~ <:penguin_hug:978250194779000892>'
            )
            view = WelcomeCog.StartTutorial(self.db)
            await i.response.send_message(embed=embed, view=view, ephemeral=True)

    class StartTutorial(View):
        def __init__(self, db: aiosqlite.Connection):
            self.db = db
            super().__init__(timeout=None)

        @button(label='開始!', style=ButtonStyle.blurple, custom_id='start_tutorial_button')
        async def start_tutorial(self, i: Interaction, button: Button):
            embeds = []
            uid_channel = i.client.get_channel(978871680019628032)
            embed = defaultEmbed(
                '原神系統',
                '先從輸入你的原神 UID 開始吧!\n'
                f'請至 {uid_channel.mention} 輸入你的原神 UID'
            )
            embeds.append(embed)
            factory = i.client.get_channel(957268464928718918)
            embed = defaultEmbed(
                '原神系統',
                '申鶴有許多原神相關的方便功能\n'
                '`/farm` 今天能刷的原神素材\n'
                '`/build` 不同角色的配置方式\n'
                '`/check` 目前樹脂\n'
                '`/abyss` 深淵數據\n'
                '`/today` 今天獲得的原石及摩拉數量\n'
                '`/remind` 樹脂溢出提醒\n'
                f'有興趣的話, 可以至 {factory.mention} 使用`/cookie`設置帳號'
            )
            embeds.append(embed)
            embed = defaultEmbed(
                'flow幣系統',
                '本群擁有專屬的經濟系統\n'
                '可以幫助你獲得免費原神月卡等好物\n'
                '有興趣的話\n'
                f'可以至使用`/tutorial`指令'
            )
            embeds.append(embed)
            role = i.client.get_channel(962311051683192842)
            embed = defaultEmbed(
                '身份組',
                f'請至 {role.mention} 領取原神等級身份組\n'
                '向上滑可以看到國籍身份組領取器\n'
                '國籍身份組是選好玩的\n'
                '按照自己內心的直覺選一個吧! (不選也可以哦)'
            )
            embeds.append(embed)
            embed = defaultEmbed(
                '還有更多...',
                '以上只是申鶴的一小部份而已!\n'
                '想要查看所有的指令請打`/help`\n'
                f'有問題歡迎至 {factory.mention} 詢問我(<@410036441129943050>)或 <@831883841417248778>)'
            )
            embeds.append(embed)
            embed = defaultEmbed(
                '祝你好運!',
                '以上就是入群導引\n'
                '歡迎加入「緣神有你」!\n'
                '在這裡好好享受歡樂的時光吧!'
            )
            embeds.append(embed)
            await TutorialPaginator(i, embeds).start(db=self.db, embeded=True)

    @app_commands.command(name='tutorial', description='進行flow幣系統教學')
    async def flow_tutorial(self, i: Interaction):
        embeds = []
        embed = defaultEmbed(
            'flow幣系統',
            '這是群內專屬的經濟系統\n'
            '在你入群的時候, 系統已經幫你創建一個帳號\n'
            '並贈送了 20 flow幣給你\n'
            '輸入`/acc`來看看你的 **flow帳號** 吧!'
        )
        embeds.append(embed)
        gv = i.client.get_channel(965517075508498452)
        role = i.client.get_channel(962311051683192842)
        embed = defaultEmbed(
            '抽獎系統',
            f'抽獎都會在 {gv.mention} 進行\n'
            '抽獎需要支付 flow幣來參與\n'
            f'可以到 {role.mention} 領取 **抽獎通知** 身份組'
        )
        c = i.client.get_channel(960861105503232030)
        embeds.append(embed)
        embed = defaultEmbed(
            '委託系統',
            f'萌新:歡迎到 {c.mention} 使用`/find`指令來發布委託\n'
            f'大佬:可以到 {role.mention} 領取 **委託通知** 身份組\n\n'
            '可以免費發布委託, 也可以花費 **flow幣 **發布\n'
            '接取委託有機會獲得 **flow幣** (取決於發布人)'
        )
        embeds.append(embed)
        flow_c = i.client.get_channel(966621141949120532)
        embed = defaultEmbed(
            'flow幣活動',
            '每週都會有不同的活動來取得flow幣\n'
            '包括討伐挑戰, 拍照等等...盡量符合不同玩家的風格\n'
            f'有興趣請往 {flow_c.mention}'
        )
        embeds.append(embed)
        embed = defaultEmbed(
            '祈願系統',
            '我們在 discord 中複製了原神的祈願玩法\n'
            '可以使用`/roll`指令來開啟祈願界面(不要直接在這裡用哦)\n'
            '有機率抽中不同物品, 取決於當期獎品'
        )
        embeds.append(embed)
        embed = defaultEmbed(
            '商店系統',
            '賺到的 **flow幣** 可以在商店進行消費\n'
            '輸入`/shop show`來看看吧\n'
            '當你賺到足夠的錢後, 可以用`/shop buy`來購買商品'
        )
        embeds.append(embed)
        await TutorialPaginator(i, embeds).start(db=self.bot.db, embeded=True)

    @app_commands.command(name='welcome', description='送出welcome message')
    @app_commands.checks.has_role('小雪團隊')
    async def welcome(self, i: Interaction):
        content = '旅行者們，歡迎來到「緣神有你」。\n在這裡你能收到提瓦特的二手消息, 還能找到志同道合的旅行者結伴同行。\n準備好踏上旅途了嗎? 出發前請先閱讀下方的「旅行者須知」。\n'
        rules = defaultEmbed(
            '🔖旅行者須知',
            '⚠️以下違規情形發生，將直接刪除貼文並禁言\n\n'
            '1. 張貼侵權事物的網址或載點\n'
            '2. 惡意引戰 / 惡意帶風向 / 仇恨言論或霸凌 / 煽動言論\n'
            '3. 交換 / 租借 / 買賣遊戲帳號、外掛\n'
            '4. 在色色台以外發表色情訊息 / 大尺度圖片 / 露點或者其他暴露圖 / \n使人感到不適的圖片或表情 / 以上相關連結\n'
            '5. 發送大量無意義言論洗版\n'
            '6. 討論政治相關內容\n'
            '7. 以暱稱惡搞或假冒管理員以及官方帳號 / 使用不雅的暱稱或簽名\n'
            '8. 推銷或發布垃圾訊息\n'
            '9. 私訊騷擾其他旅行者\n\n'
            '以上守則會隨著大家違規的創意和台主們的心情不定時更新, 感謝遵守規則的各位~\n'
        )
        view = WelcomeCog.AcceptRules(self.bot.db)
        await i.response.send_message(content=content, embed=rules, view=view)

    @welcome.error
    async def err_handle(self, interaction: Interaction, e: app_commands.AppCommandError):
        if isinstance(e, app_commands.errors.MissingRole):
            await interaction.response.send_message('你不是小雪團隊的一員!', ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WelcomeCog(bot))
