import asyncio
from typing import List

import discord
import genshin
import sentry_sdk

from apps.db.tables.hoyo_account import HoyoAccount
from apps.text_map import text_map
from dev.base_ui import get_error_handle_embed
from dev.enum import GameType
from dev.exceptions import AccountNotFound
from dev.models import BotModel, DefaultEmbed
from utils import log
from utils.general import get_dc_user


class AutoRedeem:
    def __init__(self, bot: BotModel):
        """
        Initializes the AutoRedeem class.

        Args:
            bot (BotModel): The bot instance.
        """
        self.bot = bot

        self._total = 0
        self._success = 0

    async def exec(self) -> None:
        """Execute the AutoRedeem process.

        This function retrieves all codes from the database and processes them for all users.
        If no codes are found, the function will exit early.

        Raises:
            Exception: If an error occurs during the process.

        Returns:
            None
        """
        try:
            log.info("[AutoRedeem] Starting")
            codes = await self.bot.db.codes.get_all()
            if not codes:
                return log.info("[AutoRedeem] No codes found, skipping")

            users = await self._get_users()
            await self._process_users(users, codes)
        except Exception as e:  # skipcq: PYL-W0703
            log.exception(f"[AutoRedeem] {e}")
            sentry_sdk.capture_exception(e)
        else:
            log.info(f"[AutoRedeem] Redeemed for {self._success}/{self._total} users")
        finally:
            log.info("[AutoRedeem] Finished")

    async def _get_users(self) -> List[HoyoAccount]:
        """Retrieve all users with auto-redeem enabled and their associated accounts.

        This function queries the database for all users with auto-redeem enabled and retrieves
        all of their associated accounts for the Genshin Impact game type. If an account is not found
        for a user, the user is skipped.

        Returns:
            A list of HoyoAccount objects representing all accounts associated with users with
            auto-redeem enabled.

        Raises:
            None
        """
        result: List[HoyoAccount] = []
        users = await self.bot.pool.fetch(
            "SELECT user_id FROM user_settings WHERE auto_redeem = true"
        )
        for user in users:
            try:
                accounts = await self.bot.db.users.get_all_of_user(
                    user["user_id"], GameType.GENSHIN
                )
            except AccountNotFound:
                continue
            else:
                result.extend(accounts)
                self._total += 1

        return result

    async def _process_users(self, users: List[HoyoAccount], codes: List[str]) -> None:
        """Process the given codes for the given users.

        This function attempts to redeem the given codes for each user in the list of users.
        If a code is successfully redeemed, an embed is created and sent to the user via Discord.
        If an error occurs during the process, the error is logged and the exception is captured by Sentry.

        Args:
            users: A list of HoyoAccount objects representing the users to process.
            codes: A list of strings representing the codes to redeem.

        Returns:
            None

        Raises:
            None
        """
        for user in users:
            try:
                dc_user = await get_dc_user(self.bot, user.user_id)
                embeds = await self._redeem_codes(user, codes, dc_user)
            except Exception as e:  # skipcq: PYL-W0703
                log.exception(f"[AutoRedeem] {e}")
                sentry_sdk.capture_exception(e)
            else:
                await self.notify_user(dc_user, embeds)
                self._success += 1

    async def _redeem_codes(
        self, account: HoyoAccount, codes: List[str], discord_user: discord.User
    ) -> List[discord.Embed]:
        """
        Redeems all codes for a given user account.

        Args:
            account (HoyoAccount): The user account to redeem codes for.
            codes (List[str]): The list of codes to redeem.
            discord_user (discord.User): The Discord user to notify.

        Returns:
            List[discord.Embed]: The list of embeds to send to the user.
        """
        embeds: List[discord.Embed] = []
        for code in codes:
            log.info(f"[AutoRedeem] Redeeming {code} for {account.uid}")
            redeemed = await self.bot.db.redeemed.check(account.uid, code)
            if redeemed:
                continue

            embed = await self._redeem_code(account, code, discord_user)
            await self.bot.db.redeemed.insert(account.uid, code)
            embeds.append(embed)
            await asyncio.sleep(10.0)

        return embeds

    @staticmethod
    async def _redeem_code(
        account: HoyoAccount, code: str, user: discord.User
    ) -> discord.Embed:
        """
        Redeems a single code for a given user account.

        Args:
            account (HoyoAccount): The user account to redeem the code for.
            code (str): The code to redeem.
            user (discord.User): The Discord user to notify.

        Returns:
            discord.Embed: The embed to send to the user.
        """
        client = await account.client
        lang = (await account.settings).lang or "en-US"
        try:
            await client.redeem_code(code, account.uid, game=genshin.Game.GENSHIN)
        except Exception as e:  # skipcq: PYL-W0703
            embed = get_error_handle_embed(user, e, lang)
        else:
            embed = DefaultEmbed(
                text_map.get(109, lang),
            )
        if embed.description is None:
            embed.description = ""
        embed.description += f"\n\n{text_map.get(108, lang)}: **{code}**"
        embed.set_footer(text=text_map.get(126, lang))
        return embed

    @staticmethod
    async def notify_user(user: discord.User, embeds: List[discord.Embed]) -> None:
        """
        Notifies a user of the redeemed codes.

        Args:
            user (discord.User): The Discord user to notify.
            embeds (List[discord.Embed]): The list of embeds to send to the user.
        """
        if not embeds:
            return

        try:
            await user.send(embeds=embeds)
        except discord.Forbidden:
            pass
