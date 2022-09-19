import discord
import sentry_sdk

from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import error_embed, log


class DefaultView(discord.ui.View):
    async def interaction_check(self, i: discord.Interaction) -> bool:
        if not hasattr(self, 'author'):
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
        user_locale = await get_user_locale(i.user.id, i.client.db)
        log.warning(f"[View Error][{i.user.id}]: [type]{type(e)} [e]{e} [item]{item}")
        sentry_sdk.capture_exception(e)
        embed = error_embed(message=text_map.get(513, i.locale, user_locale))
        embed.set_author(
            name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
        )
        embed.set_thumbnail(url="https://i.imgur.com/4XVfK4h.png")
        try:
            await i.response.send_message(
                embed=embed,
                ephemeral=True,
            )
        except discord.errors.InteractionResponded:
            await i.followup.send(
                embed=embed,
                ephemeral=True,
            )
        except discord.NotFound:
            pass

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        try:
            await self.message.edit(view=self)
        except AttributeError:
            log.warning(
                f"[Edit View] Attribute Error: [children]{self.children} [view]{self}"
            )
        except discord.HTTPException:
            log.warning(
                f"[Edit View] HTTPException: [children]{self.children} [view]{self}"
            )
        except Exception as e:
            log.warning(f"[Edit View] Failed{e}")
            sentry_sdk.capture_event(e)


class DefaultModal(discord.ui.Modal):
    async def on_error(self, i: discord.Interaction, e: Exception) -> None:
        user_locale = await get_user_locale(i.user.id, i.client.db)
        log.warning(f"[Modal Error][{i.user.id}]: [type]{type(e)} [e]{e}")
        sentry_sdk.capture_exception(e)
        embed = error_embed(message=text_map.get(513, i.locale, user_locale))
        embed.set_author(
            name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
        )
        embed.set_thumbnail(url="https://i.imgur.com/4XVfK4h.png")

        try:
            await i.response.send_message(
                embed=embed,
                ephemeral=True,
            )
        except discord.InteractionResponded:
            await i.followup.send(
                embed=embed,
                ephemeral=True,
            )
        except discord.NotFound:
            pass
