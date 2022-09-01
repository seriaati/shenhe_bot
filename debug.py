import discord
import sentry_sdk

from apps.text_map.text_map_app import text_map
from utility.utils import error_embed, log


class DefaultView(discord.ui.View):
    async def on_error(self, i: discord.Interaction, e: Exception, item) -> None:
        log.warning(f'[View Error][{i.user.id}]: [type]{type(e)} [e]{e} [item]{item}')
        sentry_sdk.capture_exception(e)
        try:
            await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        except discord.InteractionResponded:
            await i.followup.send(
                embed=error_embed().set_author(
                    name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
                ),
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
            log.warning(f"[Attribute Error][Edit View]: [children]{self.children}")
        except discord.HTTPException as e:
            log.warning(f"[HTTPException][Edit View]: [children]{self.children} [view]{self}")
            sentry_sdk.capture_event(e)
        except Exception as e:
            log.warning(f"[Edit View]{e}")
            sentry_sdk.capture_event(e)


class DefaultModal(discord.ui.Modal):
    async def on_error(self, i: discord.Interaction, e: Exception) -> None:
        log.warning(f'[Modal Error][{i.user.id}]: [type]{type(e)} [e]{e}')
        sentry_sdk.capture_exception(e)
        try:
            await i.response.send_message(
                embed=error_embed().set_author(
                    name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        except discord.InteractionResponded:
            await i.followup.send(
                embed=error_embed().set_author(
                    name=text_map.get(135, i.locale), icon_url=i.user.display_avatar.url
                ),
                ephemeral=True,
            )
        except discord.NotFound:
            pass
