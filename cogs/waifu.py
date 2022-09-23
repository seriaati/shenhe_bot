import ast
import random

import hmtai
import waifuim
from apps.waifu.waifu_app import get_waifu_im_tags
from discord import app_commands, Interaction
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.ext import commands
from UI_elements.waifu import HmtaiTag, WaifuImTag
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, error_embed
from waifuim import WaifuAioClient

from discord.errors import Forbidden


class WaifuCog(commands.GroupCog, name="waifu"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @app_commands.command(name="sfw", description="透過選擇標籤來產出不色色的圖片")
    @app_commands.rename(num="張數")
    @app_commands.describe(num="上限 30 張")
    async def sfw(self, i: Interaction, num: int = 1):
        if num > 30:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name="不可大於 30 張", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        view = HmtaiTag.View(i.user, type="sfw")
        await i.response.send_message(view=view)
        view.message = await i.original_response()
        await view.wait()
        if view.tag is None:
            return
        x = view.tag.split("/")
        libs = ast.literal_eval(x[0])
        tag = x[1]
        lib = random.choice(libs)
        if num == 1:
            await i.edit_original_response(
                embed=default_embed(f"標籤: {tag}")
                .set_image(url=(hmtai.get(lib, tag)))
                .set_footer(text=f"API: {lib}"),
                view=None,
            )
        else:
            embeds = []
            for _ in range(0, num):
                lib = random.choice(libs)
                embed = default_embed(f"標籤: {tag}")
                embed.set_image(url=(hmtai.get(lib, tag)))
                embed.set_footer(text=f"API: {lib}")
                embeds.append(embed)
            await GeneralPaginator(i, embeds, self.bot.db).start(edit=True)

    @app_commands.command(name="nsfw", description="透過選擇標籤來產出色色的圖片", nsfw=True)
    @app_commands.rename(num="張數")
    @app_commands.describe(num="上限 30 張")
    async def nsfw(self, i: Interaction, num: int = 1):
        if num > 30:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name="上限為 30 張", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        view = HmtaiTag.View(i.user, type="nsfw")
        await i.response.send_message(view=view)
        view.message = await i.original_response()
        await view.wait()
        if view.tag is None:
            return
        await i.edit_original_response(
            embed=default_embed("<a:LOADER:982128111904776242> 正在尋找圖片..."), view=None
        )
        x = view.tag.split("/")
        libs = ast.literal_eval(x[0])
        tag = x[1]
        embeds = []
        for index in range(0, num):
            lib = random.choice(libs)
            url = hmtai.get(lib, tag)
            if url is None:
                return await i.edit_original_response(
                    embed=error_embed(message="您所指定的老婆條件要求太高\n請試試別的標籤").set_author(
                        name="找不到老婆", icon_url=i.user.display_avatar.url
                    )
                )
            embed = default_embed()
            embed.set_author(name="色色!", icon_url=i.user.display_avatar.url)
            embed.set_footer(text=f"API: {lib} | {index+1}/{num}")
            embed.set_image(url=url)
            embeds.append(embed)
        await i.delete_original_response()
        await i.followup.send(
            content="⚠️ 申鶴已將色圖私訊給你了。如果你在一個公共場所，請注意，圖片**沒有**暴雷 ⚠️",
            ephemeral=True,
        )
        try:
            await GeneralPaginator(i, embeds, self.bot.db).start(dm=True)
        except Forbidden:
            await i.followup.send(
                embed=error_embed(message="請使用 /remind 檢查隱私設定").set_author(
                    name="申鶴沒有辦法私訊你", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )

    @app_commands.command(name="waifu", description="利用 waifu.im API 隨機產生一張二次元老婆的照片")
    @app_commands.rename(sese="色色模式", many="多情模式", tags="標籤選擇")
    @app_commands.choices(
        sese=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
        many=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
        tags=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
    )
    @app_commands.describe(sese="是否要色色", many="產生多張老婆的照片", tags="透過標籤找到更符合你的需求的老婆")
    async def waifu(self, i: Interaction, many: int = 0, sese: int = 0, tags: int = 0):
        await i.response.defer()
        is_nsfw = "True" if sese == 1 else "False"
        if tags == 1:
            view = WaifuImTag.View(
                await get_waifu_im_tags(sese, self.bot.session), i.user
            )
            await i.followup.send(view=view)
            await view.wait()
            if len(view.tags) == 0:
                return
        await i.edit_original_response(
            embed=default_embed("<a:LOADER:982128111904776242> 正在尋找圖片..."), view=None
        )
        async with WaifuAioClient() as wf:
            wf: WaifuAioClient
            try:
                many_var = True if many == 1 else False
                image = await wf.random(
                    is_nsfw=[is_nsfw],
                    selected_tags=view.tags[0] if tags == 1 else [],
                    many=many_var,
                )
            except waifuim.exceptions.APIException:
                return await i.edit_original_response(
                    embed=error_embed(message="您所指定的老婆條件要求太高\n請試試別的標籤").set_author(
                        name="找不到老婆", icon_url=i.user.display_avatar.url
                    )
                )
            embeds = []
            if many == 0:
                image = [image]
            for index in range(0, len(image)):
                embed = default_embed()
                embed.set_author(
                    name=f"{i.user.display_name}的{'色色'if sese==1 else ''}後宮",
                    icon_url=i.user.display_avatar.url,
                )
                embed.set_image(url=image[index])
                embed.set_footer(text=f"API: waifu.im | {index+1}/{len(image)}")
                embeds.append(embed)
            if sese == 1:
                await i.delete_original_response()
                await i.followup.send(
                    content="⚠️ 申鶴已將色圖私訊給你了。如果你在一個公共場所，請注意，圖片**沒有**暴雷 ⚠️",
                    ephemeral=True,
                )
                try:
                    await GeneralPaginator(i, embeds, i.client.db).start(dm=True)
                except Forbidden:
                    await i.followup.send(
                        embed=error_embed(message="請使用 /remind 檢查隱私設定").set_author(
                            name="申鶴沒有辦法私訊你", icon_url=i.user.display_avatar.url
                        ),
                        ephemeral=True,
                    )
            else:
                await GeneralPaginator(i, embeds, i.client.db).start(edit=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WaifuCog(bot))
