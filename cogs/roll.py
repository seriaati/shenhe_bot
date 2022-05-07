import asyncio
import discord
from discord.ext import commands
from discord import Interaction, app_commands
from utility.FlowApp import flow_app
from utility.utils import errEmbed, openFile, defaultEmbed
from utility.RollApp import animation_chooser, check_big_prize, check_user_data, give_money, gu_system, write_history_and_gu

global contribution_mode
contribution_mode = True

class RollCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    class Menu(discord.ui.View):
        def __init__(self, author: discord.Member, banner: str):
            super().__init__(timeout=None)
            banners = openFile('roll')
            self.author = author
            self.banner = banner
            self.banner_pic = banners[banner]['banner_pic']
            self.big_prize = banners[banner]['big_prize']

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.author.id

        class Confirm(discord.ui.View):
            def __init__(self, author: discord.Member, is_ten_pull: bool, banner: str):
                super().__init__(timeout=None)
                banners = openFile('roll')
                self.author = author
                self.banner = banner
                self.ten_pull = is_ten_pull
                self.banner_pic = banners[banner]['banner_pic']
                self.big_prize = banners[banner]['big_prize']

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user.id == self.author.id

            @discord.ui.button(label='確認', style=discord.ButtonStyle.green, row=0)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not self.ten_pull:
                    flow_app.transaction(
                        user_id=interaction.user.id, flow_for_user=-10)
                else:
                    flow_app.transaction(
                        user_id=interaction.user.id, flow_for_user=-100)
                check_user_data(interaction.user.id, self.banner, contribution_mode)
                prize = gu_system(interaction.user.id, self.ten_pull, self.banner, contribution_mode)
                give_money(interaction.user.id, prize)
                luluR = interaction.client.get_user(665092644883398671)
                check, msg = check_big_prize(
                    interaction.user.id, prize, self.banner, contribution_mode)
                if check == True:
                    await luluR.send(embed=msg)
                gif, sleep_time = animation_chooser(prize, self.banner)
                result = write_history_and_gu(
                    interaction.user.id, prize, self.banner, contribution_mode)
                embed = defaultEmbed(self.banner, '')
                embed.set_image(url=gif)
                menu = RollCog.Menu(
                    author=interaction.user, banner=self.banner)
                await interaction.response.edit_message(embed=embed, view=menu)
                await asyncio.sleep(sleep_time)
                embed = defaultEmbed('抽卡結果', result)
                await interaction.followup.send(embed=embed, ephemeral=True)
                embed = defaultEmbed(self.banner, '')
                embed.set_image(url=self.banner_pic)
                await interaction.edit_original_message(embed=embed)

            @discord.ui.button(label='取消', style=discord.ButtonStyle.grey, row=0)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                menu = RollCog.Menu(interaction.user, self.banner)
                await interaction.response.edit_message(view=menu)

        @discord.ui.button(label='詳情', style=discord.ButtonStyle.gray, row=0)
        async def detail_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = defaultEmbed('祈願詳情', '')
            embed.add_field(
                name=f'限定 UP - {self.big_prize}',
                value="70抽之前: 0.6%\n"
                "70-80抽: 5%\n"
                "80-90抽: 10%\n"
                "1000抽: 100%",
                inline=False
            )
            embed.add_field(
                name='其他獎品',
                value='10 Flow幣: 10%\n'
                '100 Flow: 3%\n'
                '1000 Flow: 0.1%',
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='歷史紀錄', style=discord.ButtonStyle.gray, row=0)
        async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            history = openFile('pull_history')
            gu = openFile('pull_guarantee')
            sum = 0
            gu_sum = 0
            result = ''
            if self.banner not in history[interaction.user.id]:
                result = '你還沒有在這期抽過卡!'
            else:
                for item, count in history[interaction.user.id][self.banner].items():
                    sum += count
                    result += f'{item} • {count}次\n'
                for item, count in gu[interaction.user.id][self.banner].items():
                    gu_sum += count
            embed = defaultEmbed(f'祈願紀錄(共{sum}抽, 目前距離保底{90-gu_sum}抽)', result)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='祈願1次', style=discord.ButtonStyle.blurple, row=0)
        async def one_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < 10:
                embed = errEmbed('你的flow幣不足!', '1次祈願需花費10 flow幣')
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            confirm = self.Confirm(
                author=interaction.user, is_ten_pull=False, banner=self.banner)
            await interaction.response.edit_message(view=confirm)

        @discord.ui.button(label='祈願10次', style=discord.ButtonStyle.blurple, row=0)
        async def ten_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < 100:
                embed = errEmbed('你的flow幣不足!', '10次祈願共需花費100 flow幣')
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            confirm = self.Confirm(
                author=interaction.user, is_ten_pull=True, banner=self.banner)
            await interaction.response.edit_message(view=confirm)

        def get_banner_options():
            banners = openFile('roll')
            banner_list = []
            for banner, value in banners.items():
                banner_list.append(discord.SelectOption(label=banner))
            return banner_list

        @discord.ui.select(options=get_banner_options(), row=1, placeholder='請選擇你想要抽取的獎品池', min_values=1, max_values=1)
        async def banner_chooser(self, interaction: discord.Interaction, select: discord.ui.Select):
            banners = openFile('roll')
            banner = select.values[0]
            menu = RollCog.Menu(interaction.user, banner)
            embed = defaultEmbed(banner, '')
            embed.set_image(url=banners[banner]['banner_pic'])
            await interaction.response.edit_message(embed=embed, view=menu)

    @app_commands.command(name='roll', description='flow幣祈願系統')
    async def roll(self, interaction: discord.Interaction):
        check, msg = flow_app.checkFlowAccount(interaction.user.id)
        if check == False:
            await interaction.response.send_message(embed=msg, ephemeral=True)
            return
        banners = openFile('roll')
        banner = '星月交輝 - 限定祈願'
        menu = self.Menu(interaction.user, banner)
        embed = defaultEmbed(banner, '')
        embed.set_image(url=banners[banner]['banner_pic'])
        await interaction.response.send_message(embed=embed, view=menu)

    @app_commands.command(name='rollstats', description='查看祈願系統資料')
    async def roll_stats(self, i: Interaction):
        history = openFile('pull_history')
        sum = 0
        for user_id, banners in history.items():
            for banner_name, rolls in banners.items():
                for prize, count in rolls.items():
                    sum+=count
        await i.response.send_message(embed=defaultEmbed('祈願資料',f'總祈願數: {sum}'))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RollCog(bot))
