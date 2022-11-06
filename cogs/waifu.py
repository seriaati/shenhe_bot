from discord import Interaction, app_commands
from discord.ext import commands
from discord.ui import Button, View

from apps.genshin.custom_model import ShenheBot
from apps.text_map.utils import get_user_locale
from utility.utils import default_embed


class WaifuCog(commands.Cog):
    def __init__(self, bot):
        self.bot: ShenheBot = bot

    @app_commands.command(name="waifu", description="指令都去哪了？")
    async def waifu_command(self, i: Interaction):
        locale = await get_user_locale(i.user.id, self.bot.db) or i.locale
        locale = str(locale)
        view = View()
        view.add_item(
            Button(
                label="邀請萊依菈" if locale in ["zh-TW", "zh-CN"] else "Invite Layla",
                url="https://discord.com/oauth2/authorize?client_id=841806468722589774&permissions=0&scope=bot%20applications.commands",
            )
        )
        if locale in ["zh-TW", "zh-CN"]:
            embed = default_embed(
                "指令都去哪了？",
                "Discord 的新政策表示想要上架在 App Directory 的機器人不可以有任何色情內容。\n所以，我把所有的指令都移除了，並原封不動的將他們移植到另一個機器人：萊依菈 | Layla\n如果你想要繼續使用先前的 waifu 指令，請邀請萊依菈進入你的伺服器。\n造成不便，敬請見諒。",
            )
        else:
            embed = default_embed(
                "Where did all the commands go?",
                "Discord's new policy states that any bot that wants to be listed on the App Directory cannot have any NSFW content.\nSo, I removed all the commands and ported them to another bot: Layla\nIf you want to continue using the waifu commands, please invite Layla to your server.\nSorry for the inconvenience.",
            )
        await i.response.send_message(
            embed=embed,
            view=view,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WaifuCog(bot))
