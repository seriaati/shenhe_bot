import asyncio

import aiosqlite
import discord
from discord import ButtonStyle, Interaction, app_commands
from discord.ext import commands
from discord.ui import Button, button
from debug import DefaultView
from utility.apps.FlowApp import FlowApp
from utility.apps.RollApp import RollApp
from utility.utils import defaultEmbed, errEmbed, log

global one_pull_price
one_pull_price = 10


class RollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.debug_toggle = self.bot.debug_toggle
        self.flow_app = FlowApp(self.bot.db, self.bot)

    class Menu(DefaultView):
        def __init__(self, author: discord.Member, banner: str, db: aiosqlite.Connection, bot):
            super().__init__(timeout=None)
            self.db = db
            self.flow_app = FlowApp(self.db, bot)
            self.author = author
            self.banner = banner
            self.bot = bot

        async def interaction_check(self, i: Interaction) -> bool:
            if i.user.id != self.author.id:
                await i.response.send_message(embed=errEmbed('這不是你的遊戲視窗','輸入 `/roll` 來開啟一個'), ephemeral=True)
            return i.user.id == self.author.id

        @button(label='詳情', style=ButtonStyle.gray)
        async def detail_button(self, i: Interaction, button: Button):
            embed = defaultEmbed('祈願詳情', '')
            c = await self.db.cursor()
            await c.execute('SELECT big_prize FROM banners WHERE banner_name = ?', (self.banner,))
            big_prize = await c.fetchone()
            big_prize = big_prize[0]
            embed.add_field(
                name=f'限定 UP - {big_prize}',
                value="70抽之前: 0.6%\n"
                "70-79抽: 5%\n"
                "80-89抽: 10%\n"
                "90抽: 100%",
                inline=False
            )
            embed.add_field(
                name='其他獎品',
                value='10 Flow幣: 10%\n'
                '100 Flow: 1%\n',
                inline=False
            )
            await i.response.send_message(embed=embed, ephemeral=True)

        @button(label='歷史紀錄', style=ButtonStyle.gray)
        async def history_button(self, i: Interaction, button: Button):
            c = await self.db.cursor()
            await c.execute('SELECT * FROM user_roll_data WHERE user_id = ? AND banner_name = ?', (i.user.id, self.banner))
            user_history = await c.fetchone()
            if user_history is None:
                await i.response.send_message(embed=defaultEmbed('你還沒有在這期抽過卡!'), ephemeral=True)
                return
            await c.execute('SELECT SUM (history) FROM user_roll_data WHERE user_id = ? AND banner_name = ?', (i.user.id, self.banner))
            pull_sum = await c.fetchone()
            pull_sum = pull_sum[0]
            await c.execute('SELECT SUM (guarantee) FROM user_roll_data WHERE user_id = ? AND banner_name = ?', (i.user.id, self.banner))
            guarantee_sum = await c.fetchone()
            guarantee_sum = guarantee_sum[0]
            result = ''
            await c.execute('SELECT prize_name, history FROM user_roll_data WHERE user_id = ? AND banner_name = ? AND guarantee IS NULL', (i.user.id, self.banner))
            user_history = await c.fetchall()
            for index, tuple in enumerate(user_history):
                prize_name = tuple[0]
                history_num = tuple[1]
                result += f'{prize_name} • {history_num}次\n'
            embed = defaultEmbed(
                f'<:wish:982419859117838386> 祈願紀錄(目前距離保底{90-guarantee_sum}抽)', f'總共{pull_sum}抽\n{result}')
            await i.response.send_message(embed=embed, ephemeral=True)

        @button(label='祈願1次', style=ButtonStyle.blurple)
        async def one_pull_button(self, i: Interaction, button: Button):
            user_flow = await self.flow_app.get_user_flow(i.user.id)
            if user_flow < one_pull_price:
                return await i.response.send_message(embed=errEmbed(message=f'1 次祈願需花費{one_pull_price} flow幣').set_author(name='flow 幣不足', icon_url=i.user.avatar), ephemeral=True)
            confirm = RollCog.Confirm(
                i.user, False, self.banner, self.db, self.bot)
            await i.response.edit_message(view=confirm)

        @button(label='祈願10次', style=ButtonStyle.blurple)
        async def ten_pull_button(self, i: Interaction, button: Button):
            user_flow = await self.flow_app.get_user_flow(i.user.id)
            if user_flow < int(one_pull_price)*10:
                return await i.response.send_message(embed=errEmbed(message=f'10 次祈願需花費{int(one_pull_price)*10} flow幣').set_author(name='flow 幣不足', icon_url=i.user.avatar), ephemeral=True)
            confirm = RollCog.Confirm(
                i.user, True, self.banner, self.db, self.bot)
            await i.response.edit_message(view=confirm)

    class Confirm(discord.ui.View):
        def __init__(self, author: discord.Member, is_ten_pull: bool, banner: str, db: aiosqlite.Connection, bot):
            super().__init__(timeout=None)
            self.db = db
            self.flow_app = FlowApp(self.db, bot)
            self.roll_app = RollApp(self.db, bot)
            self.author = author
            self.banner = banner
            self.ten_pull = is_ten_pull
            self.bot = bot

        async def interaction_check(self, i: Interaction) -> bool:
            if i.user.id != self.author.id:
                await i.response.send_message(embed=errEmbed('這不是你的遊戲視窗','輸入 `/roll` 來開啟一個'), ephemeral=True)
            return i.user.id == self.author.id

        @button(label='確認', style=ButtonStyle.green, row=0)
        async def confirm(self, i: Interaction, button: Button):
            c = await self.db.cursor()
            if not self.ten_pull:
                await self.flow_app.transaction(
                    user_id=i.user.id, flow_for_user=-int(one_pull_price))
            else:
                await self.flow_app.transaction(
                    user_id=i.user.id, flow_for_user=-int(one_pull_price)*10)
            prize = await self.roll_app.gu_system(i.user.id, self.banner, self.ten_pull)
            await self.roll_app.give_money(i.user.id, prize)
            luluR = i.client.get_user(665092644883398671)
            check, msg = await self.roll_app.check_big_prize(
                i.user.id, prize, self.banner)
            if check:
                await luluR.send(embed=msg)
                log(True, False, 'Roll', f'{i.user.id} got big prize')
                public_channel = i.client.get_channel(
                    916951131022843964) if not self.debug_toggle else i.client.get_channel(909595117952856084)
                await public_channel.send(f'🎉 恭喜 {i.user.mention} 抽到 **{self.banner}** 的大獎！！ 🎉')
            gif, sleep_time = await self.roll_app.animation_chooser(prize, self.banner)
            result = await self.roll_app.write_history_and_gu(
                i.user.id, prize, self.banner)
            embed = defaultEmbed(self.banner, '')
            embed.set_image(url=gif)
            menu = RollCog.Menu(i.user, self.banner, self.db, self.bot)
            await i.response.edit_message(embed=embed, view=menu)
            await asyncio.sleep(sleep_time)
            embed = defaultEmbed('抽卡結果', result)
            await i.followup.send(embed=embed, ephemeral=True)
            embed = defaultEmbed(self.banner)
            await c.execute('SELECT image_url FROM banners WHERE banner_name = ?', (self.banner,))
            banner_image_url = await c.fetchone()
            banner_image_url = banner_image_url[0]
            embed.set_image(url=banner_image_url)
            await i.edit_original_message(embed=embed)

        @button(label='取消', style=ButtonStyle.grey, row=0)
        async def cancel(self, i: Interaction, button: Button):
            menu = RollCog.Menu(i.user, self.banner, self.db, self.bot)
            await i.response.edit_message(view=menu)

    @app_commands.command(name='roll祈願', description='flow幣祈願系統')
    async def roll(self, i: Interaction):
        check, msg = await self.flow_app.checkFlowAccount(i.user.id)
        if check == False:
            await i.response.send_message(embed=msg, ephemeral=True)
            return
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT banner_name FROM banners')
        banner_name = await c.fetchone()
        banner_name = banner_name[0]
        await c.execute('SELECT image_url FROM banners WHERE banner_name = ?', (banner_name,))
        banner_image_url = await c.fetchone()
        banner_image_url = banner_image_url[0]
        menu = self.Menu(i.user, banner_name, self.bot.db, self.bot)
        embed = defaultEmbed(banner_name)
        embed.set_image(url=banner_image_url)
        await i.response.send_message(embed=embed, view=menu)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RollCog(bot))
