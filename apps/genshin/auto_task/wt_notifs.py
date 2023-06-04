import asyncio
from datetime import timedelta
from io import BytesIO
from typing import Any, Dict, List, Tuple, Union

import sentry_sdk
from discord import File, Forbidden

import ambr.models as ambr
from ambr.client import AmbrTopAPI
from apps.db.tables.talent_notif import TalentNotif, WeaponNotif
from apps.db.tables.user_settings import Settings
from apps.draw.main_funcs import draw_material_card
from apps.text_map import text_map
from apps.text_map.convert_locale import to_ambr_top
from dev.enum import NotifType
from dev.exceptions import AccountNotFound
from dev.models import BotModel, DefaultEmbed, DrawInput
from utils import log
from utils.general import get_dt_now
from utils.genshin import get_uid_tz
from utils.text_map import get_city_name


class WTNotifs:
    """Weapon and talent notifications"""

    def __init__(self, bot: BotModel, time_offset: int):
        self.bot = bot

        self.time_offset = time_offset
        self._now = get_dt_now() + timedelta(hours=self.time_offset)

        self._domain_cache: Dict[str, List[ambr.Domain]] = {}
        self._upgrade_cache: Dict[str, ambr.CharacterUpgrade | ambr.WeaponUpgrade] = {}
        self._item_cache: Dict[str, ambr.Weapon | ambr.Character] = {}

        self._success: Dict[NotifType, int] = {}
        self._total: Dict[NotifType, int] = {}

    async def start(self) -> None:
        try:
            log.info(f"[WTNotifs] Executing with time offset {self.time_offset}")

            users = await self._get_users()
            await self._make_notify(users)
        except Exception as e:  # skipcq: PYL-W0703
            log.exception("[WTNotifs] Failed to execute")
            sentry_sdk.capture_exception(e)
            owner = self.bot.get_user(self.bot.owner_id) or await self.bot.fetch_user(
                self.bot.owner_id
            )
            await owner.send(
                f"An error occurred in WTNotifs:\n```\n{e}\n```"
            )  # Send error message to bot owner
        else:
            for notif_type, total in self._total.items():
                success = self._success.get(notif_type, 0)
                log.info(f"[WTNotifs] {notif_type}: {success}/{total} sent")
        finally:
            log.info("[WTNotifs] Finished")

    async def _get_users(self):
        # Get all talent notifications from the database
        talents = await self.bot.db.notifs.talent.get_all()

        # Get all weapon notifications from the database
        weapons = await self.bot.db.notifs.weapon.get_all()

        # Combine the talent and weapon notifications
        users = talents + weapons

        return users

    async def _make_notify(self, users: List[Union[WeaponNotif, TalentNotif]]):
        for user in users:
            try:
                # Add value to the total dict
                self._total[user.type] = self._total.get(user.type, 0) + len(
                    user.item_list
                )
                # Get the user's ID and item list
                user_id = user.user_id
                item_list = user.item_list
                # Get the user's UID and time zone from the database
                try:
                    uid = await self.bot.db.users.get_uid(user_id)
                except AccountNotFound:
                    uid = None
                uid_tz = get_uid_tz(uid)
                # If the user's time zone is not the same as the task's time zone, skip the user
                if uid_tz != self.time_offset:
                    continue

                # Get the user's language from the database
                lang = await self.bot.db.settings.get(user_id, Settings.LANG) or "en-US"
                # Get the domains for the user's language
                domains = self._domain_cache.get(lang)
                if domains is None:
                    domains = await self._get_domains(lang)
                    self._domain_cache[lang] = domains

                notify: Dict[str, Dict[str, Any]] = {}
                # Loop through the user's item list
                for item_id in item_list:
                    # Loop through the domains
                    for domain in domains:
                        # Loop through the rewards for the domain
                        for reward in domain.rewards:
                            # Get the upgrade info for the item
                            upgrade = self._upgrade_cache.get(item_id)
                            if upgrade is None:
                                upgrade = await self._get_upgrade(
                                    item_id, lang, user.type
                                )
                                if upgrade is None:
                                    continue
                                self._upgrade_cache[item_id] = upgrade

                            # If the reward is in the upgrade items, add it to the notification
                            if reward in upgrade.items:
                                if item_id not in notify:
                                    notify[item_id] = {
                                        "materials": [],
                                        "domain": domain,
                                    }
                                if reward not in notify[item_id]["materials"]:
                                    notify[item_id]["materials"].append(reward)

                # Loop through the notifications
                for item_id, item_info in notify.items():
                    # Get item info from the cache
                    item = self._item_cache.get(item_id)
                    if item is None:
                        item = await self._get_item(item_id, lang, user.type)
                        if item is None:
                            continue
                        self._item_cache[item_id] = item

                    # Draw the notification card
                    materials: List[Tuple[ambr.Material, str]] = [
                        (m, "") for m in item_info["materials"]
                    ]
                    fp = await self._draw_card(user.user_id, lang, materials)
                    fp.seek(0)

                    # Get the notification embed
                    embed = self._get_embed(lang, item_info["domain"], item)
                    # Send the notification to the user
                    await self._send_notif(user.user_id, embed, fp, user.type)
            except Exception as e:  # skipcq: PYL-W0703
                # Log and capture any exceptions
                log.exception("[WTNotifs] Failed to get notify", exc_info=e)
                sentry_sdk.capture_exception(e)
            finally:
                # Sleep for 0.5 seconds to avoid rate limiting
                await asyncio.sleep(0.5)

    async def _get_domains(self, lang: str):
        client = AmbrTopAPI(self.bot.session, to_ambr_top(lang))
        domains = await client.get_domains()
        return [d for d in domains if d.weekday == self._now.weekday()]

    async def _get_upgrade(self, item_id: str, lang: str, notif_type: NotifType):
        client = AmbrTopAPI(self.bot.session, to_ambr_top(lang))
        if notif_type is NotifType.TALENT:
            upgrade = await client.get_character_upgrade(item_id)
        else:  # notif_type is NotifType.WEAPON:
            upgrade = await client.get_weapon_upgrade(int(item_id))

        if not isinstance(upgrade, (ambr.CharacterUpgrade, ambr.WeaponUpgrade)):
            return None
        return upgrade

    async def _get_item(self, item_id: str, lang: str, notif_type: NotifType):
        client = AmbrTopAPI(self.bot.session, to_ambr_top(lang))
        if notif_type is NotifType.TALENT:
            item = await client.get_character(item_id)
        else:
            item = await client.get_weapon(int(item_id))

        if not isinstance(item, (ambr.Character, ambr.Weapon)):
            return None
        return item

    async def _draw_card(
        self, user_id: int, lang: str, materials: List[Tuple[ambr.Material, str]]
    ):
        dark_mode = await self.bot.db.settings.get(user_id, Settings.DARK_MODE)
        fp = await draw_material_card(
            DrawInput(
                loop=self.bot.loop,
                session=self.bot.session,
                lang=lang,
                dark_mode=dark_mode,
            ),
            materials,  # type: ignore
            "",
            draw_title=False,
        )
        return fp

    @staticmethod
    def _get_embed(
        lang: str, domain: ambr.Domain, item: Union[ambr.Character, ambr.Weapon]
    ):
        embed = DefaultEmbed()
        embed.add_field(
            name=text_map.get(609, lang),
            value=f"{domain.name} ({get_city_name(domain.city.id, lang)})",
        )
        embed.set_author(
            name=text_map.get(312, lang).format(name=item.name),
            icon_url=item.icon,
        )
        embed.set_footer(text=text_map.get(134, lang))
        embed.set_image(url="attachment://reminder_card.jpeg")
        return embed

    async def _send_notif(
        self, user_id: int, embed: DefaultEmbed, fp: BytesIO, notif_type: NotifType
    ):
        try:
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
            await user.send(embed=embed, file=File(fp, "reminder_card.jpeg"))
        except Forbidden:
            if notif_type is NotifType.TALENT:
                await self.bot.db.notifs.talent.update(user_id, toggle=False)
            elif notif_type is NotifType.WEAPON:
                await self.bot.db.notifs.weapon.update(user_id, toggle=False)
        else:
            self._success[notif_type] = self._success.get(notif_type, 0) + 1
