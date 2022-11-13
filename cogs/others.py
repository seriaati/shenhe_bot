import json
import sys
from datetime import datetime
from ambr.client import AmbrTopAPI
from ambr.models import Character
import config
import pytz
from discord import Interaction, app_commands, Attachment
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.ui import View, Button
from UI_base_models import BaseView
from apps.genshin.custom_model import ShenheBot
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_elements.others import ManageAccounts, SettingsMenu
from UI_elements.others.settings import CustomImage
from utility.utils import default_embed
from aioimgur import ImgurClient
from dotenv import load_dotenv
import os

load_dotenv()


class OthersCog(commands.Cog, name="others"):
    def __init__(self, bot):
        self.bot: ShenheBot = bot
        try:
            with open(f"text_maps/avatar.json", "r", encoding="utf-8") as f:
                self.avatar = json.load(f)
        except FileNotFoundError:
            self.avatar = {}

    @app_commands.command(
        name="settings",
        description=_("View and change your user settings in Shenhe", hash=534),
    )
    async def settings(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        view = SettingsMenu.View(user_locale or i.locale)
        view.author = i.user
        embed = default_embed(message=text_map.get(534, i.locale, user_locale))
        embed.set_author(
            name=f"⚙️ {text_map.get(539, i.locale, user_locale)}",
            icon_url=i.user.display_avatar.url,
        )
        await i.response.send_message(embed=embed, view=view)
        view.message = await i.original_response()

    @app_commands.command(
        name="accounts", description=_("Manage your accounts in Shenhe", hash=544)
    )
    async def accounts_command(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        await ManageAccounts.return_accounts(i)

    @app_commands.command(
        name="timezone", description=_("View the timezone list", hash=134)
    )
    @app_commands.rename(timezone=_("timezone", hash=186))
    async def view_timezone_list(self, i: Interaction, timezone: str):
        await i.response.send_message(content=timezone, ephemeral=True)

    @view_timezone_list.autocomplete("timezone")
    async def timezone_autocomplete(self, i: Interaction, current: str):
        choices = []
        timezone_list = pytz.all_timezones
        for timezone in timezone_list:
            if current.lower() in timezone.lower():
                choices.append(Choice(name=timezone, value=timezone))
        return choices[:25]

    @app_commands.command(
        name="credits",
        description=_("Meet the awesome people that helped me!", hash=297),
    )
    async def view_credits(self, i: Interaction):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        embed = default_embed(text_map.get(475, locale) + " 🎉")
        kakaka = self.bot.get_user(425140480334888980) or await self.bot.fetch_user(
            425140480334888980
        )
        ginn = self.bot.get_user(489647643342143491) or await self.bot.fetch_user(
            489647643342143491
        )
        fox_fox = self.bot.get_user(274853284764975104) or await self.bot.fetch_user(
            274853284764975104
        )
        tedd = self.bot.get_user(272394461646946304) or await self.bot.fetch_user(
            272394461646946304
        )
        dinnerbone_3rd = self.bot.get_user(
            808396055879090267
        ) or await self.bot.fetch_user(808396055879090267)
        xiaokuai = self.bot.get_user(780643463946698813) or await self.bot.fetch_user(
            780643463946698813
        )
        embed.add_field(
            name=text_map.get(298, locale),
            value=f"{kakaka.mention} - 🇯🇵\n"
            f"{tedd.mention} - 🇯🇵\n"
            f"{ginn.mention} - 🇺🇸\n"
            f"{fox_fox.mention} - 🇺🇸\n"
            f"{dinnerbone_3rd.mention} - 🇨🇳\n"
            f"{xiaokuai.mention} - 🇨🇳",
            inline=False,
        )
        gaurav = self.bot.get_user(327390030689730561) or await self.bot.fetch_user(
            327390030689730561
        )
        kt = self.bot.get_user(153087013447401472) or await self.bot.fetch_user(
            153087013447401472
        )
        algoinde = self.bot.get_user(142949518680391680) or await self.bot.fetch_user(
            142949518680391680
        )
        m_307 = self.bot.get_user(301178730196238339) or await self.bot.fetch_user(
            301178730196238339
        )
        embed.add_field(
            name=text_map.get(466, locale),
            value=f"{gaurav.mention}\n"
            f"{kt.mention}\n"
            f"{algoinde.mention}\n"
            f"{m_307.mention}",
            inline=False,
        )
        embed.add_field(
            name=text_map.get(479, locale),
            value=text_map.get(497, locale),
            inline=False,
        )
        await i.response.send_message(embed=embed)

    @app_commands.command(name="info", description=_("View the bot's info", hash=63))
    async def view_bot_info(self, i: Interaction):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        embed = default_embed(self.bot.user.name)
        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed.add_field(
            name=text_map.get(147, locale),
            value=f"{days}d {hours}h {minutes}m {seconds}s",
            inline=False,
        )
        embed.add_field(
            name=text_map.get(194, locale), value=f"`{sys.version}`", inline=False
        )
        embed.add_field(
            name=text_map.get(503, locale),
            value=str(len(self.bot.guilds)),
            inline=False,
        )
        embed.add_field(
            name=text_map.get(564, locale),
            value=f"{round(self.bot.latency*1000, 2)} ms",
            inline=False,
        )
        embed.add_field(
            name=text_map.get(565, locale),
            value="</credits:1028913972377817129>",
            inline=False,
        )
        embed.add_field(
            name=text_map.get(566, locale),
            value=f"[discord.py](https://github.com/Rapptz/discord.py)\n"
            f"[genshin.py](https://github.com/thesadru/genshin.py)\n"
            f"[Enkanetwork.py](https://github.com/mrwan200/EnkaNetwork.py)\n"
            f"[GGanalysis](https://github.com/OneBST/GGanalysis)\n"
            f"[pyppeteer](https://github.com/pyppeteer/pyppeteer)\n"
            f"[Pillow](https://github.com/python-pillow/Pillow)\n"
            f"[pydantic](https://github.com/pydantic/pydantic)\n"
            f"[aiosqlite](https://github.com/omnilib/aiosqlite)\n"
            f"[matplotlib](https://github.com/matplotlib/matplotlib)\n",
            inline=False,
        )
        embed.add_field(
            name=text_map.get(220, locale),
            value=f"[seria#5334](http://discord.com/users/410036441129943050)",
            inline=False,
        )
        embed.set_thumbnail(url=self.bot.user.avatar.url)
        view = View()
        view.add_item(
            Button(
                label=text_map.get(642, locale),
                url="https://discord.gg/ryfamUykRw",
                emoji="<:discord_icon:1032123254103621632>",
            )
        )
        view.add_item(
            Button(label="GitHub", url="https://github.com/seriaati/shenhe_bot")
        )
        await i.response.send_message(embed=embed, view=view)

    @app_commands.command(
        name="custom-image-upload",
        description=_("Upload a custom image for /profile character cards", hash=68),
    )
    @app_commands.rename(
        image_file=_("image-file", hash=64),
        image_name=_("image-name", hash=86),
        character_id=_("character", hash=105),
    )
    @app_commands.describe(
        image_file=_("The image file to upload", hash=65),
        image_name=_("The nickname for the image", hash=66),
        character_id=_("The character to use the image", hash=67),
    )
    async def custom_image_upload(
        self, i: Interaction, image_file: Attachment, image_name: str, character_id: str
    ):
        await i.response.defer()
        imgur = ImgurClient(
            os.getenv("IMGUR_CLIENT_ID"), os.getenv("IMGUR_CLIENT_SECRET")
        )
        something = await imgur.upload(await image_file.read())
        converted_character_id = int(character_id.split("-")[0])
        await CustomImage.add_user_custom_image(
            i, something["link"], converted_character_id, image_name
        )
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        view = CustomImage.View(locale)
        view.author = i.user
        ambr = AmbrTopAPI(self.bot.session, to_ambr_top(locale))
        character = await ambr.get_character(character_id)
        if not isinstance(character, Character):
            raise TypeError("character is not a Character")
        await CustomImage.return_custom_image_interaction(
            view, i, converted_character_id, character.element
        )

    @custom_image_upload.autocomplete(name="character_id")
    async def custom_image_upload_autocomplete(self, i: Interaction, current: str):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        options = []
        for character_id, character_names in self.avatar.items():
            if current.lower() in character_names[to_ambr_top(locale)].lower():
                options.append(
                    Choice(
                        name=character_names[to_ambr_top(locale)], value=character_id
                    )
                )
        return options[:25]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OthersCog(bot))
