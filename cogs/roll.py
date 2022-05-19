import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from utility.FlowApp import flow_app
from utility.utils import errEmbed, openFile, defaultEmbed
from utility.RollApp import animation_chooser, check_big_prize, check_user_data, give_money, gu_system, write_history_and_gu

global contribution_mode
contribution_mode = False


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
                one_pull_price = -10
                if not self.ten_pull:
                    flow_app.transaction(
                        user_id=interaction.user.id, flow_for_user=one_pull_price)
                else:
                    flow_app.transaction(
                        user_id=interaction.user.id, flow_for_user=int(one_pull_price)*10)
                check_user_data(interaction.user.id,
                                self.banner, contribution_mode)
                prize = gu_system(interaction.user.id, self.banner,
                                  self.ten_pull, contribution_mode)
                give_money(interaction.user.id, prize)
                luluR = interaction.client.get_user(665092644883398671)
                check, msg = check_big_prize(
                    interaction.user.id, prize, self.banner, contribution_mode)
                if check == True:
                    await luluR.send(embed=msg)
                    public_channel = await interaction.client.get_channel(916951131022843964)
                    await public_channel.send(f'🎉 恭喜{interaction.user.mention}抽到**{self.banner}**的大獎！！ 🎉')
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
            if contribution_mode == False:
                embed.add_field(
                    name=f'限定 UP - {self.big_prize}',
                    value="70抽之前: 0.6%\n"
                    "70-79抽: 5%\n"
                    "80-89抽: 10%\n"
                    "90抽: 100%",
                    inline=False
                )
            else:
                embed.add_field(
                    name='公眾池模式',
                    value='所有人保底及歷史紀錄共計\n'
                    '100抽: 100%',
                    inline=False
                )
            embed.add_field(
                name='其他獎品',
                value='10 Flow幣: 10%\n'
                '100 Flow: 1%\n',
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='歷史紀錄', style=discord.ButtonStyle.gray, row=0)
        async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            history = openFile('pull_history')
            gu = openFile('pull_guarantee')
            user_id = 'all' if contribution_mode == True else interaction.user.id
            gu_count = 100 if contribution_mode == True else 90
            if user_id not in history:
                history[user_id] = {}
            if user_id not in gu:
                gu[user_id] = {}
            sum = 0
            gu_sum = 0
            result = ''
            if contribution_mode == True:
                user_id = 'all'
            if self.banner not in history[user_id]:
                result = '你還沒有在這期抽過卡!'
            else:
                for item, count in history[user_id][self.banner].items():
                    sum += count
                    result += f'{item} • {count}次\n'
                for item, count in gu[user_id][self.banner].items():
                    gu_sum += count
            embed = defaultEmbed(
                f'祈願紀錄(共{sum}抽, 目前距離保底{gu_count-gu_sum}抽)', result)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label='祈願1次', style=discord.ButtonStyle.blurple, row=0, disabled=False)
        async def one_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            one_pull_price = 10
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < one_pull_price:
                embed = errEmbed(
                    '你的flow幣不足!', f'1次祈願需花費{one_pull_price} flow幣')
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            confirm = self.Confirm(
                author=interaction.user, is_ten_pull=False, banner=self.banner)
            await interaction.response.edit_message(view=confirm)

        @discord.ui.button(label='祈願10次', style=discord.ButtonStyle.blurple, row=0, disabled=False)
        async def ten_pull_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            one_pull_price = 10
            users = openFile('flow')
            if users[interaction.user.id]['flow'] < int(one_pull_price)*10:
                embed = errEmbed(
                    '你的flow幣不足!', f'10次祈願共需花費{int(one_pull_price)*10} flow幣')
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
        banner = (list(banners.keys())[0])
        menu = self.Menu(interaction.user, banner)
        embed = defaultEmbed(banner, '')
        embed.set_image(url=banners[banner]['banner_pic'])
        await interaction.response.send_message(embed=embed, view=menu)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RollCog(bot))
