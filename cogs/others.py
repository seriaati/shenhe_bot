from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.update.change_log import change_log
from data.update.change_log_en import change_log_en
from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands
from UI_elements.others import ChangeLang, ChangeLog
from utility.utils import default_embed


class OthersCog(commands.Cog, name="others"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="lang",
        description=_("Change the langauge shenhe responds you with", hash=485),
    )
    async def lang(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        embed = default_embed(
            message=f"• {text_map.get(125, i.locale, user_locale)}\n"
            f"• {text_map.get(126, i.locale, user_locale)}\n"
            f"• {text_map.get(127, i.locale, user_locale)}\n"
            f"• {text_map.get(511, i.locale, user_locale)}\n\n"
            "[crowdin](https://crowdin.com/project/shenhe-bot)"
        )
        embed.set_author(
            name=text_map.get(128, i.locale, user_locale), icon_url=i.user.avatar
        )
        view = ChangeLang.View(i.locale, user_locale, self.bot.db)
        await i.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = await i.original_response()

    @app_commands.command(
        name="version", description=_("View shenhe's change logs", hash=503)
    )
    async def version(self, i: Interaction):
        embeds = []
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        seria = self.bot.get_user(410036441129943050)
        locale = user_locale or i.locale
        if str(locale) == "zh-TW" or str(locale) == "zh-CN":
            display_change_log = change_log
        else:
            display_change_log = change_log_en
        for version, log in display_change_log.items():
            if self.bot.debug:
                log = f'`{log}`'
            embed = default_embed(version, log)
            embed.set_thumbnail(url=self.bot.user.avatar)
            embed.set_footer(
                text=text_map.get(504, i.locale, user_locale), icon_url=seria.avatar
            )
            embeds.append(embed)
        if i.channel.id != 965964989875757156:
            view = ChangeLog.View(self.bot.db, embeds, i.locale, user_locale)
            await i.response.send_message(embed=embeds[0], view=view)
            view.message = await i.original_response()
        else:
            await i.response.send_message(embed=embeds[0])


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OthersCog(bot))
