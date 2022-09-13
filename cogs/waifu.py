import ast
import io
import random
from typing import List

import hmtai
import waifuim
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from apps.waifu.waifu_app import get_waifu_im_tags
from discord import File, Interaction, app_commands
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.errors import HTTPException
from discord.ext import commands
from PIL import Image
from ui_elements.waifu import DeleteImage, HmtaiTag, WaifuImTag
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, error_embed
from waifuim import WaifuAioClient


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
    @app_commands.describe(num="上限 5 張")
    async def nsfw(self, i: Interaction, num: int = 1):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if num > 5:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name="上限為 5 張", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        if i.channel.guild is not None and not i.channel.nsfw:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name="請先開啟此頻道的年齡限制設定", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        view = HmtaiTag.View(i.user, type="nsfw")
        await i.response.send_message(view=view)
        view.message = await i.original_response()
        await view.wait()
        if view.tag is None:
            return
        x = view.tag.split("/")
        libs = ast.literal_eval(x[0])
        tag = x[1]
        lib = random.choice(libs)
        url = hmtai.get(lib, tag)
        if url is None:
            return await i.edit_original_response(
                embed=error_embed(message="您所指定的老婆條件要求太高\n請試試別的標籤").set_author(
                    name="找不到老婆", icon_url=i.user.display_avatar.url
                ),
                view=None,
            )
        if num == 1:
            await i.edit_original_response(
                embed=default_embed(
                    "<a:LOADER:982128111904776242> 尋找及下載圖片中...", "時長取決於小雪家裡網路速度"
                ),
                view=None,
            )
            async with self.bot.session.get(str(url)) as resp:
                bytes_obj = io.BytesIO(await resp.read())
            if tag != "gif":
                image = Image.open(bytes_obj)
                image = image.convert("RGBA")
                fp = io.BytesIO()
                image.save(fp, "PNG", optimize=True, quality=10)
                fp.seek(0)
            else:
                fp = bytes_obj
            file = File(fp, filename="waifu_image.gif", spoiler=True)
            view = DeleteImage.View(i.user)
            try:
                await i.edit_original_response(
                    embed=None, attachments=[file], view=view
                )
            except HTTPException as e:
                if e.code == 40005:
                    await i.edit_original_response(
                        embed=default_embed(message=url).set_author(
                            name=text_map.get(532, i.locale, user_locale),
                            icon_url=i.user.display_avatar.url,
                        ),
                    )
            view.message = await i.original_response()
        else:
            await i.edit_original_response(
                embed=default_embed("<a:LOADER:982128111904776242> 尋找及下載圖片中..."),
                view=None,
            )
            for _ in range(0, num):
                lib = random.choice(libs)
                url = hmtai.get(lib, tag)
                if url is None:
                    break
                async with self.bot.session.get(str(url)) as resp:
                    bytes_obj = io.BytesIO(await resp.read())
                if tag != "gif":
                    image = Image.open(bytes_obj)
                    image = image.convert("RGBA")
                    fp = io.BytesIO()
                    image.save(fp, "PNG", optimize=True, quality=10)
                    fp.seek(0)
                else:
                    fp = bytes_obj
                file = File(fp, filename="waifu_image.gif", spoiler=True)
                view = DeleteImage.View(i.user)
                try:
                    view.message = await i.channel.send(file=file, view=view)
                except HTTPException as e:
                    if e.code == 40005:
                        await i.channel.send(
                            embed=default_embed(message=url).set_author(
                                name=text_map.get(532, i.locale, user_locale),
                                icon_url=i.user.display_avatar.url,
                            ),
                        )
            await i.delete_original_response()

    @app_commands.command(name="waifu", description="利用 waifu.im API 隨機產生一張二次元老婆的照片")
    @app_commands.rename(sese="色色模式", many="多情模式", tags="標籤選擇")
    @app_commands.choices(
        sese=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
        many=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
        tags=[Choice(name="開啟", value=1), Choice(name="關閉", value=0)],
    )
    @app_commands.describe(
        sese="是否要色色", many="產生多張老婆的照片 (色色模式開啟時5張", tags="透過標籤找到更符合你的需求的老婆"
    )
    async def waifu(self, i: Interaction, many: int = 0, sese: int = 0, tags: int = 0):
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if i.channel.guild is not None and not i.channel.nsfw and sese == 1:
            return await i.followup.send(
                embed=error_embed().set_author(
                    name="請先開啟此頻道的年齡限制設定", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        is_nsfw = "True" if sese == 1 else "False"
        if tags == 1:
            view = WaifuImTag.View(
                await get_waifu_im_tags(sese, self.bot.session), i.user
            )
            await i.followup.send(view=view)
            await view.wait()
            if len(view.tags) == 0:
                return
        async with WaifuAioClient() as wf:
            wf: WaifuAioClient
            if many == 0:
                if tags == 1:
                    try:
                        image = await wf.random(
                            is_nsfw=[is_nsfw], selected_tags=view.tags[0]
                        )
                    except waifuim.exceptions.APIException:
                        return await i.edit_original_response(
                            embed=error_embed(
                                message="您所指定的老婆條件要求太高\n請試試別的標籤"
                            ).set_author(
                                name="找不到老婆", icon_url=i.user.display_avatar.url
                            ),
                            view=None,
                        )
                else:
                    image = await wf.random(is_nsfw=[is_nsfw])
                if sese == 1:
                    async with self.bot.session.get(str(image)) as resp:
                        bytes_obj = io.BytesIO(await resp.read())
                    image = Image.open(bytes_obj)
                    image = image.convert("RGBA")
                    fp = io.BytesIO()
                    image.save(fp, "PNG", optimize=True, quality=10)
                    fp.seek(0)
                    file = File(bytes_obj, filename="waifu_image.png", spoiler=True)
                    try:
                        if tags == 1:
                            await i.edit_original_response(
                                attachments=[file], view=None
                            )
                        else:
                            await i.followup.send(file=file)
                    except HTTPException as e:
                        if e.code == 40005:
                            await i.channel.send(
                                embed=default_embed(message=image).set_author(
                                    name=text_map.get(532, i.locale, user_locale),
                                    icon_url=i.user.display_avatar.url,
                                ),
                            )
                else:
                    embed = default_embed("您的老婆已送達")
                    embed.set_image(url=image)
                    if tags == 1:
                        await i.edit_original_response(embed=embed, view=None)
                    else:
                        await i.followup.send(embed=embed)

            else:
                if tags == 1:
                    try:
                        images = await wf.random(
                            is_nsfw=[is_nsfw], many=True, selected_tags=view.tags[0]
                        )
                    except waifuim.exceptions.APIException:
                        return await i.edit_original_response(
                            embed=error_embed(
                                message="您所指定的老婆條件要求太高\n請試試別的標籤"
                            ).set_author(
                                name="找不到老婆", icon_url=i.user.display_avatar.url
                            ),
                            view=None,
                        )
                else:
                    images = await wf.random(is_nsfw=[is_nsfw], many=True)
                if sese == 1:
                    if not isinstance(images, List):
                        images = [images]

                    for index, image in enumerate(images):
                        if index > 5:
                            break
                        async with self.bot.session.get(str(images[index])) as resp:
                            bytes_obj = io.BytesIO(await resp.read())
                            image = Image.open(bytes_obj)
                            image = image.convert("RGBA")
                            fp = io.BytesIO()
                            image.save(fp, "PNG", optimize=True, quality=10)
                            fp.seek(0)
                            file = File(fp, filename="waifu_image.png", spoiler=True)
                        if index == 0:
                            await (await i.original_response()).delete()
                        try:
                            await i.channel.send(file=file)
                        except HTTPException as e:
                            if e.code == 40005:
                                await i.channel.send(
                                    embed=default_embed(message=image).set_author(
                                        name=text_map.get(532, i.locale, user_locale),
                                        icon_url=i.user.display_avatar.url,
                                    ),
                                )
                else:
                    embeds = []
                    count = 0
                    for image in images:
                        count += 1
                        embed = default_embed(f"{i.user.display_name} 的後宮")
                        embed.set_image(url=image)
                        embed.set_footer(text=f"第 {count}/{len(images)} 位老婆")
                        embeds.append(embed)
                    await GeneralPaginator(i, embeds, self.bot.db).start(followup=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WaifuCog(bot))
