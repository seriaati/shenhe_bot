import json
from discord.ui import Select, Button
from discord import Interaction, Embed, SelectOption, Locale, ButtonStyle
from typing import Any, Dict, List
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.text_map_app import text_map
from UI_base_models import BaseView
from apps.text_map.utils import get_user_locale
import config
from dateutil import parser
from discord.utils import format_dt
from utility.paginator import GeneralPaginator
from utility.utils import default_embed, parse_HTML
import hoyolab_rss_feeds.hoyolab


class View(BaseView):
    def __init__(self, locale: Locale | str):
        super().__init__(timeout=config.short_timeout)
        self.locale = locale
        self.add_item(Hoyolab())
        self.add_item(Genshin(locale))


class Hoyolab(Button):
    def __init__(self):
        super().__init__(label="Hoyolab", emoji="<:hoyolab_icon:1025044103135776809>")

    async def callback(self, i: Interaction):
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, i.client.db)
        locale = user_locale or i.locale
        genshin_locale = to_genshin_py(locale)
        await hoyolab_rss_feeds.hoyolab.create_game_feeds_from_config(genshin_locale)
        with open(f"feeds/{genshin_locale}_genshin.json") as f:
            events: Dict = json.load(f)
        select_options = []
        tags = []
        embeds = {}
        events = events["items"]
        for event in events:
            date_published = parser.parse(event["date_published"])
            embed = default_embed(
                event["title"],
                f"{format_dt(date_published)}\n\n{parse_HTML(event['content_html'])[:200]}...\n\n[{text_map.get(454, locale)}]({event['url']})",
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
            select_options.append(SelectOption(label=tag, value=tag))
        await GeneralPaginator(
            i,
            embeds[list(embeds.keys())[0]],
            i.client.db,
            [Select(select_options, embeds, i.locale, user_locale), GOBack(self.view.locale)],
        ).start(edit=True)


class Genshin(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(
            label=text_map.get(313, locale), emoji="<:genshin_icon:1025630733068423169>"
        )

    async def callback(self, i: Interaction):
        await i.response.defer()
        user_locale = (await get_user_locale(i.user.id, i.client.db)) or i.locale
        genshin_py_locale = to_genshin_py(user_locale)
        event_overview_API = f"https://sg-hk4e-api.hoyoverse.com/common/hk4e_global/announcement/api/getAnnList?game=hk4e&game_biz=hk4e_global&lang={genshin_py_locale}&announcement_version=1.21&auth_appid=announcement&bundle_id=hk4e_global&channel_id=1&level=8&platform=pc&region=os_asia&sdk_presentation_style=fullscreen&sdk_screen_transparent=true&uid=901211014"
        event_details_API = f"https://sg-hk4e-api-static.hoyoverse.com/common/hk4e_global/announcement/api/getAnnContent?game=hk4e&game_biz=hk4e_global&lang={genshin_py_locale}&bundle_id=hk4e_global&platform=pc&region=os_asia&t=1659877813&level=7&channel_id=0"
        async with i.client.session.get(event_overview_API) as r:
            overview: Dict = await r.json()
        async with i.client.session.get(event_details_API) as r:
            details: Dict = await r.json()
        type_list = overview["data"]["type_list"]
        options = []
        for type in type_list:
            options.append(SelectOption(label=type["mi18n_name"], value=type["id"]))
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
                embed = default_embed(e["title"])
                embed.set_author(name=e["type_label"], icon_url=e["tag_icon"])
                embed.set_image(url=e["banner"])
                embed.add_field(
                    name=text_map.get(406, i.locale, user_locale),
                    value=format_dt(parser.parse(e["start_time"]), "R"),
                )
                embed.add_field(
                    name=text_map.get(407, i.locale, user_locale),
                    value=format_dt(parser.parse(e["end_time"]), "R"),
                )
                embed.add_field(
                    name=text_map.get(408, i.locale, user_locale),
                    value=parse_HTML(detail_dict[e["ann_id"]])[:500] + "...",
                    inline=False,
                )
                embeds[str(e["type"])].append(embed)
        await GeneralPaginator(
            i,
            embeds[first_id],
            i.client.db,
            [Select(options, embeds, i.locale, user_locale), GOBack(self.view.locale)],
        ).start(edit=True)


class Select(Select):
    def __init__(
        self,
        options: List[SelectOption],
        embeds: Dict[int, List[Embed]],
        locale: Locale,
        user_locale: str | None,
    ) -> None:
        super().__init__(
            options=options, placeholder=text_map.get(409, locale, user_locale)
        )
        self.embeds = embeds

    async def callback(self, i: Interaction) -> Any:
        self.view.current_page = 0
        self.view.embeds = self.embeds[self.values[0]]
        await i.response.edit_message(embed=self.view.embeds[0], view=self.view)

class GOBack(Button):
    def __init__(self, locale: Locale | str):
        super().__init__(label=text_map.get(282, locale), style=ButtonStyle.green, row=3)
    
    async def callback(self, i: Interaction):
        await return_events(i, edit=True)

async def return_events(i: Interaction, edit: bool = False):
    user_locale = await get_user_locale(i.user.id, i.client.db)
    view = View(user_locale or i.locale)
    embed = default_embed().set_author(
        name=text_map.get(361, i.locale, user_locale),
        icon_url=i.user.display_avatar.url,
    )
    if edit:
        await i.response.edit_message(embed=embed, view=view)
    else:
        await i.response.send_message(embed=embed, view=view)
    view.message = await i.original_response()
