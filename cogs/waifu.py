import json

import waifuim
from apps.waifu.waifu_app import get_waifu_im_tags
from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.ext import commands
from UI_elements.waifu import HmtaiTag, WaifuImTag
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, error_embed
from waifuim import WaifuAioClient


class WaifuCog(commands.GroupCog, name="waifu"):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        with open("data/waifu/tags.json", "r", encoding="utf-8") as f:
            self.tags = json.load(f)

    async def hm_tai_command(self, i: Interaction, num: int, tag_type: str):
        await i.response.defer(ephemeral=True)
        if num > 30:
            return await i.followup.send(
                embed=error_embed().set_author(
                    name="不可大於 30 張", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        view = HmtaiTag.View(self.tags[tag_type], num)
        await i.followup.send(view=view, ephemeral=True)
        view.message = await i.original_response()

    @app_commands.command(name="sfw", description="透過選擇標籤來產出不色色的圖片")
    @app_commands.rename(num="張數")
    @app_commands.describe(num="上限 30 張")
    async def sfw(self, i: Interaction, num: int = 1):
        await self.hm_tai_command(i, num, "sfw")

    @app_commands.command(name="nsfw", description="透過選擇標籤來產出色色的圖片", nsfw=True)
    @app_commands.rename(num="張數")
    @app_commands.describe(num="上限 30 張")
    async def nsfw(self, i: Interaction, num: int = 1):
        await self.hm_tai_command(i, num, "nsfw")

    @app_commands.command(name="wallpaper", description="透過選擇標籤來產出桌布圖片")
    @app_commands.rename(num="張數")
    @app_commands.describe(num="上限 30 張")
    async def wallpaper(self, i: Interaction, num: int = 1):
        await self.hm_tai_command(i, num, "wallpaper")

    @app_commands.command(name="waifu_im", description="利用 waifu.im API 隨機產生一張二次元老婆的照片")
    @app_commands.rename(sese="色色模式", tags="標籤選擇", many="多張模式")
    @app_commands.choices(
        sese=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
        tags=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
        many=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
    )
    @app_commands.describe(sese="是否要色色", many="產生多張老婆的照片", tags="透過標籤找到更符合你的需求的老婆")
    async def waifu(self, i: Interaction, many: int = 0, sese: int = 0, tags: int = 0):
        await i.response.defer(ephemeral=True)
        is_nsfw = True if sese == 1 else False
        if tags == 1:
            view = WaifuImTag.View(await get_waifu_im_tags(sese, i.client.session), i.user)
            await i.followup.send(view=view, ephemeral=True)
            view.message = await i.original_response()
            await view.wait()
            if not view.tags:
                return
        await i.edit_original_response(
            embed=default_embed("<a:LOADER:982128111904776242> 正在尋找圖片..."), view=None
        )
        async with WaifuAioClient() as wf:
            wf: WaifuAioClient
            try:
                many_var = True if many > 1 else False
                images = await wf.random(
                    is_nsfw=is_nsfw,
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
            if not isinstance(images, list):
                images = [images]
            for index, image in enumerate(images):
                embed = default_embed()
                embed.set_author(
                    name=f"{i.user.display_name}的{'色色'if sese==1 else ''}後宮",
                    icon_url=i.user.display_avatar.url,
                )
                embed.set_image(url=image)
                embed.set_footer(text=f"API: waifu.im | {index}/{len(images)}")
                embeds.append(embed)
            await GeneralPaginator(i, embeds, i.client.db).start(edit=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WaifuCog(bot))
