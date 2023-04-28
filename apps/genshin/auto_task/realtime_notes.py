import asyncio
from multiprocessing import Manager
from typing import Dict, Optional, Union

import genshin
import sentry_sdk
from discord import Forbidden, User
from discord.utils import format_dt

import apps.db.tables as tables
import dev.asset as asset
from apps.text_map import text_map
from dev.enum import NotificationType
from dev.models import BotModel, DefaultEmbed, ErrorEmbed
from utils import log
from utils.general import get_dt_now


class RealtimeNotes:
    def __init__(self, bot: BotModel) -> None:
        self.bot = bot

        self._total: Dict[NotificationType, int] = {}
        self._success: Dict[NotificationType, int] = {}
        self._notes_dict: Dict[int, genshin.models.Notes] = Manager().dict()  # type: ignore

    async def start(self) -> None:
        log.info("[RealtimeNotes] Starting...")

        try:
            # Create the queue of notifications
            queue: asyncio.Queue[
                Union[
                    tables.ResinNotification,
                    tables.PotNotification,
                    tables.PtNotification,
                ]
            ] = asyncio.Queue()

            # Make the queue
            tasks = [asyncio.create_task(self._make_queue(queue))]
            tasks.append(asyncio.create_task(self._get_realtime_notes(queue)))
            await asyncio.gather(*tasks)
        except Exception as e:  # skipcq: PYL-W0703
            log.warning(f"[RealtimeNotes] {e}", exc_info=True)
            sentry_sdk.capture_exception(e)
        finally:
            log.info("[RealtimeNotes] Finished")

    async def _make_queue(
        self,
        queue: asyncio.Queue[
            Union[
                tables.ResinNotification, tables.PotNotification, tables.PtNotification
            ]
        ],
    ) -> None:
        """
        Retrieves users from the database for each notification type that is toggled on,
        creates the corresponding notification objects, and adds them to the provided queue.

        Args:
            queue (asyncio.Queue): An asyncio queue that stores ResinNotification, PotNotification,
                or PtNotification objects.

        Returns:
            None.
        """
        # Retrieve users from the database
        resin = await self.bot.pool.fetch(
            "SELECT * FROM resin_notification WHERE toggle=true"
        )
        pot = await self.bot.pool.fetch(
            "SELECT * FROM pot_notification WHERE toggle=true"
        )
        pt = await self.bot.pool.fetch(
            "SELECT * FROM pt_notification WHERE toggle=true"
        )

        # Create notification objects
        resin = [tables.ResinNotification(**r) for r in resin]
        pot = [tables.PotNotification(**p) for p in pot]
        pt = [tables.PtNotification(**p) for p in pt]

        # Add notification objects to the queue
        users = resin + pot + pt
        for user in users:
            self._total[user.type] = self._total.get(user.type, 0) + 1
            await queue.put(user)

        # Log the number of users added to the queue
        log.info(f"[RealtimeNotes] Queue made with {queue.qsize()} users")

    async def _get_realtime_notes(
        self,
        queue: asyncio.Queue[
            Union[
                tables.ResinNotification, tables.PotNotification, tables.PtNotification
            ]
        ],
    ) -> None:
        """
        Retrieve and send Genshin Impact realtime notes to users.

        Args:
            queue: An asyncio queue of notification objects to process.

        Returns:
            None
        """

        # Process notifications in the queue
        while not queue.empty():
            notif_user = await queue.get()

            # Check if the notes have been cached
            if notif_user.uid in self._notes_dict:
                continue

            # Fetch user account details
            user = await self.bot.pool.fetchrow(
                """
                SELECT * FROM user_accounts
                WHERE uid = $1
                AND user_id = $2
                AND ltuid IS NOT NULL
                AND ltoken IS NOT NULL
                AND cookie_token IS NOT NULL
                """,
                notif_user.uid,
                notif_user.user_id,
            )

            # Skip user if no account found
            if user is None:
                continue

            # Create a user account object
            user = tables.UserAccount(**user)

            # Fetch user's language preference
            locale = await user.fetch_lang(self.bot.pool)

            # Set default locale to en-US if no preference found
            if locale is None:
                locale = "en-US"

            # Fetch Discord user object associated with the user account
            discord_user = await user.fetch_discord_user(self.bot)

            try:
                # Retrieve the latest notes from Genshin Impact API
                notes = await user.client.get_genshin_notes(user.uid)
            except Exception as e:  # skipcq: PYL-W0703
                # Disable notifications and create error embed if API request fails
                await self._disable_notif(notif_user)
                await self._reset_current(notif_user)
                embed = await self._create_error_embed(notif_user.type, locale, e)
                if embed:
                    await self._send_notif(discord_user, embed)
            else:
                # Cache the latest notes
                self._notes_dict[user.uid] = notes
                self._success[notif_user.type] = (
                    self._success.get(notif_user.type, 0) + 1
                )

                # Check if the threshold is exceeded and reset the notification counter if necessary
                check = await self._check_notes(notif_user)
                if check and notif_user.current < notif_user.max:
                    # Send the notification and update the notification counter
                    embed = self._create_notif_embed(
                        notif_user.type, notif_user.uid, notes, discord_user, locale
                    )
                    await self._send_notif(discord_user, embed)
                    await self._update_current(notif_user)
                    await self._update_last_notif(notif_user)
                elif not check and notif_user.current != 0:
                    # Reset the notification counter if the user's current amount is less than the threshold
                    await self._reset_current(notif_user)
            finally:
                # Wait for 1.5 seconds before processing the next notification
                await asyncio.sleep(1.5)

    @staticmethod
    async def _create_error_embed(
        notif_type: NotificationType, locale: str, e: Exception
    ) -> Optional[ErrorEmbed]:
        """
        Create and return an ErrorEmbed based on the given notification type, locale,
        and exception object.

        Args:
            notif_type (NotificationType): The type of notification that caused the error.
            locale (str): The locale code to use for the error message.
            e (Exception): The exception object that caused the error.

        Returns:
            Optional[ErrorEmbed]: An ErrorEmbed object if the error message should be
            sent to the user, otherwise None.

        """
        # Initialize an ErrorEmbed object.
        embed = ErrorEmbed()

        # Get the map hash for the given notification type.
        if notif_type is NotificationType.RESIN:
            map_hash = 582
        elif notif_type is NotificationType.POT:
            map_hash = 584
        elif notif_type is NotificationType.PT:
            map_hash = 704

        # Set the author of the ErrorEmbed to the appropriate text based on the map hash
        # and locale.
        embed.set_author(name=text_map.get(map_hash, locale))

        # Determine the title and description of the ErrorEmbed based on the type of
        # exception that occurred.
        if isinstance(e, genshin.InvalidCookies):
            title_hash = 36
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
        # and locale.
        embed.title = text_map.get(title_hash, locale)

        # Return the ErrorEmbed object.
        return embed

    async def _check_notes(
        self,
        notif_user: tables.NotifBase,
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
            isinstance(notif_user, tables.ResinNotification)
            and notes.current_resin < notif_user.threshold
        ):
            return False
        if (
            isinstance(notif_user, tables.PotNotification)
            and notes.current_realm_currency < notif_user.threshold
        ):
            return False
        if isinstance(notif_user, tables.PtNotification) and (
            notes.remaining_transformer_recovery_time is None
            or notes.remaining_transformer_recovery_time.total_seconds() > 0
        ):
            return False

        return True

    @staticmethod
    def _create_notif_embed(
        notif_type: NotificationType,
        uid: int,
        notes: genshin.models.Notes,
        user: User,
        locale: str,
    ) -> DefaultEmbed:
        """
        Creates and returns a notification embed based on the notification type and user data.

        Args:
            notif_type (NotificationType): The type of notification.
            uid (int): The Genshin Imapct UID.
            notes (genshin.models.Notes): The user's notes.
            user (User): The user.
            locale (str): The user's locale.

        Returns:
            DefaultEmbed: The notification embed.
        """

        if notif_type is NotificationType.RESIN:
            if notes.current_resin == notes.max_resin:
                remain_time = text_map.get(1, locale)  # "Full"
            else:
                remain_time = format_dt(notes.resin_recovery_time, "R")

            embed = DefaultEmbed(
                description=f"""
                {text_map.get(303, locale)}: {notes.current_resin}/{notes.max_resin}  # "Current Resin"
                {text_map.get(15, locale)}: {remain_time}  # "Recovery Time"
                UID: {uid}
                """,
            )
            embed.set_title(306, locale, user)
            embed.set_thumbnail(url=asset.resin_icon)
        elif notif_type is NotificationType.POT:
            if notes.current_realm_currency == notes.max_realm_currency:
                remain_time = text_map.get(1, locale)  # "Full"
            else:
                remain_time = format_dt(notes.realm_currency_recovery_time, "R")

            embed = DefaultEmbed(
                description=f"""
                {text_map.get(102, locale)}: {notes.current_resin}/{notes.max_resin}
                {text_map.get(15, locale)}: {remain_time}
                UID: {uid}
                """,
            )
            embed.set_title(518, locale, user)
            embed.set_thumbnail(url=asset.realm_currency_icon)
        elif notif_type is NotificationType.PT:
            embed = DefaultEmbed(description=f"UID: {uid}")
            embed.set_title(366, locale, user)
            embed.set_thumbnail(url=asset.pt_icon)

        embed.set_footer(text=text_map.get(305, locale))
        return embed

    @staticmethod
    async def _send_notif(user: User, embed: Union[DefaultEmbed, ErrorEmbed]) -> None:
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

    @staticmethod
    def _get_table_name(notif_type: NotificationType):
        if notif_type is NotificationType.RESIN:
            table_name = "resin_notification"
        elif notif_type is NotificationType.POT:
            table_name = "pot_notification"
        elif notif_type is NotificationType.PT:
            table_name = "pt_notification"
        return table_name

    async def _disable_notif(
        self,
        notif_user: tables.NotifBase,
    ) -> None:
        table_name = self._get_table_name(notif_user.type)
        await self.bot.pool.execute(
            f"""
            UPDATE {table_name}
            SET toggle = FALSE
            WHERE uid = $1
            AND user_id = $2""",
            notif_user.uid,
            notif_user.user_id,
        )

    async def _reset_current(
        self,
        notif_user: tables.NotifBase,
    ) -> None:
        table_name = self._get_table_name(notif_user.type)
        await self.bot.pool.execute(
            f"""
            UPDATE {table_name}
            SET current = 0
            WHERE uid = $1
            AND user_id = $2""",
            notif_user.uid,
            notif_user.user_id,
        )

    async def _update_current(
        self,
        notif_user: Union[
            tables.ResinNotification, tables.PotNotification, tables.PtNotification
        ],
    ) -> None:
        table_name = self._get_table_name(notif_user.type)
        await self.bot.pool.execute(
            f"""
            UPDATE {table_name}
            SET current = current + 1
            WHERE uid = $1
            AND user_id = $2""",
            notif_user.uid,
            notif_user.user_id,
        )

    async def _update_last_notif(self, notif_user: tables.NotifBase) -> None:
        now = get_dt_now()

        table_name = self._get_table_name(notif_user.type)
        await self.bot.pool.execute(
            f"""
            UPDATE {table_name}
            SET last_notif = $1
            WHERE uid = $2
            AND user_id = $3""",
            now,
            notif_user.uid,
            notif_user.user_id,
        )
