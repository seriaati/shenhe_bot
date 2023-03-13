import json
import aiofiles
from apps.genshin.custom_model import CustomInteraction
import discord
from discord import ui
from discord.utils import format_dt
from typing import Any, Dict, List
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from apps.hoyolab_rss_feeds.create_feed import create_feed
from apps.text_map.utils import get_user_locale
from UI_base_models import BaseView
import config
import asset
from dateutil import parser
from utility.paginator import GeneralPaginator, GeneralPaginatorView
from utility.utils import DefaultEmbed, parse_HTML


class View(BaseView):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale
        self.add_item(Hoyolab())
        self.add_item(Genshin(locale))


class Hoyolab(ui.Button):
    def __init__(self):
        super().__init__(label="HoYoLAB", emoji=asset.hoyolab_emoji)

    async def callback(self, i: CustomInteraction):
        self.view: View
        await i.response.defer()

        user_locale = await get_user_locale(i.user.id, i.client.pool)
        locale = user_locale or i.locale
        genshin_locale = to_genshin_py(locale)

        await create_feed(genshin_locale)

        async with aiofiles.open(
            f"apps/hoyolab_rss_feeds/feeds/{genshin_locale}.json"
        ) as f:
            events = json.loads(await f.read())

        select_options = []
        tags = []
        embeds = {}
        events = events["items"]
        for event in events:
            date_published = parser.parse(event["date_published"])
            embed = DefaultEmbed(event["title"])
            embed.add_field(
                name=text_map.get(625, locale),
                value=format_dt(date_published, "R"),
                inline=False,
            )
            embed.add_field(
                name=text_map.get(408, locale),
                value=f"{parse_HTML(event['content_html'])[:200]}...\n\n[{text_map.get(454, locale)}]({event['url']})",
                inline=False,
            )
            if "image" in event:
                embed.set_image(url=event["image"])
            for tag in event["tags"]:
                if tag not in tags:
                    tags.append(tag)
                if tag not in embeds:
                    embeds[tag] = []
                embeds[tag].append(embed)
            embed.set_author(
                name="Hoyolab",
                icon_url="https://play-lh.googleusercontent.com/5_vh9y9wp8s8Agr7_bjTIz5syyp_jYxGgbTCcPDj3VaA-nilI6Fd75xsBqHHXUxMyB8",
            )

        for tag in tags:
            select_options.append(discord.SelectOption(label=tag, value=tag))
        await GeneralPaginator(
            i,
            embeds[list(embeds.keys())[0]],
            [
                EventTypeSelect(select_options, embeds, self.view.locale),
                GOBack(self.view.locale),
            ],
        ).start(edit=True)


class Genshin(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            label=text_map.get(313, locale), emoji="<:genshin_icon:1025630733068423169>"
        )

    async def callback(self, i: CustomInteraction):
        self.view: View
        await i.response.defer()
        genshin_py_locale = to_genshin_py(self.view.locale)
        event_overview_api = f"https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnList?game=hk4e&game_biz=hk4e_global&lang={genshin_py_locale}&announcement_version=1.21&auth_appid=announcement&bundle_id=hk4e_global&channel_id=1&level=8&platform=pc&region=os_asia&sdk_presentation_style=fullscreen&sdk_screen_transparent=true&uid=901211014"
        event_details_api = f"https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?game=hk4e&game_biz=hk4e_global&lang={genshin_py_locale}&bundle_id=hk4e_global&platform=pc&region=os_asia&t=1659877813&level=7&channel_id=0"
        async with i.client.session.get(event_overview_api) as r:
            overview: Dict = await r.json()
        async with i.client.session.get(event_details_api) as r:
            details: Dict = await r.json()
        type_list = overview["data"]["type_list"]
        options = []
        for type_ in type_list:
            options.append(
                discord.SelectOption(label=type_["mi18n_name"], value=type_["id"])
            )
        # get a dict of details
        detail_dict = {}
        for event in details["data"]["list"]:
            detail_dict[event["ann_id"]] = event["content"]
        first_id = None
        embeds = {}
        for event in overview["data"]["list"]:
            event_list = event["list"]
            if event_list[0]["type"] not in embeds:
                embeds[str(event_list[0]["type"])] = []
            if first_id is None:
                first_id = str(event_list[0]["type"])
            for e in event_list:
                embed = DefaultEmbed(e["title"])
                embed.set_author(name=e["type_label"], icon_url=e["tag_icon"])
                embed.set_image(url=e["banner"])
                embed.add_field(
                    name=text_map.get(406, self.view.locale),
                    value=format_dt(parser.parse(e["start_time"]), "R"),
                )
                embed.add_field(
                    name=text_map.get(407, self.view.locale),
                    value=format_dt(parser.parse(e["end_time"]), "R"),
                )
                embed.add_field(
                    name=text_map.get(408, self.view.locale),
                    value=parse_HTML(detail_dict[e["ann_id"]])[:500] + "...",
                    inline=False,
                )
                embeds[str(e["type"])].append(embed)
        await GeneralPaginator(
            i,
            embeds[first_id],
            [
                EventTypeSelect(options, embeds, self.view.locale),
                GOBack(self.view.locale),
            ],
        ).start(edit=True)


class EventTypeSelect(ui.Select):
    def __init__(
        self,
        options: List[discord.SelectOption],
        embeds: Dict[str, List[discord.Embed]],
        locale: discord.Locale | str,
    ) -> None:
        super().__init__(options=options, placeholder=text_map.get(409, locale))
        self.embeds = embeds

    async def callback(self, i: CustomInteraction) -> Any:
        self.view: GeneralPaginatorView
        self.view.current_page = 0
        self.view.embeds = self.embeds[self.values[0]]
        await self.view.update_children(i)


class GOBack(ui.Button):
    def __init__(self, locale: discord.Locale | str):
        super().__init__(
            label=text_map.get(282, locale), style=discord.ButtonStyle.green, row=3
        )

    async def callback(self, i: CustomInteraction):
        await return_events(i)


async def return_events(i: CustomInteraction):
    await i.response.defer()
    user_locale = await get_user_locale(i.user.id, i.client.pool)
    view = View(user_locale or i.locale)
    embed = DefaultEmbed().set_author(
        name=text_map.get(361, i.locale, user_locale),
        icon_url=i.user.display_avatar.url,
    )
    await i.edit_original_response(embed=embed, view=view)
    view.message = await i.original_response()
