import io
import typing

import discord
import enkanetwork
import genshin
import sentry_sdk

import dev.asset as asset
import dev.exceptions as exceptions
from apps.db.tables.user_settings import Settings
from apps.text_map import text_map
from utils import log

from .models import ErrorEmbed, Inter, OriginalInfo


async def global_error_handler(
    i: Inter,
    e: typing.Union[Exception, discord.app_commands.AppCommandError],
):
    lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
    embed = get_error_handle_embed(i.user, e, lang)
    view = support_server_view(lang)

    try:
        await i.response.send_message(
            embed=embed,
            ephemeral=True,
            view=view,
        )
    except discord.InteractionResponded:
        await i.followup.send(
            embed=embed,
            ephemeral=True,
            view=view,
        )
    except discord.HTTPException:
        pass


def support_server_view(lang: typing.Union[discord.Locale, str]):
    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label=text_map.get(642, lang),
            url="https://discord.gg/ryfamUykRw",
            emoji="<:discord_icon:1032123254103621632>",
        )
    )

    return view


def get_error_handle_embed(
    user: typing.Optional[typing.Union[discord.User, discord.Member]],
    e: Exception,
    lang: typing.Union[discord.Locale, str],
) -> ErrorEmbed:
    """Returns an error embed based on the givern error type."""
    embed = ErrorEmbed()

    if isinstance(e, discord.app_commands.errors.CommandInvokeError):
        e = e.original

    if isinstance(e, discord.errors.NotFound) and e.code in (
        10062,
        10008,
        10015,
    ):
        embed.description = text_map.get(624, lang)
        embed.set_author(name=text_map.get(623, lang))
    elif isinstance(e, exceptions.AccountNotFound):
        embed.description = text_map.get(35, lang)
        embed.set_author(name=text_map.get(545, lang))
    elif isinstance(e, exceptions.NoPlayerFound):
        embed.set_author(name=text_map.get(367, lang))
    elif isinstance(e, enkanetwork.EnkaServerMaintanance):
        embed.description = text_map.get(519, lang)
        embed.set_author(name=text_map.get(523, lang))
    elif isinstance(e, (enkanetwork.VaildateUIDError, enkanetwork.EnkaPlayerNotFound)):
        embed.description = text_map.get(286, lang)
        embed.set_author(name=text_map.get(523, lang))
    elif isinstance(e, (enkanetwork.EnkaServerError, enkanetwork.HTTPException)):
        embed.set_author(name=text_map.get(523, lang))
    elif isinstance(e, exceptions.NoCharacterFound):
        embed.description = text_map.get(287, lang)
        embed.set_author(name=text_map.get(141, lang))
        embed.set_image(url="https://i.imgur.com/frMsGHO.gif")
    elif isinstance(e, exceptions.NoWishHistory):
        embed.description = text_map.get(368, lang)
        embed.set_author(name=text_map.get(683, lang))
    elif isinstance(e, exceptions.CardNotFound):
        embed.set_author(name=text_map.get(719, lang))
    elif isinstance(e, exceptions.ItemNotFound):
        embed.set_author(name=text_map.get(542, lang))
    elif isinstance(e, exceptions.NumbersOnly):
        embed.set_author(name=text_map.get(187, lang))
    elif isinstance(e, exceptions.AutocompleteError):
        embed.set_author(name=text_map.get(310, lang))
        embed.set_image(url="https://i.imgur.com/TRcvXCG.gif")
    elif isinstance(e, exceptions.CardNotReady):
        embed.set_author(name=text_map.get(189, lang))
    elif isinstance(e, exceptions.FeatureDisabled):
        embed.set_author(name=text_map.get(758, lang))
        embed.description = text_map.get(759, lang)
    elif isinstance(e, exceptions.Maintenance):
        embed.set_author(name=text_map.get(760, lang))
        embed.description = text_map.get(759, lang)
    elif isinstance(e, exceptions.InvalidInput):
        embed.set_author(name=text_map.get(190, lang))
        embed.description = text_map.get(172, lang).format(a=e.a, b=e.b)
    elif isinstance(e, exceptions.AbyssDataNotFound):
        embed.set_author(name=text_map.get(76, lang))
        embed.description = text_map.get(74, lang)
    elif isinstance(e, exceptions.WishFileImportError):
        embed.set_author(name=text_map.get(135, lang))
        embed.description = text_map.get(567, lang)
    elif isinstance(e, genshin.errors.GenshinException):
        if isinstance(e, genshin.errors.DataNotPublic):
            embed.set_author(name=text_map.get(22, lang))
            embed.description = f"{text_map.get(21, lang)}"
        elif isinstance(e, genshin.errors.InvalidCookies):
            embed.set_author(name=text_map.get(36, lang))
            embed.description = text_map.get(767, lang)
        elif isinstance(e, genshin.errors.AlreadyClaimed):
            embed.set_author(name=text_map.get(40, lang))
        elif isinstance(e, genshin.errors.RedemptionClaimed):
            embed.set_author(name=text_map.get(106, lang))
        elif isinstance(e, genshin.errors.RedemptionInvalid):
            embed.set_author(name=text_map.get(107, lang))
        elif isinstance(e, genshin.errors.RedemptionCooldown):
            embed.set_author(name=text_map.get(133, lang))
        elif isinstance(e, genshin.errors.InvalidAuthkey):
            embed.set_author(name=text_map.get(363, lang))
        elif isinstance(e, genshin.errors.AuthkeyTimeout):
            embed.set_author(name=text_map.get(702, lang))
        elif e.retcode == -10002:
            embed.set_author(name=text_map.get(772, lang))
        elif e.retcode == -10001:
            embed.set_author(name=text_map.get(778, lang))
        else:
            embed.description = f"```\n[{e.retcode}]: {e.msg}\n```"
            if e.original:
                embed.description += f"```\n{e.original}\n```"
            embed.set_author(name=text_map.get(10, lang))
    else:
        capture_exception(e)

        embed.description = f"```{type(e)}: {e}```"
        embed.set_author(name=text_map.get(135, lang))
        embed.set_thumbnail(url="https://i.imgur.com/Xi51hSe.gif")

    icon_url = user.display_avatar.url if user else None
    embed.set_author(name=embed.author.name or "Error", icon_url=icon_url)
    return embed


def capture_exception(e: Exception):
    """Log the error and traceback then capture exception to sentry."""
    log.warning(f"Error: {type(e)}: {e}", exc_info=e)
    sentry_sdk.capture_exception(e)


class BaseView(discord.ui.View):
    def __init__(self, timeout: typing.Optional[float] = 60.0):
        super().__init__(timeout=timeout)
        self.message: typing.Optional[
            discord.Message | discord.InteractionMessage
        ] = None
        self.author: typing.Optional[discord.Member | discord.User] = None
        self.original_info: typing.Optional[OriginalInfo] = None

    def get_item(self, custom_id: str) -> typing.Any:
        """Get an item from the view by its custom ID."""
        for item in self.children:
            if (
                isinstance(item, (discord.ui.Button, discord.ui.Select))
                and item.custom_id == custom_id
            ):
                return item
        return None

    def disable_items(self):
        """Disable all items in the view."""
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True

    def enable_items(self):
        """Enable all items in the view."""
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = False

    async def interaction_check(self, i: Inter) -> bool:
        if self.author is None:
            return True

        lang = await i.client.db.settings.get(i.user.id, Settings.LANG) or str(i.locale)
        if self.author.id != i.user.id:
            await i.response.send_message(
                embed=ErrorEmbed().set_author(
                    name=text_map.get(143, lang),
                    icon_url=i.user.display_avatar.url,
                ),
                ephemeral=True,
            )
        return self.author.id == i.user.id

    async def on_error(self, i: Inter, e: Exception, _, /) -> None:
        await global_error_handler(i, e)

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True

        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except Exception:  # skipcq: PYL-W0703
                pass


class BaseModal(discord.ui.Modal):
    async def on_error(self, i: Inter, e: Exception) -> None:
        await global_error_handler(i, e)


class GoBackButton(discord.ui.Button):
    def __init__(self, original_info: OriginalInfo, **kwargs):
        super().__init__(emoji=asset.back_emoji, row=2, **kwargs)
        self.original_embed = original_info.embed
        self.original_view = original_info.view
        self.original_children = original_info.children
        self.original_attachments = original_info.attachments

    async def callback(self, i: Inter):
        await i.response.defer()

        self.original_view.clear_items()
        for item in self.original_children:
            self.original_view.add_item(item)

        kwargs: typing.Dict[str, typing.Any] = {
            "embed": self.original_embed,
            "view": self.original_view,
        }

        if self.original_attachments:
            async with i.client.session.get(self.original_attachments[0].url) as r:
                image = await r.read()
                file_ = discord.File(
                    io.BytesIO(image), filename=self.original_attachments[0].filename
                )
                kwargs["attachments"] = [file_]

        await i.edit_original_response(**kwargs)


class EnkaView(BaseView):
    overview_embeds: typing.List[discord.Embed]
    overview_fps: typing.List[io.BytesIO]
    data: enkanetwork.EnkaNetworkResponse
    en_data: enkanetwork.EnkaNetworkResponse
    member: typing.Union[discord.User, discord.Member]
    author: typing.Union[discord.User, discord.Member]
    message: discord.Message
    character_options: typing.List[discord.SelectOption]
    lang: typing.Union[discord.Locale, str]

    original_children: typing.List[discord.ui.Item] = []
    character_id: str = "0"
    card_data: typing.Optional[enkanetwork.EnkaNetworkResponse] = None

    class Config:
        arbitrary_types_allowed = True


class BaseSelect(discord.ui.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_options: typing.List[discord.SelectOption]
        self.view: BaseView

    async def loading(self, i: Inter):
        self.original_options = self.options

        lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
        lang = lang or str(i.locale)

        self.options = [
            discord.SelectOption(
                label=text_map.get(773, lang),
                emoji=asset.loading_emoji,
                default=True,
            )
        ]
        await i.response.edit_message(view=self.view)

    async def restore(self, i: Inter):
        self.options = self.original_options
        await i.edit_original_response(view=self.view)


class BaseButton(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view: BaseView
        self.original_label: typing.Optional[str]
        self.original_emoji: typing.Optional[typing.Union[str, discord.PartialEmoji]]
        self.original_disabled: bool

    async def loading(self, i: Inter):
        self.original_label = self.label
        self.original_emoji = self.emoji
        self.original_disabled = self.disabled

        lang = await i.client.db.settings.get(i.user.id, Settings.LANG)
        lang = lang or str(i.locale)

        self.emoji = asset.loading_emoji
        self.label = text_map.get(773, lang)
        self.disabled = True
        await i.response.edit_message(view=self.view)

    async def restore(self, i: Inter):
        self.label = self.original_label
        self.emoji = self.original_emoji
        self.disabled = self.original_disabled

        await i.edit_original_response(view=self.view)
