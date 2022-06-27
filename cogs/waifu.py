from ast import ExceptHandler
import io
from typing import Any, List
import aiohttp
from discord.ext import commands
from discord import ButtonStyle, Interaction, Member, SelectOption, app_commands, File
from discord.app_commands import Choice
from discord.ui import Select, select, Button
import waifuim
from waifuim import WaifuAioClient
from debug import DefaultView
from utility.paginators.GeneralPaginator import GeneralPaginator
import utility.global_vars as emoji
from utility.utils import defaultEmbed, errEmbed


class WaifuCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def waifu_tags(sese: int, bot: commands.Bot):
        async with bot.session.get('https://api.waifu.im/tags/?full=on') as r:
            tags = await r.json()
        choices = []
        for tag in tags['versatile']:
            choices.append(SelectOption(label=tag['name']))
        if sese == 1:
            for tag in tags['nsfw']:
                choices.append(SelectOption(label=tag['name']))
        return choices

    class TagSelectorView(DefaultView):
        def __init__(self, choices: List, author: Member):
            super().__init__(timeout=None)
            self.add_item(WaifuCog.TagSelector(choices))
            self.tags = []
            self.author = author

        async def interaction_check(self, interaction: Interaction) -> bool:
            if self.author.id != interaction.user.id:
                await interaction.response.send_message(embed=errEmbed(f'{emoji.error} 這不是你的操控視窗', '輸入 `/waifu` 來自行選擇標籤'), ephemeral=True)
            return self.author.id == interaction.user.id

    class TagSelector(Select):
        def __init__(self, choices: List) -> None:
            super().__init__(placeholder='選擇你想要查詢的標籤', min_values=1,
                             max_values=len(choices), options=choices)

        async def callback(self, interaction: Interaction) -> Any:
            await interaction.response.defer()
            self.view.tags.append(self.values)
            self.view.stop()

    @app_commands.command(name='waifu', description='從 waifu API 隨機產生一張老婆的照片(?')
    @app_commands.rename(sese='色色模式', many='多情模式', tags='標籤選擇')
    @app_commands.choices(sese=[Choice(name='開啟', value=1), Choice(name='關閉', value=0)], many=[Choice(name='開啟', value=1), Choice(name='關閉', value=0)], tags=[Choice(name='開啟', value=1), Choice(name='關閉', value=0)])
    @app_commands.describe(sese='是否要色色', many='產生 30 張老婆的照片 (色色模式開啟時5張', tags='透過標籤找到更符合你的需求的老婆')
    async def waifu(self, i: Interaction, many: int = 0, sese: int = 0, tags: int = 0):
        await i.response.defer()
        async with WaifuAioClient() as wf:
            sese_id = 965842415913152522 if not self.bot.debug_toggle else 984792329426714677
            if i.channel.id != sese_id and sese == 1:
                return await i.followup.send(embed=errEmbed(f'{emoji.error} 只能在色色台開啟色色模式哦'), ephemeral=True)
            is_nsfw = 'True' if sese == 1 else 'False'
            if tags == 1:
                view = WaifuCog.TagSelectorView(await WaifuCog.waifu_tags(sese, self.bot), i.user)
                await i.followup.send(view=view)
                await view.wait()
            if many == 0:
                if tags == 1:
                    try:
                        image = await wf.random(is_nsfw=[is_nsfw], selected_tags=view.tags[0])
                    except waifuim.exceptions.APIException:
                        return await i.edit_original_message(embed=errEmbed(f'{emoji.error} 找不到老婆', '您所指定的老婆條件要求太高\n請試試別的標籤'), view=None)
                else:
                    image = await wf.random(is_nsfw=[is_nsfw])
                if sese == 1:
                    async with self.bot.session.get(str(image)) as resp:
                        bytes_obj = io.BytesIO(await resp.read())
                        file = File(
                            bytes_obj, filename='waifu_image.jpg', spoiler=True)
                    if tags == 1:
                        await i.edit_original_message(attachments=[file], view=None)
                    else:
                        await i.followup.send(file=file)
                else:
                    embed = defaultEmbed('您的老婆已送達')
                    embed.set_image(url=image)
                    if tags == 1:
                        await i.edit_original_message(embed=embed, view=None)
                    else:
                        await i.followup.send(embed=embed)

            else:
                if tags == 1:
                    try:
                        images = await wf.random(is_nsfw=[is_nsfw], many=True, selected_tags=view.tags[0])
                    except waifuim.exceptions.APIException:
                        return await i.edit_original_message(embed=errEmbed(f'{emoji.error} 找不到老婆', '您所指定的老婆條件要求太高\n請試試別的標籤'), view=None)
                else:
                    images = await wf.random(is_nsfw=[is_nsfw], many=True)
                if sese == 1:
                    for index in range(0, 5):
                        async with self.bot.session.get(str(images[index])) as resp:
                            bytes_obj = io.BytesIO(await resp.read())
                            file = File(
                                bytes_obj, filename='waifu_image.jpg', spoiler=True)
                        if index == 0:
                            await (await i.original_message()).delete()
                        await i.channel.send(file=file)
                else:
                    embeds = []
                    count = 0
                    for image in images:
                        count += 1
                        embed = defaultEmbed(f'{i.user.display_name} 的後宮')
                        embed.set_image(url=image)
                        embed.set_footer(text=f'第 {count}/30 位老婆')
                        embeds.append(embed)
                    await GeneralPaginator(i, embeds).start(embeded=True, follow_up=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WaifuCog(bot))
