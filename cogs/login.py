import os

import asyncpg
from discord import HTTPException
from discord.ext import commands
from dotenv import load_dotenv
from logingateway import HuTaoLoginAPI
from logingateway.model import (
    AccountToken,
    Genshin,
    LoginMethod,
    Player,
    Ready,
    ServerId,
)

from apps.text_map import text_map
from models import ShenheBot
from utility import DefaultEmbed, log

load_dotenv()


class LoginGatewayCog(commands.Cog):
    def __init__(self, bot: ShenheBot) -> None:
        self.bot = bot
        self.gateway = HuTaoLoginAPI(
            client_id=os.getenv("HUTAO_CLIENT_ID", ""),
            client_secret=os.getenv("HUTAO_CLIENT_SECRET", ""),
        )

        # Event
        self.gateway.ready(self.gateway_connect)
        self.gateway.player(self.gateway_player)
        self.gateway.player_update(self.gateway_player_update)

        # Start gateway
        if not self.bot.debug:
            log.info("[System][LoginGateway] Starting gateway...")
            self.gateway.start()

        self.bot.gateway = self.gateway

    async def cog_unload(self):
        if not self.bot.debug:
            log.info("[System][LoginGateway] Closing gateway...")
            await self.gateway.close()

    @staticmethod
    async def gateway_connect(_: Ready):
        log.info("[System][LoginGateway] Gateway connected")

    async def gateway_player_update(self, data: Player):
        log.info(f"[System][LoginGateway][PlayerUpdate] Recieved data: {data.genshin}")

        user_id = data.discord.user_id
        genshin = data.genshin
        uid = data.genshin.uid

        await self.bot.pool.execute(
            """
            UPDATE user_accounts
            SET ltuid = $1, cookie_token = $2, ltoken = $3
            WHERE user_id = $4 AND uid = $5
            """,
            genshin.ltuid,
            genshin.cookie_token,
            genshin.ltoken,
            int(user_id),
            int(uid),
        )

    async def gateway_player(self, data: Player):
        if data.token not in self.bot.tokenStore:
            return

        log.info(f"[System][LoginGateway][Player] Recieved data: {data}")
        ctx = self.bot.tokenStore[data.token]
        uid = data.genshin.uid
        user_id = data.discord.user_id
        await register_user(data.genshin, int(uid), int(user_id), self.bot.pool)

        try:
            await ctx["message"].edit(
                embed=DefaultEmbed().set_author(
                    name=text_map.get(39, ctx["locale"]),
                    icon_url=ctx["author"].display_avatar.url,
                ),
                view=None,
            )
        except HTTPException:
            pass


async def setup(client: ShenheBot):
    await client.add_cog(LoginGatewayCog(client))


async def register_user(
    data: Genshin | AccountToken, uid: int, user_id: int, pool: asyncpg.Pool
):
    """Register user to database"""
    if data.login_type == LoginMethod.UID:
        cookie = {
            "ltuid": None,
            "ltoken": None,
            "cookie_token": None,
        }
    else:
        cookie = {
            "ltuid": data.ltuid,
            "ltoken": data.ltoken,
            "cookie_token": data.cookie_token,
        }

    china = data.server is ServerId.CHINA
    await pool.execute(
        """
        UPDATE user_accounts
        SET current = false
        WHERE user_id = $1
        """,
        user_id,
    )
    await pool.execute(
        """
        INSERT INTO user_accounts
        (uid, user_id, ltuid, ltoken, cookie_token, china)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (uid, user_id)
        DO UPDATE SET
        ltuid = $3,
        ltoken = $4,
        cookie_token = $5
        """,
        uid,
        user_id,
        cookie["ltuid"],
        cookie["ltoken"],
        cookie["cookie_token"],
        china,
    )
