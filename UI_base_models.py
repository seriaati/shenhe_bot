import traceback
from typing import Optional, Union

import discord
from exceptions import NoPlayerFound, ShenheAccountNotFound, UIDNotFound
import sentry_sdk

from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import error_embed, log


async def global_error_handler(
    i: discord.Interaction, e: Exception | discord.app_commands.AppCommandError
):
    if isinstance(e, discord.app_commands.errors.CheckFailure):
        return

    log.warning(f"[Error][{i.user.id}]{type(e)}: {e}")
    traceback.print_exc()

    locale = await get_user_locale(i.user.id, i.client.db) or i.locale
    embed = get_error_handle_embed(i.user, e, locale)

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label=text_map.get(642, locale),
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


def get_error_handle_embed(
    user: Union[discord.User, discord.Member],
    e: Exception,
    locale: Union[discord.Locale, str],
):
    embed = error_embed()

    unknown = False

    if hasattr(e, "code") and e.code in [10062, 10008, 10015]:
        embed.description = text_map.get(624, locale)
        embed.set_author(name=text_map.get(623, locale))
    elif isinstance(e, discord.app_commands.errors.CommandInvokeError):
        if isinstance(e.original, discord.errors.NotFound) and e.original.code in [
            10062,
            10008,
            10015,
        ]:
            embed.description = text_map.get(624, locale)
            embed.set_author(name=text_map.get(623, locale))
        if isinstance(e.original, UIDNotFound):
            embed.set_author(name=text_map.get(672, locale))
        elif isinstance(e, ShenheAccountNotFound):
            embed.description = text_map.get(35, locale)
            embed.set_author(name=text_map.get(545, locale))
        elif isinstance(e, NoPlayerFound):
            embed.set_author(name=text_map.get(367, locale))
        else:
            unknown = True
    else:
        unknown = True

    if unknown:
        traceback.print_exc()
        sentry_sdk.capture_exception(e)

        embed.description = text_map.get(513, locale)
        embed.description += f"\n\n```{e}```"
        embed.set_author(name=text_map.get(135, locale))
        embed.set_thumbnail(url="https://i.imgur.com/Xi51hSe.gif")

    embed.set_author(name=embed.author.name or "Error", icon_url=user.display_avatar.url)
    return embed


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
                pass
            except Exception as e:
                sentry_sdk.capture_exception(e)
                log.warning(f"[Edit View] Failed{e}")


class BaseModal(discord.ui.Modal):
    async def on_error(self, i: discord.Interaction, e: Exception) -> None:
        await global_error_handler(i, e)
