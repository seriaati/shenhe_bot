from typing import Dict, List
from UI_base_models import BaseView
from ambr.client import AmbrTopAPI
from ambr.models import Material, Monster
from apps.draw.utility import image_gen_transition
from apps.genshin.custom_model import AbyssHalf, DrawInput
from apps.text_map.convert_locale import to_ambr_top
from apps.text_map.utils import get_element_name
import config
from discord.ui import Select, Button
from discord import Locale, Interaction, SelectOption, File, Embed, ButtonStyle
from apps.text_map.text_map_app import text_map
from utility.utils import default_embed, divide_chunks, get_user_appearance_mode
from apps.draw import main_funcs


class View(BaseView):
    def __init__(
        self,
        locale: Locale | str,
        halfs: Dict[str, List[AbyssHalf]],
        embeds: Dict[str, Embed],
        buff_embed: Embed,
    ):
        super().__init__(timeout=config.long_timeout)
        self.locale = locale
        self.halfs = halfs
        self.embeds = embeds
        self.buff_embed = buff_embed

        options = []
        for key in halfs.keys():
            options.append(SelectOption(label=key, value=key))
            if "12" in key:
                self.add_item(InstantButton(key))

        divided_options = list(divide_chunks(options, 25))
        for i, options in enumerate(divided_options):
            self.add_item(ChamberSelect(locale, options, i))
        
        self.add_item(BuffButton(text_map.get(732, locale), buff_embed))


class ChamberSelect(Select):
    def __init__(self, locale: Locale | str, options: List[SelectOption], index: int):
        super().__init__(
            placeholder=text_map.get(314, locale) + f" ({index+1})",
            options=options,
            row=index,
        )

    async def callback(self, i: Interaction):
        self.view: View
        await select_callback(i, self.view, self.values[0])


class InstantButton(Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=ButtonStyle.primary, row=2)

    async def callback(self, i: Interaction):
        self.view: View
        await select_callback(i, self.view, self.label)
        
class BuffButton(Button):
    def __init__(self, label: str, embed: Embed):
        super().__init__(label=label, style=ButtonStyle.green, row=2)
        self.embed = embed
    
    async def callback(self, i: Interaction):
        await i.response.edit_message(embed=self.embed)

async def select_callback(i: Interaction, view: View, value: str):
    await image_gen_transition(i, view, view.locale)
    ambr = AmbrTopAPI(i.client.session, to_ambr_top(view.locale))
    halfs = view.halfs[value]
    embeds = []
    attachments = []
    for index, half in enumerate(halfs):
        materials = []
        for enemy in half.enemies:
            geovishap = False
            enemy_id = text_map.get_id_from_name(enemy.name)
            if "Geovishap" in enemy.name:
                geovishap = True
                enemy_id = 26040101
            if enemy_id is None:
                continue
            monster = await ambr.get_monster(enemy_id)
            if isinstance(monster, Monster):
                monster_name = monster.name
                if geovishap:
                    element = (
                        enemy.name.split("Geovishap ")[1]
                        .replace("(", "")
                        .replace(")", "")
                    )
                    monster_name = (
                        f"{monster.name} ({get_element_name(element, view.locale)})"
                    )
                materials.append(
                    (
                        Material(
                            id=monster.id,
                            name=monster_name,
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
                locale=view.locale,
                dark_mode=await get_user_appearance_mode(i.user.id, i.client.db),
            ),
            materials,
            "",
            draw_title=False,
        )
        fp.seek(0)
        attachment = File(fp, f"enemies{'' if index == 0 else '2'}.jpeg")
        attachments.append(attachment)

        if index == 0:
            embed = view.embeds[value]
        else:
            embed = default_embed(text_map.get(708, view.locale))
            embed.set_image(url=f"attachment://enemies2.jpeg")
        embeds.append(embed)

    for item in view.children:
        item.disabled = False

    if len(embeds) == 2:
        embeds[0].set_footer(text=text_map.get(707, view.locale))

    await i.edit_original_response(attachments=attachments, embeds=embeds, view=view)
