import importlib
import json
import pprint
import sys

from apps.genshin.utils import get_dummy_client
from apps.text_map.convert_locale import to_ambr_top_dict
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from data.game.artifacts import artifacts_map
from data.game.characters import characters_map
from data.game.consumables import consumables_map
from data.game.elements import convert_elements
from data.game.weapons import weapons_map
from data.update.change_log import change_log
from data.update.change_log_en import change_log_en
from discord import Interaction, app_commands
from discord.app_commands import locale_str as _
from discord.ext import commands
from UI_elements.others import ChangeLang, ChangeLog, Roles
from utility.utils import default_embed, error_embed


class OthersCog(commands.Cog, name='others'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='lang', description=_('Change the langauge shenhe responds you with', hash=485))
    async def lang(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        embed = default_embed(message=f'• {text_map.get(125, i.locale, user_locale)}\n'
                              f'• {text_map.get(126, i.locale, user_locale)}\n'
                              f'• {text_map.get(127, i.locale, user_locale)}\n'
                              f'• {text_map.get(511, i.locale, user_locale)}\n\n'
                              '[crowdin](https://crowdin.com/project/shenhe-bot)')
        embed.set_author(name=text_map.get(128, i.locale, user_locale), icon_url=i.user.avatar)
        view=ChangeLang.View(i.locale, user_locale, self.bot.db)
        await i.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = await i.original_response()

    @app_commands.command(name='update', description=_('Admin usage only', hash=496))
    async def update(self, i: Interaction):
        if i.user.id != 410036441129943050:
            return await i.response.send_message(embed=error_embed(message='你不是小雪本人').set_author(name='生物驗證失敗', icon_url=i.user.avatar), ephemeral=True)
        await i.response.send_message(embed=default_embed().set_author(name='更新資料開始', icon_url=i.user.avatar))

        # character, weapon, material, artifact text map
        things_to_update = ['avatar', 'weapon', 'material', 'reliquary']
        for thing in things_to_update:
            dict = {}
            for lang in list(to_ambr_top_dict.values()):
                async with self.bot.session.get(f'https://api.ambr.top/v2/{lang}/{thing}') as r:
                    data = await r.json()
                for character_id, character_info in data['data']['items'].items():
                    if character_id not in dict:
                        dict[character_id] = {}
                    dict[character_id][lang] = character_info['name']
            if thing == 'material':
                dict['202'] = {
                    "chs": "摩拉",
                    "cht": "摩拉",
                    "de": "Mora",
                    "en": "Mora",
                    "es": "Mora",
                    "fr": "Mora",
                    "jp": "モラ",
                    "kr": "모라",
                    "th": "Mora",
                    "pt": "Mora",
                    "ru": "Mopa",
                    "vi": "Mora"
                }
                dict['104003'] = {
                    "chs": "大英雄的经验",
                    "cht": "大英雄的經驗",
                    "de": "Eines Helden Weisheit",
                    "en": "Mora",
                    "es": "Ingenio del héroe",
                    "fr": "Leçons du héros",
                    "jp": "大英雄の経験",
                    "kr": "영웅의 경험",
                    "th": "Hero's Wit",
                    "pt": "EXP do Herói",
                    "ru": "Опыт героя",
                    "vi": "Kinh Nghiệm Anh Hùng"
                }
            with open(f'text_maps/{thing}.json', 'w+', encoding='utf-8') as f:
                json.dump(dict, f, indent=4, ensure_ascii=False)

        await i.followup.send(embed=default_embed().set_author(name='角色、武器、素材、聖遺物 text map 更新成功', icon_url=i.user.avatar))

        # daily dungeon text map
        dict = {}
        for lang in list(to_ambr_top_dict.values()):
            async with self.bot.session.get(f'https://api.ambr.top/v2/{lang}/dailyDungeon') as r:
                data = await r.json()
            for weekday, domains in data['data'].items():
                for domain, domain_info in domains.items():
                    if str(domain_info['id']) not in dict:
                        dict[str(domain_info['id'])] = {}
                    dict[str(domain_info['id'])][lang] = domain_info['name']
        with open(f'text_maps/dailyDungeon.json', 'w+', encoding='utf-8') as f:
            json.dump(dict, f, indent=4, ensure_ascii=False)

        await i.followup.send(embed=default_embed().set_author(name='秘境關卡 text map 更新成功', icon_url=i.user.avatar))

        client = get_dummy_client()
        client.lang = 'zh-tw'

        # artifacts
        result = {}
        artifacts = await client.get_calculator_artifacts()
        for artifact in artifacts:
            if str(artifact.id) in artifacts_map:
                continue
            result[str(artifact.id)] = {
                'name': artifact.name,
                'icon': artifact.icon,
                'ratity': artifact.rarity,
                'artifacts': [],
                'emoji': ''
            }
            other_artifacts = await client.get_complete_artifact_set(artifact.id)
            for other_artifact in other_artifacts:
                result[str(artifact.id)]['artifacts'].append(
                    other_artifact.name)

        result = json.dumps(result, indent=4, sort_keys=True)

        await i.followup.send(embed=default_embed(message=f'```py\n{result}\n```').set_author(name='聖遺物', icon_url=i.user.avatar))

        # characters
        result = {}
        characters = await client.get_calculator_characters()
        for character in characters:
            if str(character.id) in characters_map:
                continue
            result[str(character.id)] = {
                'name': character.name,
                'icon': character.icon,
                'element': character.element,
                'rarity': character.rarity,
                'emoji': '',
                'eng': ''
            }
        # character english names
        client.lang = 'en-us'
        characters = await client.get_calculator_characters()
        for character in characters:
            if str(character.id) in result:
                result[str(character.id)]['eng'] = character.name

        async with self.bot.session.get(f'https://api.ambr.top/v2/cht/avatar') as r:
            characters = await r.json()

        for character_id, character_info in characters['data']['items'].items():
            if 'beta' not in character_info and character_id not in characters_map:
                result[character_id] = {
                    'name': character_info['name'],
                    'icon': f'https://api.ambr.top/assets/UI/{character_info["icon"]}.png',
                    'rarity': character_info['rank'],
                    'emoji': '',
                    'element': convert_elements.get(character_info['element']),
                    'eng': ''
                }

        async with self.bot.session.get(f'https://api.ambr.top/v2/en/avatar') as r:
            characters = await r.json()

        for character_id, character_info in characters['data']['items'].items():
            if character_id in result:
                result[character_id]['eng'] = character_info['name']

        result = json.dumps(result, indent=4, sort_keys=True)

        await i.followup.send(embed=default_embed(message=f'```py\n{result}\n```').set_author(name='角色', icon_url=i.user.avatar))

        # weapons
        client.lang = 'zh-tw'
        result = {}
        weapons = await client.get_calculator_weapons()
        for weapon in weapons:
            if str(weapon.id) in weapons_map:
                continue
            result[str(weapon.id)] = {
                'name': weapon.name,
                'icon': weapon.icon,
                'rarity': weapon.rarity,
                'emoji': '',
                'eng': ''
            }
        client.lang = 'en-us'
        weapons = await client.get_calculator_weapons()
        for weapon in weapons:
            if str(weapon.id) in result:
                result[str(weapon.id)]['eng'] = weapon.name

        async with self.bot.session.get(f'https://api.ambr.top/v2/cht/weapon') as r:
            weapons = await r.json()

        for weapon_id, weapon_info in weapons['data']['items'].items():
            if 'beta' not in weapon_info and weapon_id not in weapons_map:
                result[weapon_id] = {
                    'name': weapon_info['name'],
                    'icon': f'https://api.ambr.top/assets/UI/{weapon_info["icon"]}.png',
                    'rarity': weapon_info['rank'],
                    'emoji': '',
                    'eng': ''
                }

        async with self.bot.session.get(f'https://api.ambr.top/v2/en/weapon') as r:
            weapons = await r.json()

        for weapon_id, weapon_info in weapons['data']['items'].items():
            if weapon_id in result:
                result[weapon_id]['eng'] = weapon_info['name']

        result = json.dumps(result, indent=4, sort_keys=True)

        await i.followup.send(embed=default_embed(message=f'```py\n{result}\n```').set_author(name='武器', icon_url=i.user.avatar))

        # materials
        result = {}

        async with self.bot.session.get(f'https://api.ambr.top/v2/cht/material') as r:
            materials = await r.json()

        needed = ['forgingOre', 'localSpecialtyMondstadt', 'localSpecialtyLiyue', 'localSpecialtyInazuma', 'characterLevelUpMaterial',
                  'weaponAscensionMaterial', 'talentLevelUpMaterial', 'sumeruRegionalSpecialty', 'talentLevelUpMaterials']

        for material_id, material_info in materials['data']['items'].items():
            if 'beta' not in material_info and material_id not in consumables_map and material_info['type'] in needed:
                result[material_id] = {
                    'name': material_info['name'],
                    'icon': f'https://api.ambr.top/assets/UI/{material_info["icon"]}.png',
                    'emoji': ''
                }

        result = json.dumps(result, indent=4, sort_keys=True)

        await i.followup.send(embed=default_embed(message=f'```py\n{result}\n```').set_author(name='素材', icon_url=i.user.avatar))
        
        # check emojis
        message = ''
        for artifact, artifact_info in artifacts_map.items():
            message += artifact_info['emoji']
        await i.followup.send(embed=default_embed(message=message).set_author(name='聖遺物 emoji', icon_url=i.user.avatar))
        
        message = ''
        for character, character_info in characters_map.items():
            message += character_info['emoji']
        await i.followup.send(embed=default_embed(message=message).set_author(name='角色 emoji', icon_url=i.user.avatar))

        message = ''
        for weapon, weapon_info in weapons_map.items():
            message += weapon_info['emoji']
        await i.followup.send(embed=default_embed(message=message).set_author(name='武器 emoji', icon_url=i.user.avatar))
        
        messages = []
        message = ''
        for consumable, consumable_info in consumables_map.items():
            if (len(message) + len(consumable_info['emoji'])) > 4096:
                messages.append(message)
                message = ''
            message += consumable_info['emoji']
        messages.append(message)
        
        for message in messages:
            await i.followup.send(embed=default_embed(message=message).set_author(name='素材 emoji', icon_url=i.user.avatar))

        await i.followup.send(embed=default_embed().set_author(name='更新資料完畢', icon_url=i.user.avatar))

    @app_commands.command(name='reload', description=_('Admin usage only', hash=496))
    @app_commands.rename(module_name='名稱')
    async def realod(self, i: Interaction, module_name: str):
        if i.user.id != 410036441129943050:
            return await i.response.send_message(embed=error_embed(message='你不是小雪本人').set_author(name='生物驗證失敗', icon_url=i.user.avatar), ephemeral=True)
        try:
            importlib.reload(sys.modules[module_name])
        except KeyError:
            return await i.response.send_message(embed=error_embed(message=module_name).set_author(name='查無 module', icon_url=i.user.avatar), ephemeral=True)
        else:
            return await i.response.send_message(embed=default_embed(message=module_name).set_author(name='重整成功', icon_url=i.user.avatar), ephemeral=True)

    @app_commands.command(name='roles', description=_('Admin usage only', hash=496))
    async def roles(self, i: Interaction):
        if i.user.id != 410036441129943050:
            return await i.response.send_message(embed=error_embed(message='你不是小雪本人').set_author(name='生物驗證失敗', icon_url=i.user.avatar), ephemeral=True)
        role = i.guild.get_role(1006906916678684752)
        embed = default_embed(
            '身份組 Roles', f'{role.mention}: {len(role.members)}')
        await i.response.defer(ephemeral=True)
        await i.channel.send(embed=embed, view=Roles.View())

    @app_commands.command(name='version', description=_("View shenhe's change logs", hash=503))
    async def version(self, i: Interaction):
        embeds = []
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        seria = self.bot.get_user(410036441129943050)
        locale = user_locale or i.locale
        if str(locale) == 'zh-TW' or str(locale) == 'zh-CN':
            display_change_log = change_log
        else:
            display_change_log = change_log_en
        for version, log in display_change_log.items():
            embed = default_embed(version, log)
            embed.set_thumbnail(url=self.bot.user.avatar)
            embed.set_footer(text=text_map.get(
                504, i.locale, user_locale), icon_url=seria.avatar)
            embeds.append(embed)
        if i.channel.id != 965964989875757156:
            view = ChangeLog.View(self.bot.db, embeds, i.locale, user_locale)
            await i.response.send_message(embed=embeds[0], view=view)
            view.message = await i.original_response()
        else:
            await i.response.send_message(embed=embeds[0])
            
    @app_commands.command(name='sync', description=_('Admin usage only', hash=496))
    async def roles(self, i: Interaction):
        if i.user.id != 410036441129943050:
            return await i.response.send_message(embed=error_embed(message='你不是小雪本人').set_author(name='生物驗證失敗', icon_url=i.user.avatar), ephemeral=True)
        await i.response.defer()
        await self.bot.tree.sync()
        await i.followup.send('sync done')

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OthersCog(bot))
