import datetime
import inspect
import itertools
import json
import os
from typing import Optional

import psutil
import pygit2
from aioimgur import ImgurClient
from discord import Attachment, Interaction, app_commands, utils
from discord.app_commands import Choice
from discord.app_commands import locale_str as _
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

import asset
from ambr.client import AmbrTopAPI
from ambr.models import Character
from apps.genshin.custom_model import OriginalInfo, ShenheBot
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from UI_elements.others import Feedback, ManageAccounts, SettingsMenu
from UI_elements.others.settings import CustomImage
from utility.utils import default_embed, error_embed

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
        async with self.bot.pool.acquire() as db:
            await db.execute(
                "INSERT INTO user_settings (user_id) VALUES (?) ON CONFLICT DO NOTHING",
                (i.user.id,),
            )
            await db.commit()

        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale

        embed = default_embed(
            message=f"**{asset.settings_emoji} {text_map.get(539, locale)}**\n\n{text_map.get(534, locale)}"
        )
        view = SettingsMenu.View(locale)

        await i.response.send_message(embed=embed, view=view)
        view.message = await i.original_response()
        view.author = i.user
        view.original_info = OriginalInfo(
            view=view, embed=embed, children=view.children.copy()
        )

    @app_commands.command(
        name="accounts", description=_("Manage your accounts in Shenhe", hash=544)
    )
    async def accounts_command(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        await ManageAccounts.return_accounts(i)

    @app_commands.command(
        name="credits",
        description=_("Meet the awesome people that helped me!", hash=297),
    )
    async def view_credits(self, i: Interaction):
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
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

    def format_commit(self, commit: pygit2.Commit) -> str:
        short, _, _ = commit.message.partition("\n")
        short_sha2 = commit.hex[0:6]
        commit_tz = datetime.timezone(
            datetime.timedelta(minutes=commit.commit_time_offset)
        )
        commit_time = datetime.datetime.fromtimestamp(commit.commit_time).astimezone(
            commit_tz
        )

        # [`hash`](url) message (offset)
        offset = utils.format_dt((commit_time.astimezone(datetime.timezone.utc)), "R")
        return f"[`{short_sha2}`](https://github.com/seriaati/shenhe_bot/commit/{commit.hex}) {short} ({offset})"

    def get_last_commits(self, count: int = 5):
        repo = pygit2.Repository(".git")
        commits = list(
            itertools.islice(
                repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL), count
            )
        )
        return "\n".join(self.format_commit(c) for c in commits)

    @app_commands.command(name="info", description=_("View the bot's info", hash=63))
    async def view_bot_info(self, i: Interaction):
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale

        revision = self.get_last_commits()
        embed = default_embed("申鶴 | Shenhe", f"{text_map.get(296, locale)}\n{revision}")

        seria = self.bot.get_user(410036441129943050) or await self.bot.fetch_user(
            410036441129943050
        )
        embed.set_author(name=str(seria), icon_url=seria.display_avatar.url)

        process = psutil.Process()
        memory_usage = process.memory_full_info().uss / 1024**2  # type: ignore
        cpu_usage = process.cpu_percent() / psutil.cpu_count()  # type: ignore
        embed.add_field(
            name=text_map.get(349, locale),
            value=f"{memory_usage:.2f} MB\n{cpu_usage:.2f}% CPU",
        )

        async with self.bot.pool.acquire() as db:
            async with db.execute("SELECT COUNT(*) FROM user_accounts") as cursor:
                total = await cursor.fetchone()
                await cursor.execute(
                    "SELECT COUNT(*) FROM user_accounts WHERE ltuid IS NOT NULL"
                )
                cookie = await cursor.fetchone()
                await cursor.execute(
                    "SELECT COUNT(*) FROM user_accounts WHERE china = 1"
                )
                china = await cursor.fetchone()
                embed.add_field(
                    name=text_map.get(524, locale),
                    value=text_map.get(194, locale).format(
                        total=total[0], cookie=cookie[0], china=china[0]
                    ),
                )

        total_members = 0
        total_unique = len(self.bot.users)

        guilds = 0
        for guild in self.bot.guilds:
            guilds += 1
            if guild.unavailable:
                continue
            total_members += guild.member_count or 0

        embed.add_field(
            name=text_map.get(528, locale),
            value=text_map.get(566, locale).format(
                total=total_members, unique=total_unique
            ),
        )

        embed.add_field(
            name=text_map.get(503, locale),
            value=str(guilds),
        )
        embed.add_field(
            name=text_map.get(564, locale),
            value=f"{round(self.bot.latency*1000, 2)} ms",
        )

        delta_uptime = datetime.datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed.add_field(
            name=text_map.get(147, locale),
            value=f"{days}d {hours}h {minutes}m {seconds}s",
        )

        view = View()
        view.add_item(
            Button(
                label=text_map.get(642, locale),
                url="https://discord.gg/ryfamUykRw",
                emoji=asset.discord_emoji,
            )
        )
        view.add_item(
            Button(
                label="GitHub",
                url="https://github.com/seriaati/shenhe_bot",
                emoji=asset.github_emoji,
            )
        )
        await i.response.send_message(embed=embed, view=view)

    @app_commands.command(
        name="img-upload",
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
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
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
        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        options = []
        for character_id, character_names in self.avatar.items():
            if current.lower() in character_names[to_ambr_top(locale)].lower():
                options.append(
                    Choice(
                        name=character_names[to_ambr_top(locale)], value=character_id
                    )
                )
        return options[:25]

    @app_commands.command(
        name="feedback", description=_("Send feedback to the bot developer", hash=723)
    )
    async def feedback(self, i: Interaction):
        await i.response.send_modal(
            Feedback.FeedbackModal(
                await get_user_locale(i.user.id, i.client.pool) or i.locale
            )
        )

    @app_commands.command(
        name="source", description=_("View the bot source code", hash=739)
    )
    @app_commands.rename(command=_("command", hash=742))
    @app_commands.describe(command=_("Name of command to view the source code of", hash=743))
    async def source(self, i: Interaction, command: Optional[str] = None):
        source_url = "https://github.com/seriaati/shenhe_bot"
        branch = "main"

        if not command:
            return await i.response.send_message(f"<{source_url}>")

        locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
        obj = self.bot.tree.get_command(command)
        if obj is None:
            return await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(740, locale), icon_url=i.user.display_avatar.url
                )
            )

        assert isinstance(obj, app_commands.commands.Command)

        src = obj.callback.__code__
        module = obj.callback.__module__
        filename = src.co_filename

        lines, firstlineno = inspect.getsourcelines(src)
        if not module.startswith("discord"):
            if filename is None:
                return await i.response.send_message(
                    embed=error_embed().set_author(
                        name=text_map.get(741, locale),
                        icon_url=i.user.display_avatar.url,
                    )
                )

            location = os.path.relpath(filename).replace("\\", "/")
        else:
            location = module.replace(".", "/") + ".py"
            source_url = "https://github.com/Rapptz/discord.py"
            branch = "master"

        final_url = f"<{source_url}/blob/{branch}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        await i.response.send_message(final_url)
    
    @source.autocomplete(name="command")
    async def source_autocomplete(self, i: Interaction, current: str):
        options = []
        for command in self.bot.tree.get_commands():
            if current.lower() in command.name.lower():
                options.append(Choice(name=command.name, value=command.name))
        return options[:25]


async def setup(bot: commands.AutoShardedBot) -> None:
    await bot.add_cog(OthersCog(bot))
