from typing import Dict, List

import discord
from discord import ui

import config
from ambr import AmbrTopAPI, Material, Monster
from apps.db import get_user_theme
from apps.draw import main_funcs
from apps.draw.utility import image_gen_transition
from apps.text_map import text_map, to_ambr_top
from base_ui import BaseView
from models import AbyssHalf, CustomInteraction, DefaultEmbed, DrawInput
from utility import divide_chunks


class View(BaseView):
    def __init__(
        self,
        locale: discord.Locale | str,
        halfs: Dict[str, List[AbyssHalf]],
        embeds: Dict[str, discord.Embed],
        buff_embed: discord.Embed,
    ):
        super().__init__(timeout=config.long_timeout)
        self.locale = locale
        self.halfs = halfs
        self.embeds = embeds
        self.buff_embed = buff_embed

        options = []
        for key in halfs.keys():
            options.append(discord.SelectOption(label=key, value=key))
            if "12" in key:
                self.add_item(InstantButton(key))

        divided_options = list(divide_chunks(options, 25))
        for i, options in enumerate(divided_options):
            self.add_item(ChamberSelect(locale, options, i))

        self.add_item(BuffButton(text_map.get(732, locale), buff_embed))


class ChamberSelect(ui.Select):
    def __init__(
        self,
        locale: discord.Locale | str,
        options: List[discord.SelectOption],
        index: int,
    ):
        super().__init__(
            placeholder=text_map.get(314, locale) + f" ({index+1})",
            options=options,
            row=index,
        )
        self.view: View

    async def callback(self, i: CustomInteraction):
        await select_callback(i, self.view, self.values[0])


class InstantButton(ui.Button):
    def __init__(self, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=2)
        self.view: View

    async def callback(self, i: CustomInteraction):
        if self.label is None:
            raise AssertionError
        await select_callback(i, self.view, self.label)


class BuffButton(ui.Button):
    def __init__(self, label: str, embed: discord.Embed):
        super().__init__(label=label, style=discord.ButtonStyle.green, row=2)
        self.embed = embed

    async def callback(self, i: CustomInteraction):
        await i.response.edit_message(embed=self.embed, attachments=[])


async def select_callback(i: CustomInteraction, view: View, value: str):
    await image_gen_transition(i, view, view.locale)
    ambr = AmbrTopAPI(i.client.session, to_ambr_top(view.locale))  # type: ignore
    halfs = view.halfs[value]
    embeds = []
    attachments = []
    for index, half in enumerate(halfs):
        if not half.enemies:
            continue

        materials = []
        for enemy in half.enemies:
            enemy_id = text_map.get_id_from_name(enemy)
            if enemy_id:
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
                            "",
                        )
                    )
            else:
                materials.append(
                    (Material(id=0, name=enemy, icon="", type="custom"), "")
                )

        fp = await main_funcs.draw_material_card(
            DrawInput(
                loop=i.client.loop,
                session=i.client.session,
                locale=view.locale,
                dark_mode=await get_user_theme(i.user.id, i.client.pool),
            ),
            materials,
            "",
            draw_title=False,
        )
        fp.seek(0)
        attachment = discord.File(fp, f"enemies{'' if index == 0 else '2'}.jpeg")
        attachments.append(attachment)

        if index == 0:
            embed = view.embeds[value]
        else:
            embed = DefaultEmbed(text_map.get(708, view.locale))
            embed.set_image(url="attachment://enemies2.jpeg")
        embeds.append(embed)

    for item in view.children:
        if isinstance(item, (ui.Button, ui.Select)):
            item.disabled = False

    if len(embeds) == 2:
        embeds[0].set_footer(text=text_map.get(707, view.locale))

    await i.edit_original_response(attachments=attachments, embeds=embeds, view=view)
