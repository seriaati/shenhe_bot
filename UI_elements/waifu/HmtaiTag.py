from typing import Any, Dict, List

import config
from UI_base_models import BaseView
from discord import Interaction, SelectOption
from discord.ui import Select
from hmtai_async.client import HmtaiAPI
from utility.utils import default_embed, divide_chunks, error_embed
from utility.paginator import GeneralPaginator


class View(BaseView):
    def __init__(self, tags: Dict[str, str], num: int):
        super().__init__(timeout=config.short_timeout)
        self.tags = tags
        self.num = num
        options = []
        for tag, name in tags.items():
            options.append(SelectOption(label=name, value=tag))
        divided = list(divide_chunks(options, 25))
        first = 1
        second = len(divided[0])
        for d in divided:
            self.add_item(TagSelect(d, f"{first}~{second}"))
            first += 25
            second = first + len(d)


class TagSelect(Select):
    def __init__(self, options: List, range: str):
        super().__init__(placeholder=f"選擇標籤 ({range})", options=options)

    async def callback(self, i: Interaction) -> Any:
        await i.response.defer(ephemeral=True)
        await i.edit_original_response(
            embed=default_embed("<a:LOADER:982128111904776242> 正在尋找圖片..."), view=None
        )
        result = []
        hmtai = HmtaiAPI(i.client.session)
        for _ in range(self.view.num):
            url = await hmtai.get(self.values[0])
            if url is None:
                continue
            result.append(url)
        if not result:
            await i.followup.send(
                embed=error_embed(
                    message="可能是你選擇的標籤不再支援\n"
                    "有疑問可私訊 [seria#5334](https://discord.com/users/410036441129943050)"
                ).set_author(name="找不到圖片", icon_url=i.user.display_avatar.url),
                ephemeral=True,
            )
        else:
            embeds = []
            for index, url in enumerate(result):
                embed = default_embed()
                embed.set_author(name=self.view.tags[self.values[0]], icon_url=i.user.display_avatar.url)
                embed.set_image(url=url)
                embed.set_footer(text=f"API: Hmtai | {index + 1}/{len(result)}")
                embeds.append(embed)
            await GeneralPaginator(i, embeds, i.client.db).start(edit=True)