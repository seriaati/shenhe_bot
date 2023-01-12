from apps.genshin.custom_model import ShenheBot

from discord.ext import commands
import asqlite
from logingateway import HuTaoLoginAPI
from logingateway.model import Player, Ready, LoginMethod, ServerId

from utility.utils import default_embed, log

import os
from dotenv import load_dotenv
from discord import HTTPException

from apps.text_map.text_map_app import text_map

load_dotenv()


class LoginGatewayCog(commands.Cog):
    def __init__(self, bot: ShenheBot) -> None:
        self.bot = bot
        self.gateway = HuTaoLoginAPI(
            client_id=os.getenv("HUTAO_CLIENT_ID", ""),
            client_secret=os.getenv("HUTAO_CLIENT_SECRET", ""),
        )
        self.tokenStore = {}

        # Event
        self.gateway.ready(self.gateway_connect)
        self.gateway.player(self.gateway_player)
        self.gateway.player_update(self.gateway_player_update)

        # Start gateway
        if not self.bot.debug:
            log.info("[System][LoginGateway] Starting gateway...")
            self.gateway.start()
        
        self.bot.gateway = self.gateway
        self.bot.tokenStore = self.tokenStore
    
    async def cog_unload(self):
        self.gateway.close()

    async def gateway_connect(self, _: Ready):
        log.info("[System][LoginGateway] Gateway connected")

    async def gateway_player_update(self, data: Player):
        log.info(f"[System][LoginGateway][PlayerUpdate] Recieved data: {data.genshin}")

        # Set variable data
        user_id = data.discord.user_id
        genshin = data.genshin

        # Update cookie_token
        _data = [genshin.ltuid, genshin.cookie_token]

        # Set default value
        update_value = "ltuid = ?, cookie_token = ?"
        # Check if ltoken is not empty string
        if data.genshin.ltoken != "":
            update_value += ", ltoken = ?"
            _data.append(genshin.ltoken)

        # Append discord ID
        _data.append(user_id)
        async with self.bot.pool.acquire() as db:
            await db.execute(
                f"UPDATE user_accounts SET {update_value} WHERE user_id = ?", tuple(_data)
            )
            await db.commit()

    async def gateway_player(self, data: Player):
        if not data.token in self.tokenStore:
            return

        log.info(f"[System][LoginGateway][Player] Recieved data: {data.genshin}")
        ctx = self.tokenStore[data.token]
        log.info(f"[System][Hutao Login Gateway] {data}")
        uid = data.genshin.uid
        user_id = data.discord.user_id
        if data.genshin.login_type == LoginMethod.UID:
            cookie = {
                "ltuid": None,
                "ltoken": None,
                "cookie_token": None,
            }
        else:
            cookie = {
                "ltuid": data.genshin.ltuid,
                "ltoken": data.genshin.ltoken,
                "cookie_token": data.genshin.cookie_token,
            }

        china = 1 if data.genshin.server == ServerId.CHINA else 0
        async with self.bot.pool.acquire() as db:
            await db.execute(
                "INSERT INTO user_accounts (uid, user_id, ltuid, ltoken, cookie_token, china) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (uid, user_id) DO UPDATE SET ltuid = ?, ltoken = ?, cookie_token = ? WHERE uid = ? AND user_id = ?",
                (
                    uid,
                    user_id,
                    cookie["ltuid"],
                    cookie["ltoken"],
                    cookie["cookie_token"],
                    china,
                    cookie["ltuid"],
                    cookie["ltoken"],
                    cookie["cookie_token"],
                    uid,
                    user_id,
                ),
            )
            await db.commit()

        try:
            await ctx["message"].edit(
                embed=default_embed().set_author(
                    name=text_map.get(39, ctx["locale"]),
                    icon_url=ctx["author"].display_avatar.url,
                ),
                view=None,
            )
        except HTTPException:
            pass


async def setup(client: ShenheBot):
    await client.add_cog(LoginGatewayCog(client))
