import importlib
import json
import sys

import sentry_sdk
from apps.text_map.text_map_app import text_map
import aiosqlite
from apps.genshin.utils import get_dummy_client
from apps.text_map.convert_locale import to_ambr_top_dict
from discord import Forbidden, Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands
from apps.text_map.utils import get_user_locale
from utility.utils import default_embed, error_embed
from apps.genshin.utils import get_dummy_client
from apps.text_map.convert_locale import to_ambr_top_dict
from data.game.artifacts import artifacts_map
from data.game.characters import characters_map
from data.game.consumables import consumables_map
from data.game.elements import convert_elements
from data.game.weapons import weapons_map


class AdminCog(commands.Cog, name="admin"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_seria():
        async def predicate(i: Interaction) -> bool:
            if i.user.id != 410036441129943050:
                await i.response.send_message(
                    embed=error_embed(message="你不是小雪本人").set_author(
                        name="生物驗證失敗", icon_url=i.user.display_avatar.url
                    ),
                    ephemeral=True,
                )
            return i.user.id == 410036441129943050

        return app_commands.check(predicate)

    @is_seria()
    @app_commands.command(name="reload", description=_("Admin usage only", hash=496))
    @app_commands.rename(module_name="名稱")
    async def realod(self, i: Interaction, module_name: str):
        try:
            importlib.reload(sys.modules[module_name])
        except KeyError:
            return await i.response.send_message(
                embed=error_embed(message=module_name).set_author(
                    name="查無 module", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        else:
            return await i.response.send_message(
                embed=default_embed(message=module_name).set_author(
                    name="重整成功", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )

    @is_seria()
    @app_commands.command(name="sync", description=_("Admin usage only", hash=496))
    async def roles(self, i: Interaction):
        await i.response.defer()
        await self.bot.tree.sync()
        await i.followup.send("sync done")

    @is_seria()
    @app_commands.command(name="status", description=_("Admin usage only", hash=496))
    async def status(self, i: Interaction):
        await i.response.defer()
        embed = default_embed()
        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency*1000)} ms", inline=False
        )
        embed.add_field(
            name="Servers",
            value=f"Connected to {len(self.bot.guilds)} servers",
            inline=False,
        )
        count = 0
        for guild in self.bot.guilds:
            count += len(guild.members)
        embed.add_field(name="Users", value=f"{count} users", inline=False)
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute("SELECT COUNT(user_id) FROM active_users")
        (count,) = await c.fetchone()
        embed.add_field(name="Active Users", value=f"{count} users", inline=False)
        await i.followup.send(embed=embed)

    @is_seria()
    @app_commands.command(name="annouce", description=_("Admin usage only", hash=496))
    async def annouce(
        self, i: Interaction, title: str, description: str, url: str = None
    ):
        await i.response.defer(ephemeral=True)
        c: aiosqlite.Cursor = await i.client.db.cursor()
        await c.execute("SELECT user_id FROM active_users")
        user_ids = await c.fetchall()
        for index, tuple in enumerate(user_ids):
            user_id = tuple[0]
            user = i.client.get_user(user_id)
            if user is None:
                await c.execute(
                    "DELETE FROM active_users WHERE user_id = ?", (user_id,)
                )
                continue
            user_locale = await get_user_locale(user_id, i.client.db)
            seria = i.client.get_user(410036441129943050)
            embed = default_embed(
                title.replace("%n", "\n"), description.replace("%n", "\n")
            )
            embed.set_author(name="seria#5334", icon_url=seria.avatar)
            embed.set_footer(text=text_map.get(524, "zh-TW", user_locale))
            embed.set_image(url=url)
            try:
                await user.send(embed=embed)
            except Forbidden:
                pass
            except Exception as e:
                sentry_sdk.capture_exception(e)
        await i.followup.send("complete.", ephemeral=True)

    @is_seria()
    @app_commands.command(name="update", description=_("Admin usage only", hash=496))
    async def update(self, i: Interaction):
        if i.user.id != 410036441129943050:
            return await i.response.send_message(
                embed=error_embed(message="你不是小雪本人").set_author(
                    name="生物驗證失敗", icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        await i.response.send_message(
            embed=default_embed().set_author(
                name="更新資料開始", icon_url=i.user.display_avatar.url
            )
        )

        client = get_dummy_client()
        client.lang = "zh-tw"

        # artifacts
        result = {}
        artifacts = await client.get_calculator_artifacts()
        for artifact in artifacts:
            if str(artifact.id) in artifacts_map:
                continue
            result[str(artifact.id)] = {
                "name": artifact.name,
                "icon": artifact.icon,
                "ratity": artifact.rarity,
                "artifacts": [],
                "emoji": "",
            }
            other_artifacts = await client.get_complete_artifact_set(artifact.id)
            for other_artifact in other_artifacts:
                result[str(artifact.id)]["artifacts"].append(other_artifact.name)

        result = json.dumps(result, indent=4, sort_keys=True)

        await i.followup.send(
            embed=default_embed(message=f"```py\n{result}\n```").set_author(
                name="聖遺物", icon_url=i.user.display_avatar.url
            )
        )

        # characters
        result = {}
        characters = await client.get_calculator_characters()
        for character in characters:
            if str(character.id) in characters_map:
                continue
            result[str(character.id)] = {
                "name": character.name,
                "icon": character.icon,
                "element": character.element,
                "rarity": character.rarity,
                "emoji": "",
                "eng": "",
            }
        # character english names
        client.lang = "en-us"
        characters = await client.get_calculator_characters()
        for character in characters:
            if str(character.id) in result:
                result[str(character.id)]["eng"] = character.name

        async with self.bot.session.get(f"https://api.ambr.top/v2/cht/avatar") as r:
            characters = await r.json()

        for character_id, character_info in characters["data"]["items"].items():
            if "beta" not in character_info and character_id not in characters_map:
                result[character_id] = {
                    "name": character_info["name"],
                    "icon": f'https://api.ambr.top/assets/UI/{character_info["icon"]}.png',
                    "rarity": character_info["rank"],
                    "emoji": "",
                    "element": convert_elements.get(character_info["element"]),
                    "eng": "",
                }

        async with self.bot.session.get(f"https://api.ambr.top/v2/en/avatar") as r:
            characters = await r.json()

        for character_id, character_info in characters["data"]["items"].items():
            if character_id in result:
                result[character_id]["eng"] = character_info["name"]

        result = json.dumps(result, indent=4, sort_keys=True)

        await i.followup.send(
            embed=default_embed(message=f"```py\n{result}\n```").set_author(
                name="角色", icon_url=i.user.display_avatar.url
            )
        )

        # weapons
        client.lang = "zh-tw"
        result = {}
        weapons = await client.get_calculator_weapons()
        for weapon in weapons:
            if str(weapon.id) in weapons_map:
                continue
            result[str(weapon.id)] = {
                "name": weapon.name,
                "icon": weapon.icon,
                "rarity": weapon.rarity,
                "emoji": "",
                "eng": "",
            }
        client.lang = "en-us"
        weapons = await client.get_calculator_weapons()
        for weapon in weapons:
            if str(weapon.id) in result:
                result[str(weapon.id)]["eng"] = weapon.name

        async with self.bot.session.get(f"https://api.ambr.top/v2/cht/weapon") as r:
            weapons = await r.json()

        for weapon_id, weapon_info in weapons["data"]["items"].items():
            if "beta" not in weapon_info and weapon_id not in weapons_map:
                result[weapon_id] = {
                    "name": weapon_info["name"],
                    "icon": f'https://api.ambr.top/assets/UI/{weapon_info["icon"]}.png',
                    "rarity": weapon_info["rank"],
                    "emoji": "",
                    "eng": "",
                }

        async with self.bot.session.get(f"https://api.ambr.top/v2/en/weapon") as r:
            weapons = await r.json()

        for weapon_id, weapon_info in weapons["data"]["items"].items():
            if weapon_id in result:
                result[weapon_id]["eng"] = weapon_info["name"]

        result = json.dumps(result, indent=4, sort_keys=True)

        await i.followup.send(
            embed=default_embed(message=f"```py\n{result}\n```").set_author(
                name="武器", icon_url=i.user.display_avatar.url
            )
        )

        # check emojis
        message = ""
        for artifact, artifact_info in artifacts_map.items():
            message += artifact_info["emoji"]
        await i.followup.send(
            embed=default_embed(message=message).set_author(
                name="聖遺物 emoji", icon_url=i.user.display_avatar.url
            )
        )

        message = ""
        for character, character_info in characters_map.items():
            message += character_info["emoji"]
        await i.followup.send(
            embed=default_embed(message=message).set_author(
                name="角色 emoji", icon_url=i.user.display_avatar.url
            )
        )

        message = ""
        for weapon, weapon_info in weapons_map.items():
            message += weapon_info["emoji"]
        await i.followup.send(
            embed=default_embed(message=message).set_author(
                name="武器 emoji", icon_url=i.user.display_avatar.url
            )
        )

        messages = []
        message = ""
        for consumable, consumable_info in consumables_map.items():
            if (len(message) + len(consumable_info["emoji"])) > 4096:
                messages.append(message)
                message = ""
            message += consumable_info["emoji"]
        messages.append(message)

        for message in messages:
            await i.followup.send(
                embed=default_embed(message=message).set_author(
                    name="素材 emoji", icon_url=i.user.display_avatar.url
                )
            )

        await i.followup.send(
            embed=default_embed().set_author(
                name="更新資料完畢", icon_url=i.user.display_avatar.url
            )
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot))
