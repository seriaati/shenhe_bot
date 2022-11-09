from typing import Optional

import discord
import sentry_sdk

from apps.genshin.custom_model import ShenheBot
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import error_embed, log


async def global_error_handler(
    i: discord.Interaction, e: Exception | discord.app_commands.AppCommandError
):
    if isinstance(e, discord.app_commands.errors.CheckFailure):
        return
    user_locale = await get_user_locale(i.user.id, i.client.db)
    if hasattr(e, "code") and e.code in [10062, 10008, 10015]:
        embed = error_embed(message=text_map.get(624, i.locale, user_locale))
        embed.set_author(name=text_map.get(623, i.locale, user_locale))
    else:
        log.warning(f"[{i.user.id}]{type(e)}: {e}")
        sentry_sdk.capture_exception(e)
        embed = error_embed(message=text_map.get(513, i.locale, user_locale))
        embed.description += f"\n```{e}```"
        embed.set_author(
            name=text_map.get(135, i.locale, user_locale),
            icon_url=i.user.display_avatar.url,
        )
        embed.set_thumbnail(url="https://i.imgur.com/Xi51hSe.gif")
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label=text_map.get(642, i.locale, user_locale),
            url="https://discord.gg/ryfamUykRw",
            emoji="<:discord_icon:1032123254103621632>",
        )
    )

    try:
        await i.response.send_message(
            embed=embed,
            ephemeral=True,
            view=view,
        )
    except discord.errors.InteractionResponded:
        await i.followup.send(
            embed=embed,
            ephemeral=True,
            view=view,
        )
    except discord.errors.NotFound:
        pass


class BaseView(discord.ui.View):
    def __init__(self, timeout: Optional[float] = 60.0):
        super().__init__(timeout=timeout)
        self.message: Optional[discord.Message | discord.InteractionMessage] = None
        self.author: Optional[discord.Member | discord.User] = None

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if self.author is None:
            return True
        user_locale = await get_user_locale(i.user.id, i.client.db)
        if self.author.id != i.user.id:
            await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(143, i.locale, user_locale),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        return self.author.id == i.user.id

    async def on_error(self, i: discord.Interaction, e: Exception, item) -> None:
        await global_error_handler(i, e)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                log.warning(
                    f"[Edit View] HTTPException: [children]{self.children} [view]{self}"
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)
                log.warning(f"[Edit View] Failed{e}")


class BaseModal(discord.ui.Modal):
    async def on_error(self, i: discord.Interaction, e: Exception) -> None:
        await global_error_handler(i, e)
