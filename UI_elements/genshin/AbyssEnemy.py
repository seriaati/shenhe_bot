from typing import Dict, List
from UI_base_models import BaseView
from ambr.client import AmbrTopAPI
from ambr.models import Material, Monster
from apps.draw.utility import image_gen_transition
from apps.genshin.custom_model import AbyssHalf, DrawInput
from apps.text_map.convert_locale import to_ambr_top
import config
from discord.ui import Select
from discord import Locale, Interaction, SelectOption, File, Embed
from apps.text_map.text_map_app import text_map
from utility.utils import default_embed, divide_chunks, get_user_appearance_mode
from apps.draw import main_funcs


class View(BaseView):
    def __init__(
        self,
        locale: Locale | str,
        halfs: Dict[str, List[AbyssHalf]],
        embeds: Dict[str, Embed],
    ):
        super().__init__(timeout=config.long_timeout)
        options = []
        for key in halfs.keys():
            options.append(SelectOption(label=key, value=key))
        self.locale = locale
        self.halfs = halfs
        self.embeds = embeds
        divided_options = list(divide_chunks(options, 25))
        for i, options in enumerate(divided_options):
            self.add_item(ChamberSelect(locale, options, i))


class ChamberSelect(Select):
    def __init__(self, locale: Locale | str, options: List[SelectOption], index: int):
        super().__init__(
            placeholder=text_map.get(314, locale) + f" ({index+1})",
            options=options,
        )

    async def callback(self, i: Interaction):
        self.view: View
        await image_gen_transition(i, self.view, self.view.locale)
        ambr = AmbrTopAPI(i.client.session, to_ambr_top(self.view.locale))
        halfs = self.view.halfs[self.values[0]]
        embeds = []
        attachments = []
        for index, half in enumerate(halfs):
            materials = []
            for enemy in half.enemies:
                enemy_id = text_map.get_id_from_name(enemy.name)
                monster = await ambr.get_monster(enemy_id)
                if isinstance(monster, Monster):
                    materials.append(
                        (
                            Material(
                                id=monster.id,
                                name=monster.name,
                                icon=monster.icon,
                                type="custom",
                            ),
                            enemy.num,
                        )
                    )
            fp = await main_funcs.draw_material_card(
                DrawInput(
                    loop=i.client.loop,
                    session=i.client.session,
                    locale=self.view.locale,
                    dark_mode=await get_user_appearance_mode(i.user.id, i.client.db),
                ),
                materials,
                "",
                draw_title=False
            )
            fp.seek(0)
            attachment = File(fp, f"enemies{'' if index == 0 else '2'}.jpeg")
            attachments.append(attachment)
            
            if index == 0:
                embed = self.view.embeds[self.values[0]]
            else:
                embed = default_embed(text_map.get(708, self.view.locale))
                embed.set_image(url=f"attachment://enemies2.jpeg")
            embeds.append(embed)
            
        for item in self.view.children:
            item.disabled = False
            
        await i.edit_original_response(
            attachments=attachments, embeds=embeds, view=self.view
        )
