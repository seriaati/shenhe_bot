import os

from discord.ext import commands
from dotenv import load_dotenv
from logingateway import HuTaoLoginAPI
from logingateway.model import Player, Ready

from apps.db.tables.cookies import Cookie
from dev.models import BotModel
from utils import log

load_dotenv()


class LoginGatewayCog(commands.Cog):
    def __init__(self, bot: BotModel) -> None:
        self.bot = bot
        self.gateway = HuTaoLoginAPI(
            client_id=os.getenv("HUTAO_CLIENT_ID", ""),
            client_secret=os.getenv("HUTAO_CLIENT_SECRET", ""),
        )

        # Event
        self.gateway.ready(self.gateway_connect)
        self.gateway.player_update(self.gateway_player_update)

    async def cog_load(self):
        if self.bot.debug:
            return

        log.info("[System][LoginGateway] Starting gateway...")
        self.gateway.start()
        self.bot.gateway = self.gateway

    async def cog_unload(self):
        if self.bot.debug:
            return

        log.info("[System][LoginGateway] Closing gateway...")
        await self.gateway.close()

    @staticmethod
    async def gateway_connect(_: Ready):
        log.info("[System][LoginGateway] Gateway connected")

    async def gateway_player_update(self, data: Player):
        genshin = data.genshin
        cookie = Cookie(
            ltuid=int(genshin.ltuid),
            cookie_token=genshin.cookie_token,
            ltoken=genshin.ltoken,
        )
        await self.bot.db.cookies.update(cookie)


async def setup(client: BotModel):
    await client.add_cog(LoginGatewayCog(client))
