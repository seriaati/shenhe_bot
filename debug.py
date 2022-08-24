import discord
import sentry_sdk

from apps.text_map.text_map_app import text_map
from utility.utils import error_embed, log


class DefaultView(discord.ui.View):
    async def on_error(self, i: discord.Interaction, e: Exception, item) -> None:
        sentry_sdk.capture_exception(e)
        
        await i.response.send_message(
            embed=error_embed().set_author(
                name=text_map.get(135, i.locale), icon_url=i.user.avatar
            ),
            ephemeral=True,
        )

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        try:
            await self.message.edit(view=self)
        except AttributeError:
            log.warning(f"[EXCEPTION][Attribute Error]: [children]{self.children}")
        except Exception as e:
            log.warning(f"[EXCEPTION][Edit View Erorr]: [retcode]{e.retcode} [original]{e.original} [error message]{e.msg}")
