import io
from typing import Any, Dict, Optional, Union

import genshin

import discord
import enkanetwork
import sentry_sdk

import asset
from apps.genshin.custom_model import OriginalInfo
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from exceptions import (CardNotFound, ItemNotFound, NoCharacterFound, NoCookie,
                        NoPlayerFound, NoUID, NoWishHistory, NumbersOnly,
                        ShenheAccountNotFound, UIDNotFound)
from utility.utils import ErrorEmbed, log


async def global_error_handler(
    i: discord.Interaction, e: Exception | discord.app_commands.AppCommandError
):
    locale = await get_user_locale(i.user.id, i.client.pool) or i.locale
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
    user: Optional[Union[discord.User, discord.Member]],
    e: Exception,
    locale: Union[discord.Locale, str],
):
    """Returns an error embed based on the givern error type."""
    embed = ErrorEmbed()

    if isinstance(e, discord.app_commands.errors.CommandInvokeError):
        e = e.original

    if isinstance(e, discord.errors.NotFound) and e.code in [
        10062,
        10008,
        10015,
    ]:
        embed.description = text_map.get(624, locale)
        embed.set_author(name=text_map.get(623, locale))
    elif isinstance(e, UIDNotFound):
        embed.set_author(name=text_map.get(672, locale))
    elif isinstance(e, ShenheAccountNotFound):
        embed.description = text_map.get(35, locale)
        embed.set_author(name=text_map.get(545, locale))
    elif isinstance(e, NoPlayerFound):
        embed.set_author(name=text_map.get(367, locale))
    elif isinstance(e, enkanetwork.EnkaServerMaintanance):
        embed.description = text_map.get(519, locale)
        embed.set_author(name=text_map.get(523, locale))
    elif isinstance(e, enkanetwork.VaildateUIDError):
        embed.description = text_map.get(286, locale)
        embed.set_author(name=text_map.get(523, locale))
    elif isinstance(e, enkanetwork.EnkaServerError) or isinstance(
        e, enkanetwork.HTTPException
    ):
        embed.set_author(name=text_map.get(523, locale))
    elif isinstance(e, NoCharacterFound):
        embed.description = text_map.get(287, locale)
        embed.set_author(
            name=text_map.get(141, locale),
        )
        embed.set_image(url="https://i.imgur.com/frMsGHO.gif")
    elif isinstance(e, NoUID):
        embed.description = text_map.get(572, locale)
        embed.set_author(name=text_map.get(571 if e.current_user else 579, locale))
    elif isinstance(e, NoCookie):
        if e.current_account:
            embed.description = text_map.get(572, locale)
            embed.set_author(name=text_map.get(573 if e.current_user else 580, locale))
        else:
            embed.description = text_map.get(575, locale)
            embed.set_author(name=text_map.get(574 if e.current_user else 581, locale))
    elif isinstance(e, NoWishHistory):
        embed.description = text_map.get(368, locale)
        embed.set_author(name=text_map.get(683, locale))
    elif isinstance(e, CardNotFound):
        embed.set_author(name=text_map.get(719, locale))
    elif isinstance(e, ItemNotFound):
        embed.set_author(name=text_map.get(542, locale))
    elif isinstance(e, NumbersOnly):
        embed.set_author(name=text_map.get(187, locale))
    elif isinstance(e, genshin.GenshinException):
        embed.set_author(name=text_map.get(10, locale))
    else:
        capture_exception(e)
        
        embed.description = text_map.get(513, locale)
        embed.description += f"\n\n```{type(e)}: {e}```"
        embed.set_author(name=text_map.get(135, locale))
        embed.set_thumbnail(url="https://i.imgur.com/Xi51hSe.gif")

    icon_url = user.display_avatar.url if user else None
    embed.set_author(
        name=embed.author.name or "Error", icon_url=icon_url
    )
    return embed

def capture_exception(e: Exception):
    """Log the error and traceback then capture exception to sentry."""
    log.warning(f"Error: {type(e)}: {e}", exc_info=e)
    sentry_sdk.capture_exception(e)


class BaseView(discord.ui.View):
    def __init__(self, timeout: Optional[float] = 60.0):
        super().__init__(timeout=timeout)
        self.message: Optional[discord.Message | discord.InteractionMessage] = None
        self.author: Optional[discord.Member | discord.User] = None
        self.original_info: Optional[OriginalInfo] = None

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if self.author is None:
            return True

        user_locale = await get_user_locale(i.user.id, i.client.pool)
        if self.author.id != i.user.id:
            await i.response.send_message(
                embed=ErrorEmbed().set_author(
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
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True

        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class BaseModal(discord.ui.Modal):
    async def on_error(self, i: discord.Interaction, e: Exception) -> None:
        await global_error_handler(i, e)


class GoBackButton(discord.ui.Button):
    def __init__(self, original_info: OriginalInfo, **kwargs):
        super().__init__(emoji=asset.back_emoji, row=2, **kwargs)
        self.original_embed = original_info.embed
        self.original_view = original_info.view
        self.original_children = original_info.children
        self.original_attachments = original_info.attachments

    async def callback(self, i: discord.Interaction):
        await i.response.defer()
        
        self.original_view.clear_items()
        for item in self.original_children:
            self.original_view.add_item(item)
        
        kwargs: Dict[str, Any] = {
            "embed": self.original_embed,
            "view": self.original_view,
        }
        
        if self.original_attachments:
            async with i.client.session.get(self.original_attachments[0].url) as r:
                image = await r.read()
                file_ = discord.File(io.BytesIO(image), filename=self.original_attachments[0].filename)
                kwargs["attachments"] = [file_]

        await i.edit_original_response(**kwargs)
