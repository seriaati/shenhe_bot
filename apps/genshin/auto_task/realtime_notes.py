import asyncio
from datetime import timedelta
from typing import Dict, List, Optional, Union

import genshin
import sentry_sdk
from discord import Forbidden, User
from discord.utils import format_dt

import dev.asset as asset
from apps.db.tables.notes_notif import NotifBase, PotNotif, PTNotif, ResinNotif
from apps.text_map import text_map
from dev.enum import NotifType
from dev.exceptions import AccountNotFound
from dev.models import BotModel, DefaultEmbed, ErrorEmbed
from utils import log
from utils.general import get_dc_user, get_dt_now


class RealtimeNotes:
    def __init__(self, bot: BotModel) -> None:
        self.bot = bot

        self._total: Dict[NotifType, int] = {}
        self._success: Dict[NotifType, int] = {}
        self._notes_dict: Dict[int, genshin.models.Notes] = {}

    async def start(self) -> None:
        """Start the RealtimeNotes process.

        This function retrieves all users with notifications enabled and their associated accounts,
        and checks for new Genshin Impact API notes for each user. If a new note is found and the
        notification threshold has been exceeded, a notification is sent to the user via Discord.
        If an error occurs during the process, the error is logged and the exception is captured by Sentry.

        Raises:
            None

        Returns:
            None
        """
        log.info("[RealtimeNotes] Starting...")
        try:
            users = await self._get_users()
            await self._check_realtime_notes(users)
        except Exception as e:  # skipcq: PYL-W0703
            log.exception(f"[RealtimeNotes] Error: {e}")
            sentry_sdk.capture_exception(e)
            owner = self.bot.get_user(self.bot.owner_id) or await self.bot.fetch_user(
                self.bot.owner_id
            )
            await owner.send(f"An error occurred in RealtimeNotes:\n```\n{e}\n```")
        finally:
            for notif_type, total in self._total.items():
                success = self._success.get(notif_type, 0)
                log.info(f"[RealtimeNotes] {notif_type.name}: {success}/{total} sent")
            log.info("[RealtimeNotes] Finished")

    async def _get_users(self) -> List[NotifBase]:
        """
        Retrieve users from the database.

        Args:
            None

        Returns:
            List[NotifBase]: A list of notification objects to process.
        """
        result = []
        # Retrieve users from the database
        resin = await self.bot.db.notifs.resin.get_all()
        pot = await self.bot.db.notifs.pot.get_all()
        pt = await self.bot.db.notifs.pt.get_all()

        # Add notification objects to the result list
        users = resin + pot + pt
        for user in users:
            result.append(user)
            self._total[user.type] = self._total.get(user.type, 0) + 1

        return result

    async def _check_realtime_notes(
        self,
        users: List[NotifBase],
    ) -> None:
        """Check for new Genshin Impact API notes and send notifications to users if necessary.

        This function checks for new notes from the Genshin Impact API for each user in the given list.
        If a user has notifications enabled for the type of note being checked and the notification
        threshold has been exceeded, a notification is sent to the user via Discord.

        Args:
            users: A list of NotifBase objects representing the users to check for notifications.

        Returns:
            None

        Raises:
            ValueError: If an invalid notification type is encountered.
        """
        for notif_user in users:
            # Fetch user account details
            try:
                user = await self.bot.db.users.get(notif_user.user_id, notif_user.uid)
            except AccountNotFound:
                continue

            if notif_user.type is NotifType.RESIN:
                db = self.bot.db.notifs.resin
            elif notif_user.type is NotifType.POT:
                db = self.bot.db.notifs.pot
            elif notif_user.type is NotifType.PT:
                db = self.bot.db.notifs.pt
            else:
                raise ValueError("Invalid notification type")

            # Fetch user's language preference
            lang = (await user.settings).lang or "en-US"

            # Fetch Discord user object associated with the user account
            dc_user = await get_dc_user(self.bot, user.user_id)

            try:
                # Retrieve the latest notes from Genshin Impact API
                if user.uid in self._notes_dict:
                    notes = self._notes_dict[user.uid]
                else:
                    client = await user.client
                    notes = await client.get_genshin_notes(user.uid)
            except Exception as e:  # skipcq: PYL-W0703
                # Disable notifications and create error embed if API request fails
                await db.update(user.user_id, user.uid, toggle=False, current=0)
                embed = await self._create_error_embed(notif_user.type, lang, e)
                if embed:
                    await self._send_notif(dc_user, embed, notif_user.type)
            else:
                # Cache the latest notes
                if user.uid not in self._notes_dict:
                    self._notes_dict[user.uid] = notes

                # Check if the threshold is exceeded and reset the notification counter if necessary
                check = await self._check_notes(notif_user)
                now = get_dt_now()
                if check and notif_user.current < notif_user.max:
                    if (
                        notif_user.last_notif is not None
                        and now - notif_user.last_notif < timedelta(hours=2)
                    ):
                        continue

                    # Send the notification and update the notification counter
                    embed = self._create_notif_embed(
                        notif_user.type, notif_user.uid, notes, dc_user, lang
                    )
                    await self._send_notif(dc_user, embed, notif_user.type)
                    await db.update(
                        user.user_id,
                        user.uid,
                        current=notif_user.current + 1,
                        last_notif=get_dt_now(),
                    )
                elif not check and notif_user.current != 0:
                    # Reset the notification counter if the user's current amount is less than the threshold
                    await db.update(user.user_id, user.uid, current=0)
            finally:
                # Wait for 1.5 seconds before processing the next notification
                await asyncio.sleep(1.5)

    @staticmethod
    async def _create_error_embed(
        notif_type: NotifType, lang: str, e: Exception
    ) -> Optional[ErrorEmbed]:
        """
        Create and return an ErrorEmbed based on the given notification type, lang,
        and exception object.

        Args:
            notif_type (NotificationType): The type of notification that caused the error.
            lang (str): The lang code to use for the error message.
            e (Exception): The exception object that caused the error.

        Returns:
            Optional[ErrorEmbed]: An ErrorEmbed object if the error message should be
            sent to the user, otherwise None.

        """
        # Initialize an ErrorEmbed object.
        embed = ErrorEmbed()

        # Get the map hash for the given notification type.
        if notif_type is NotifType.RESIN:
            map_hash = 582
        elif notif_type is NotifType.POT:
            map_hash = 584
        elif notif_type is NotifType.PT:
            map_hash = 704
        else:
            raise AssertionError("Invalid notification type")

        # Set the author of the ErrorEmbed to the appropriate text based on the map hash
        # and lang.
        embed.set_author(name=text_map.get(map_hash, lang))

        # Determine the title and description of the ErrorEmbed based on the type of
        # exception that occurred.
        if isinstance(e, genshin.InvalidCookies):
            title_hash = 36
            embed.description = text_map.get(767, lang)
        elif isinstance(e, genshin.GenshinException):
            if e.retcode == 1009:
                return None
            title_hash = 10
            embed.description = f"```\n{e.msg}\n```"
        elif isinstance(e, (genshin.errors.InternalDatabaseError, OSError)):
            return None
        else:
            title_hash = 135
            embed.description = f"```\n{e}\n```"
            sentry_sdk.capture_exception(e)

        # Set the title of the ErrorEmbed to the appropriate text based on the title hash
        # and lang.
        embed.title = text_map.get(title_hash, lang)
        if embed.description is None:
            embed.description = ""
        embed.description += f"\n\n{text_map.get(631, lang)}"

        # Return the ErrorEmbed object.
        return embed

    async def _check_notes(
        self,
        notif_user: NotifBase,
    ) -> bool:
        """
        Check whether a notification should be triggered based on the notes for the
        specified user.

        Args:
            notif_user (tables.NotifBase): A notification user for whom to check notes.

        Returns:
            bool: True if the notification should be triggered, False otherwise.
        """
        notes = self._notes_dict[notif_user.uid]
        if (
            isinstance(notif_user, ResinNotif)
            and notes.current_resin < notif_user.threshold
        ):
            return False
        if (
            isinstance(notif_user, PotNotif)
            and notes.current_realm_currency < notif_user.threshold
        ):
            return False
        if isinstance(notif_user, PTNotif) and (
            notes.remaining_transformer_recovery_time is None
            or notes.remaining_transformer_recovery_time.total_seconds() > 0
        ):
            return False

        return True

    @staticmethod
    def _create_notif_embed(
        notif_type: NotifType,
        uid: int,
        notes: genshin.models.Notes,
        user: User,
        lang: str,
    ) -> DefaultEmbed:
        """
        Creates and returns a notification embed based on the notification type and user data.

        Args:
            notif_type (NotificationType): The type of notification.
            uid (int): The Genshin Imapct UID.
            notes (genshin.models.Notes): The user's notes.
            user (User): The user.
            lang (str): The user's lang.

        Returns:
            DefaultEmbed: The notification embed.
        """

        if notif_type is NotifType.RESIN:
            if notes.current_resin == notes.max_resin:
                remain_time = text_map.get(1, lang)  # "Full"
            else:
                remain_time = format_dt(notes.resin_recovery_time, "R")

            embed = DefaultEmbed(
                description=f"""
                {text_map.get(303, lang)}: {notes.current_resin}/{notes.max_resin}
                {text_map.get(15, lang)}: {remain_time}
                UID: {uid}
                """,
            )
            embed.set_title(306, lang, user)
            embed.set_thumbnail(url=asset.resin_icon)
        elif notif_type is NotifType.POT:
            if notes.current_realm_currency == notes.max_realm_currency:
                remain_time = text_map.get(1, lang)  # "Full"
            else:
                remain_time = format_dt(notes.realm_currency_recovery_time, "R")

            embed = DefaultEmbed(
                description=f"""
                {text_map.get(102, lang)}: {notes.current_resin}/{notes.max_resin}
                {text_map.get(15, lang)}: {remain_time}
                UID: {uid}
                """,
            )
            embed.set_title(518, lang, user)
            embed.set_thumbnail(url=asset.realm_currency_icon)
        elif notif_type is NotifType.PT:
            embed = DefaultEmbed(description=f"UID: {uid}")
            embed.set_title(366, lang, user)
            embed.set_thumbnail(url=asset.pt_icon)
        else:
            raise AssertionError("Invalid notification type")

        embed.set_footer(text=text_map.get(305, lang))
        return embed

    async def _send_notif(
        self, user: User, embed: Union[DefaultEmbed, ErrorEmbed], notif_type: NotifType
    ) -> None:
        """
        Sends the notification to the user's DM.

        Args:
            user (User): The user to send the notification to.
            embed (Union[DefaultEmbed, ErrorEmbed]): The embed containing the notification data.
        """
        try:
            await user.send(embed=embed)
        except Forbidden:
            # If the bot is not allowed to send messages to the user's DM,
            # catch the error and do nothing.
            pass
        else:
            if isinstance(embed, DefaultEmbed):
                self._success[notif_type] = self._success.get(notif_type, 0) + 1
