import calendar
import uuid
from datetime import datetime
from typing import Any, List

import aiosqlite
import discord
from dateutil import parser
from debug import DefaultView
from discord import Button, Interaction, Member, SelectOption, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.ui import Select
from utility.apps.FlowApp import FlowApp
from utility.utils import defaultEmbed, errEmbed, log


class FlowCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.flow_app = FlowApp(self.bot.db, self.bot)
        self.debug_toggle = self.bot.debug_toggle

    @commands.Cog.listener()
    async def on_message(self, message):
        user_id = message.author.id
        user = self.bot.get_user(message.author.id)
        if message.author.bot:
            return

        if "早" in message.content or "午" in message.content or "晚" in message.content:
            if '早午晚' in message.content:
                await message.add_reaction('<:PaimonSeria:958341967698337854>')
                return
            check, msg = await self.flow_app.checkFlowAccount(user_id)
            if check == False:
                try:
                    await user.send(embed=msg)
                except:
                    pass
                return
            now = datetime.now()
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            if "早" in message.content:
                start = datetime(year=now.year, month=now.month,
                                 day=now.day, hour=5, minute=0, second=0, microsecond=0)
                end = datetime(year=now.year, month=now.month, day=now.day,
                               hour=11, minute=59, second=0, microsecond=0)
                if start <= now <= end:
                    await c.execute('SELECT morning FROM flow_accounts WHERE user_id = ?', (user_id,))
                    morning = await c.fetchone()
                    if parser.parse(morning[0]).day != now.day:
                        await self.flow_app.transaction(
                            user_id, 1, time_state='morning')
                        await message.add_reaction('<:morning:982608491426508810>')
            elif "午" in message.content:
                start = datetime(year=now.year, month=now.month, day=now.day,
                                 hour=12, minute=0, second=0, microsecond=0)
                end = datetime(year=now.year, month=now.month, day=now.day,
                               hour=17, minute=59, second=0, microsecond=0)
                if start <= now <= end:
                    await c.execute('SELECT noon FROM flow_accounts WHERE user_id = ?', (user_id,))
                    noon = await c.fetchone()
                    if parser.parse(noon[0]).day != now.day:
                        await self.flow_app.transaction(
                            user_id, 1, time_state='noon')
                        await message.add_reaction('<:noon:982608493313929246>')
            elif "晚" in message.content:
                start = datetime(year=now.year, month=now.month, day=now.day,
                                 hour=18, minute=0, second=0, microsecond=0)
                end = datetime(year=now.year, month=now.month+1 if now.day == calendar.monthrange(now.year, now.month)[
                               1] else now.month, day=1 if now.day == calendar.monthrange(now.year, now.month)[1] else now.day+1, hour=4, minute=59, second=0, microsecond=0)
                if start <= now <= end:
                    await c.execute('SELECT night FROM flow_accounts WHERE user_id = ?', (user_id,))
                    night = await c.fetchone()
                    if parser.parse(night[0]).day != now.day:
                        await self.flow_app.transaction(
                            user_id, 1, time_state='night')
                        await message.add_reaction('<:night:982608497290125366>')

    @app_commands.command(name='acc帳號', description='查看flow帳號')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的flow帳號')
    async def acc(self, i: Interaction, member: Member = None):
        member = member or i.user
        check, msg = await self.flow_app.checkFlowAccount(member.id)
        if check == False:
            return await i.response.send_message(embed=msg, ephemeral=True)
        db: aiosqlite.Connection = self.bot.db
        c = await db.cursor()
        await c.execute('SELECT morning, noon, night FROM flow_accounts WHERE user_id = ?', (member.id,))
        result = await c.fetchone()
        flow = await self.flow_app.get_user_flow(member.id)
        time_state_str = ''
        time_coin_list = ['<:morning:982608491426508810>', '<:noon:982608493313929246>', '<:night:982608497290125366>']
        for index in range(0, 3):
            new_time = (parser.parse(result[index])).strftime("%Y-%m-%d %H:%M:%S")
            time_state_str += f'{time_coin_list[index]} {new_time}\n'
        embed = defaultEmbed()
        embed.add_field(name=f'{flow} flow',value=time_state_str)
        embed.set_author(name=f'flow 帳號', icon_url=member.avatar)
        await i.response.send_message(embed=embed)

    @app_commands.command(name='give給錢', description='給其他人flow幣')
    @app_commands.rename(member='某人', flow='要給予的flow幣數量')
    async def give(self, i: Interaction, member: Member, flow: int):
        log(False, False, 'Give', f'{i.user.id} give {flow} to {member.id}')
        if member.id == i.user.id:
            return await i.response.send_message(
                embed=errEmbed(message='<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!').set_author(
                    name='不可以自己給自己flow幣', icon_url=i.user.avatar),
                ephemeral=True)
        if flow < 0:
            return await i.response.send_message(
                embed=errEmbed(message='<:PaimonSeria:958341967698337854> 還想學土司跟ceye洗錢啊!').set_author(
                    name='不可以給負數flow幣', icon_url=i.user.avatar),
                ephemeral=True)
        user_flow = await self.flow_app.get_user_flow(i.user.id)
        if user_flow < flow:
            return await i.response.send_message(embed=errEmbed(f'需要至少: {flow} flow').set_author(name="flow 幣不足", icon_url=i.user.avatar), ephemeral=True)
        await self.flow_app.transaction(i.user.id, -flow)
        await self.flow_app.transaction(member.id, flow)
        embed = defaultEmbed(message=
            f"{self.bot.get_user(i.user.id).mention} **- {flow}** flow幣\n"
            f"{self.bot.get_user(member.id).mention} **+ {flow}** flow幣").set_author(name='交易成功', icon_url=i.user.avatar)
        await i.response.send_message(content=f'{i.user.mention}{member.mention}', embed=embed)

    @app_commands.command(name='take收錢', description='將某人的flow幣轉回銀行')
    @app_commands.rename(member='某人', flow='要拿取的flow幣數量', private='私人訊息')
    @app_commands.choices(private=[
        Choice(name='是', value=0),
        Choice(name='否', value=1)])
    @app_commands.checks.has_role('小雪團隊')
    async def take(self, i: Interaction, member: Member, flow: int, private: int):
        check, msg = await self.flow_app.checkFlowAccount(member.id)
        if check == False:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        await self.flow_app.transaction(member.id, -flow)
        embed = defaultEmbed(
            "已成功施展「反」摩拉克斯的力量",
            f"{i.user.mention} 從 {self.bot.get_user(member.id).mention} 的帳戶裡拿走了**{flow}**枚flow幣"
        )
        ephemeral_toggler = True if private == 0 else False
        await i.response.send_message(embed=embed, ephemeral=ephemeral_toggler)

    @app_commands.command(name='make送錢', description='從銀行轉出flow幣給某人')
    @app_commands.rename(member='某人', flow='要給予的flow幣數量', private='私人訊息')
    @app_commands.choices(private=[
        Choice(name='是', value=0),
        Choice(name='否', value=1)])
    @app_commands.checks.has_role('小雪團隊')
    async def make(self, i: Interaction, member: Member, flow: int, private: int = 1):
        check, msg = await self.flow_app.checkFlowAccount(member.id)
        if check == False:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        await self.flow_app.transaction(member.id, int(flow))
        acceptor = self.bot.get_user(member.id)
        embed = defaultEmbed(
            "已成功施展摩拉克斯的力量",
            f"{i.user.mention} 給了 {acceptor.mention} {flow} 枚flow幣"
        )
        ephemeral_toggler = True if private == 0 else False
        await i.response.send_message(embed=embed, ephemeral=ephemeral_toggler)

    @app_commands.command(name='total總額', description='查看目前群組帳號及銀行flow幣分配情況')
    async def total(self, i: Interaction):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT SUM(flow) FROM flow_accounts')
        sum = await c.fetchone()
        bank = await self.flow_app.get_bank_flow()
        await c.execute('SELECT COUNT(*) FROM flow_accounts')
        account_count = await c.fetchone()
        embed = defaultEmbed(
            f'目前共{account_count[0]}個flow帳號',
            f'用戶 {sum[0]} +銀行 {bank} = {sum[0]+bank} 枚flow幣'
        )
        await i.response.send_message(embed=embed)

    @app_commands.command(name='flows所有帳號', description='查看群組內所有flow帳號')
    @app_commands.rename(category='範圍')
    @app_commands.describe(category='選擇要查看的flow幣範圍')
    @app_commands.choices(category=[
        Choice(name='小於 100 flow', value=0),
        Choice(name='100~200 flow', value=1),
        Choice(name='200~300 flow', value=2),
        Choice(name='大於 300 flow', value=3),
        Choice(name='總覽', value=4)])
    async def flows(self, i: Interaction, category: int):
        category_list = ['小於 100 flow', '100~200 flow',
                         '200~300 flow', '大於 300 flow', '總覽']
        result_list = []
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        if category == 0:
            await c.execute('SELECT user_id, flow FROM flow_accounts WHERE flow<100')
            result = await c.fetchall()
            for index, tuple in enumerate(result):
                result_list.append(
                    f'{i.client.get_user(tuple[0])}: {tuple[1]}')
        elif category == 1:
            await c.execute('SELECT user_id, flow FROM flow_accounts WHERE flow BETWEEN 100 AND 200')
            result = await c.fetchall()
            for index, tuple in enumerate(result):
                result_list.append(
                    f'{i.client.get_user(tuple[0])}: {tuple[1]}')
        elif category == 2:
            await c.execute('SELECT user_id, flow FROM flow_accounts WHERE flow BETWEEN 201 AND 300')
            result = await c.fetchall()
            for index, tuple in enumerate(result):
                result_list.append(
                    f'{i.client.get_user(tuple[0])}: {tuple[1]}')
        elif category == 3:
            await c.execute('SELECT user_id, flow FROM flow_accounts WHERE flow>300')
            result = await c.fetchall()
            for index, tuple in enumerate(result):
                result_list.append(
                    f'{i.client.get_user(tuple[0])}: {tuple[1]}')
        elif category == 4:
            await c.execute('SELECT user_id, flow FROM flow_accounts')
            result = await c.fetchall()
            for index, tuple in enumerate(result):
                result_list.append(
                    f'{i.client.get_user(tuple[0])}: {tuple[1]}'
                )
        if len(result_list) == 0:
            await i.response.send_message(embed=errEmbed('此範圍還沒有任何 flow帳號'), ephemeral=True)
        else:
            value_str = ''
            for user_str in result_list:
                value_str += f'{user_str}\n'
            await i.response.send_message(embed=defaultEmbed(category_list[category], value_str))

    class ShopItemView(DefaultView):
        def __init__(self, item_names: List, action: str, db: aiosqlite.Connection, bot: commands.Bot, author: Member):
            super().__init__(timeout=None)
            self.author = author
            self.add_item(FlowCog.ShopItemSelect(item_names, action, db, bot))

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed().set_author(name='輸入 `/shop` 來打開你的商店', icon_url=interaction.user.avatar), ephemeral=True)
            return self.author.id == interaction.user.id

    class ShopItemSelect(Select):
        def __init__(self, item_names: List, action: str, db: aiosqlite.Connection, bot):
            self.action = action
            self.db = db
            self.flow_app = FlowApp(self.db, bot)
            options = []
            for item_name in item_names:
                options.append(SelectOption(label=item_name, value=item_name))
            super().__init__(placeholder=f'選擇要購買的商品', min_values=1, max_values=1, options=options)

        async def callback(self, i: Interaction) -> Any:
            c = await self.db.cursor()
            if self.action == 'remove':
                await c.execute('DELETE FROM flow_shop WHERE name = ?', (self.values[0],))
                await i.response.send_message(f'商品**{self.values[0]}**移除成功', ephemeral=True)
            elif self.action == 'buy':
                await c.execute('SELECT flow, current, max FROM flow_shop WHERE name= ?', (self.values[0],))
                result = await c.fetchone()
                flow: int = result[0]
                current: int = result[1]
                max: int = result[2]
                user_flow = await self.flow_app.get_user_flow(i.user.id)
                if user_flow < flow:
                    return await i.response.send_message(embed=errEmbed().set_author(name="你的flow幣不足夠購買這項商品", icon_url=i.user.avatar), ephemeral=True)
                if current == max:
                    return await i.response.send_message(embed=errEmbed().set_author(name="這個商品已經售罄了", icon_url=i.user.avatar), ephemeral=True)
                log_uuid = str(uuid.uuid4())
                await c.execute('UPDATE flow_shop SET current = ? WHERE name = ?', (current+1, self.values[0]))
                await c.execute('INSERT INTO flow_shop_log (log_uuid) VALUES (?)', (log_uuid,))
                await c.execute('UPDATE flow_shop_log SET flow = ?, item = ?, buyer_id = ? WHERE log_uuid = ?', (int(flow), self.values[0], int(i.user.id), str(log_uuid)))
                await self.flow_app.transaction(i.user.id, -int(flow))
                await i.response.send_message(f"<:wish:982419859117838386> {i.user.mention} 商品 **{self.values[0]}** 購買成功, 詳情請查看私訊")
                msg = await i.original_message()
                thread = await msg.create_thread(name=f'{i.user} • {self.values[0]} 購買討論串')
                await thread.add_user(i.user)
                lulurR = i.client.get_user(665092644883398671)
                await thread.add_user(lulurR)
                embed = defaultEmbed(
                    "📜 購買證明",
                    f"購買人: {i.user.mention}\n"
                    f"商品: {self.values[0]}\n"
                    f"收據UUID: {log_uuid}\n"
                    f"價格: {flow}")
                await thread.send(embed=embed)
                log(False, False, 'shop buy', i.user.id)
            await self.db.commit()
    
    @app_commands.command(name='shop', description='顯示 flow 商店')
    async def show(self, i: Interaction):
        check, msg = await self.flow_app.checkFlowAccount(i.user.id)
        if check == False:
            return await i.response.send_message(embed=msg, ephemeral=True)
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT name, flow, current, max FROM flow_shop')
        result = await c.fetchall()
        item_str = ''
        item_names = []
        for index, tuple in enumerate(result):
            item_names.append(tuple[0])
            item_str += f'• {tuple[0]} - **{tuple[1]}** flow ({tuple[2]}/{tuple[3]})\n\n'
        embed = defaultEmbed("🛒 flow商店", item_str)
        view = FlowCog.ShopItemView(item_names, 'buy', self.bot.db, self.bot, i.user)
        await i.response.send_message(embed=embed, view=view)

    @app_commands.command(name='additem', description='新增商品')
    @app_commands.rename(item='商品名稱', flow='價格', max='最大購買次數')
    @app_commands.checks.has_role('小雪團隊')
    async def additem(self, i: Interaction, item: str, flow: int, max: int):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('INSERT INTO flow_shop(name) values(?)', (item,))
        await c.execute('UPDATE flow_shop SET flow = ?, current = 0, max = ? WHERE name = ?', (flow, max, item))
        await self.bot.db.commit()
        await i.response.send_message(f"商品**{item}**新增成功", ephemeral=True)

    @app_commands.command(name='removeitem', description='刪除商品')
    @app_commands.checks.has_role('小雪團隊')
    async def removeitem(self, i: Interaction):
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT name FROM flow_shop')
        result = await c.fetchall()
        item_names = []
        for index, tuple in enumerate(result):
            item_names.append(tuple[0])
        view = FlowCog.ShopItemView(
            item_names, 'remove', self.bot.db, self.bot)
        await i.response.send_message(view=view, ephemeral=True)

    def check_in_find_channel(self, channel_id: int):
        find_channel_id = 909595117952856084 if self.debug_toggle else 960861105503232030
        if channel_id != find_channel_id:
            channel = self.bot.get_channel(find_channel_id)
            return False, f"請在{channel.mention}裡使用此指令"
        else:
            return True, None

    async def check_flow(self, user_id: int, flow: int):
        user_flow = await self.flow_app.get_user_flow(user_id)
        if user_flow < 0 and flow >= 0:
            return True, None
        if flow < 0:
            result = errEmbed("發布失敗, 請輸入大於 1 的flow幣")
            return False, result
        elif user_flow < int(flow):
            result = errEmbed("發布失敗, 請勿輸入大於自己擁有數量的flow幣")
            return False, result
        else:
            return True, None

    class AcceptView(DefaultView):
        def __init__(self, db: aiosqlite.Connection, bot):
            super().__init__(timeout=None)
            self.db = db
            self.bot = bot

        async def interaction_check(self, i: Interaction) -> bool:
            c = await self.db.cursor()
            await c.execute('SELECT author_id FROM find WHERE msg_id = ?', (i.message.id,))
            author_id = await c.fetchone()
            author_id = author_id[0]
            if i.user.id == author_id:
                await i.response.send_message(embed=errEmbed('不能自己接自己的委託'), ephemeral=True)
            return i.user.id != author_id

        @discord.ui.button(label='接受委託', style=discord.ButtonStyle.green, custom_id='accept_commision_button')
        async def confirm(self, i: Interaction, button: discord.ui.Button):
            button.disabled = True
            await i.response.edit_message(view=self)
            msg = i.message
            c: aiosqlite.Cursor = await self.db.cursor()
            await c.execute('SELECT * FROM find WHERE msg_id = ?', (msg.id,))
            result = await c.fetchone()
            flow = result[1]
            title = result[2]
            type = result[3]
            author_id = result[4]
            author = i.client.get_user(author_id)
            confirmer = i.client.get_user(i.user.id)
            await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (confirmer.id,))
            uid = (await c.fetchone())[0]
            thread = await msg.create_thread(name=f"{author.name} • {title}")
            await thread.add_user(author)
            await thread.add_user(confirmer)
            if type == 2:
                await thread.send(embed=defaultEmbed(message=uid).set_author(name='接受人 uid', icon_url=confirmer.avatar))
            action_str = ['委託', '素材委託', '委託', '幫助']
            for index in range(1, 5):
                if type == index:
                    await i.followup.send(embed=defaultEmbed(message=f"{confirmer.mention} 已接受 {author.mention} 的 **{title}** {action_str[index-1]}").set_author(name='委託接受', icon_url=confirmer.avatar))
            if type == 4:
                embedDM = defaultEmbed(message=
                    f"當{confirmer.mention}完成幫忙的內容時, 請按OK來結算flow幣\n"
                    f"按下後, 你的flow幣將會 **-{flow}**\n"
                    f"對方則會 **+{flow}**")
            else:
                embedDM = defaultEmbed(message=
                    f"當{confirmer.mention}完成委託的內容時, 請按OK來結算flow幣\n"
                    f"按下後, 你的flow幣將會 **-{flow}**\n"
                    f"對方則會 **+{flow}**")
            embedDM.set_author(name='結算單', icon_url=author.avatar)
            view = FlowCog.ConfirmView(self.db, self.bot)
            confirm_message = await thread.send(embed=embedDM, view=view)
            await c.execute('UPDATE find SET msg_id = ?, confirmer_id = ? WHERE msg_ID = ?', (confirm_message.id, i.user.id, i.message.id))
            await self.db.commit()

    class ConfirmView(DefaultView):
        def __init__(self, db: aiosqlite.Connection, bot: commands.Bot):
            self.db = db
            self.flow_app = FlowApp(self.db, bot)
            self.bot = bot
            super().__init__(timeout=None)

        async def interaction_check(self, i: Interaction) -> bool:
            c = await self.db.cursor()
            await c.execute('SELECT author_id FROM find WHERE msg_id = ?', (i.message.id,))
            author_id = await c.fetchone()
            author_id = author_id[0]
            if i.user.id != author_id:
                await i.response.send_message(embed=errEmbed('你不是這個委託的發布者!'), ephemeral=True)
            return i.user.id == author_id

        @discord.ui.button(label='OK', style=discord.ButtonStyle.blurple, custom_id='ok_confirm_button')
        async def ok_confirm(self, i: Interaction, button: Button):
            c: aiosqlite.Cursor = await self.db.cursor()
            await c.execute('SELECT * FROM find WHERE msg_id = ?', (i.message.id,))
            result = await c.fetchone()
            flow = result[1]
            title = result[2]
            type = result[3]
            author_id = result[4]
            confirmer_id = result[5]
            str = ''
            author = i.client.get_user(author_id)
            confirmer = i.client.get_user(confirmer_id)
            await c.execute('SELECT find_free_trial FROM flow_accounts WHERE user_id = ?', (author_id,))
            result = await c.fetchone()
            author_free_trial = result[0]
            await c.execute('SELECT find_free_trial FROM flow_accounts WHERE user_id = ?', (confirmer_id,))
            result = await c.fetchone()
            if result is None:
                await self.flow_app.register(confirmer_id)
            confirmer_free_trial = result[0]
            if type == 4:
                new_flow = flow
                if confirmer_free_trial < 10 and flow >= 10:
                    new_flow = flow-10
                    await c.execute('UPDATE flow_accounts SET find_free_trial = ? WHERE user_id = ?', (confirmer_free_trial+1, confirmer_id))
                    str = f'({confirmer.mention}受到 10 flow幣贊助)\n'
                    f'已使用 {confirmer_free_trial+1}/10 次贊助機會'
                await self.flow_app.transaction(author_id, flow)
                await self.flow_app.transaction(confirmer_id, -int(new_flow))
                embed = defaultEmbed(
                    "🆗 結算成功",
                    f"幫忙名稱: {title}\n"
                    f"幫助人: {author.mention} **+{flow}** flow幣\n"
                    f"被幫助人: {confirmer.mention} **-{new_flow}** flow幣\n{str}")
            else:
                new_flow = flow
                if author_free_trial < 10 and flow >= 10:
                    new_flow = flow-10
                    await c.execute('UPDATE flow_accounts SET find_free_trial = ? WHERE user_id = ?', (author_free_trial+1, author_id))
                    str = f'({author.mention}受到 10 flow幣贊助)\n'
                    f'已使用 {author_free_trial+1}/10 次贊助機會'
                await self.flow_app.transaction(author_id, -int(new_flow))
                await self.flow_app.transaction(confirmer_id, flow)
                embed = defaultEmbed(
                    "🆗 結算成功",
                    f"委託名稱: {title}\n"
                    f"委託人: {author.mention} **-{new_flow}** flow幣\n"
                    f"接收人: {confirmer.mention} **+{flow}** flow幣\n{str}")
            await i.response.send_message(embed=embed)
            t = i.guild.get_thread(i.channel.id)
            await t.edit(archived=True)
            await c.execute('DELETE FROM find WHERE msg_id = ?', (i.message.id,))
            await self.db.commit()

    @app_commands.command(name='find發布委託', description='發布委託')
    @app_commands.rename(type='委託類型', title='幫助名稱', flow='flow幣數量', tag='tag人開關')
    @app_commands.describe(title='需要什麼幫助?', flow='這個幫助值多少flow幣?', tag='是否要tag委託通知?')
    @app_commands.choices(type=[
        Choice(name='1類委託 其他玩家進入你的世界(例如: 陪玩, 打素材等)', value=1),
        Choice(name='2類委託 你進入其他玩家的世界(例如: 拿特產)', value=2),
        Choice(name='3類委託 其他委託(例如: 打apex, valorant)', value=3),
        Choice(name='4類委託 可以幫助別人(讓拿素材, 可幫打刀鐔等)', value=4)],
        tag=[Choice(name='不tag', value=0),
             Choice(name='tag', value=1)])
    async def find(self, i: Interaction, type: int, title: str, flow: int, tag: int = 1):
        check, msg = self.check_in_find_channel(i.channel.id)
        if check == False:
            await i.response.send_message(msg, ephemeral=True)
            return
        check, msg = await self.flow_app.checkFlowAccount(i.user.id)
        if check == False:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        channel = i.client.get_channel(962311051683192842)
        role_found = False
        if not self.debug_toggle:
            WLroles = []
            for index in range(1, 9):
                WLroles.append(discord.utils.get(
                    i.user.guild.roles, name=f"W{str(index)}"))
            for r in WLroles:
                if r in i.user.roles:
                    role_name = r.name
                    role_found = True
                    break
        check, msg = await self.check_flow(i.user.id, flow)
        if check == False:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        if not role_found:
            role_str = f'請至 {channel.mention} 選擇世界等級身份組'
        else:
            if type == 1:
                if role_name == 'W8':
                    role_str = role_name
                else:
                    role_str = f'>= {role_name}'
            else:
                if role_name == 'W1':
                    role_str = role_name
                else:
                    role_str = f'<= {role_name}'
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
        uid = await c.fetchone()
        uid = uid[0]
        if type == 1:
            embed = defaultEmbed(
                f'請求幫助: {title}',
                f'發布者: {i.user.mention}\n'
                f'flow幣: {flow}\n'
                f'世界等級: {role_str}\n'
                f'發布者 UID: {uid}'
            )
        elif type == 2:
            embed = defaultEmbed(
                f'需要素材: {title}',
                f'發布者: {i.user.mention}\n'
                f'flow幣: {flow}\n'
                f'世界等級: {role_str}\n'
                f'發布者 UID: {uid}'
            )
        elif type == 3:
            embed = defaultEmbed(
                f'請求幫助: {title}',
                f'發布者: {i.user.mention}\n'
                f'flow幣: {flow}'
            )
        elif type == 4:
            embed = defaultEmbed(
                f'可以幫忙: {title}',
                f'發布者: {i.user.mention}\n'
                f'flow幣: {flow}\n'
                f'發布者世界等級: {role_name}\n'
                f'發布者 UID: {uid}'
            )
        if tag == 1:
            g = self.bot.get_guild(916838066117824553)  # 緣神有你
            role = g.get_role(965141973700857876)  # 委託通知
            await i.channel.send(role.mention)
        view = self.AcceptView(self.bot.db, self.bot)
        await i.response.send_message(embed=embed, view=view)
        msg = await i.original_message()
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('INSERT INTO find(msg_id, flow, title, type, author_id) VALUES (?, ?, ?, ?, ?)', (msg.id, flow, title, type, i.user.id))
        await self.bot.db.commit()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FlowCog(bot))
