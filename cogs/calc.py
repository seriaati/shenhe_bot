from discord import Interaction, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from apps.genshin.utils import check_level_validity, get_character, get_dummy_client, get_material, get_weapon
from apps.text_map.convert_locale import to_genshin_py
from apps.text_map.utils import get_user_locale
from apps.text_map.text_map_app import text_map
from UI_elements.calc import AddToTodo, CalcCharacter, CalcWeapon
from apps.genshin.genshin_app import GenshinApp
from utility.utils import (default_embed, error_embed)



class CalcCog(commands.GroupCog, name='calc'):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.genshin_app = GenshinApp(bot.db, bot)

    @app_commands.command(name='character角色', description='計算角色升級所需素材')
    @app_commands.rename(sync='同步')
    @app_commands.describe(sync='與遊戲資料同步, 將會自動填入角色及天賦等級')
    @app_commands.choices(sync=[Choice(name='開啟', value=1), Choice(name='關閉', value=0)])
    async def calc_characters(self, i: Interaction, sync: int = 0):
        sync = True if sync == 1 else False
        special_talent_characters = [10000041, 10000002]
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        exists = await self.genshin_app.check_user_data(i.user.id)
        if sync and not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)

        if sync:
            client = (await self.genshin_app.get_user_data(i.user.id, i.locale))[0]
        else:
            client = get_dummy_client()
            client.lang = to_genshin_py(user_locale or i.locale)

        characters = await client.get_calculator_characters(sync=sync)
        view = CalcCharacter.View(
            i.user, self.bot.session, self.bot.db, characters)
        await i.response.send_message(view=view)
        await view.wait()
        valid, error_message = check_level_validity(
            view.levels, user_locale or i.locale)
        if not valid:
            await i.delete_original_message()
            return await i.followup.send(embed=error_embed(message=error_message).set_author(name=text_map.get(190, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)

        embed = default_embed()
        embed.set_author(name=text_map.get(
            191, i.locale, user_locale), icon_url=i.user.avatar)
        embed.set_thumbnail(url=get_character(view.character_id)['icon'])
        
        if sync:
            character_level = (await client.get_calculator_characters(query=text_map.get_character_name(int(view.character_id), 'en-US'), sync=True, lang='en-us'))[0].level
            talents = (await client.get_character_details(int(view.character_id))).talents
        else:
            character_level = 1
            talents = await client.get_character_talents(int(view.character_id))

        builder = client.calculator()
        builder.set_character(int(view.character_id), current=character_level,
                              target=int(view.levels['target']))
        builder.add_talent(talents[0].group_id,
                           current=talents[0].level if sync else 1, target=int(view.levels['a']))
        builder.add_talent(talents[1].group_id,
                           current=talents[1].level if sync else 1, target=int(view.levels['e']))
        burst_talent = talents[3 if int(
            view.character_id) in special_talent_characters else 2]
        builder.add_talent(burst_talent.group_id,
                           current=burst_talent.level if sync else 1, target=int(view.levels['q']))
        cost = await builder.calculate()

        embed.add_field(
            name=text_map.get(192, i.locale, user_locale),
            value=f'{text_map.get(193, i.locale, user_locale)} {character_level} ▸ {view.levels["target"]}\n'
            f'{text_map.get(194, i.locale, user_locale)} {talents[0].level if sync else 1} ▸ {view.levels["a"]}\n'
            f'{text_map.get(195, i.locale, user_locale)} {talents[1].level if sync else 1} ▸ {view.levels["e"]}\n'
            f'{text_map.get(196, i.locale, user_locale)} {burst_talent.level if sync else 1} ▸ {view.levels["q"]}',
            inline=False
        )

        materials = {}
        if len(cost.character) == 0:
            value = text_map.get(197, i.locale, user_locale)
        else:
            value = ''
            for consumable in cost.character:
                value += f'{get_material(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
                if consumable.id in materials:
                    materials[consumable.id] += consumable.amount
                else:
                    materials[consumable.id] = consumable.amount
        embed.add_field(name=text_map.get(
            198, i.locale, user_locale), value=value, inline=False)

        if len(cost.talents) == 0:
            value = text_map.get(197, i.locale, user_locale)
        else:
            value = ''
            for consumable in cost.talents:
                value += f'{get_material(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
                if consumable.id in materials:
                    materials[consumable.id] += consumable.amount
                else:
                    materials[consumable.id] = consumable.amount
        embed.add_field(name=text_map.get(
            199, i.locale, user_locale), value=value, inline=False)

        disabled = True if len(materials) == 0 else False
        view = AddToTodo.View(self.bot.db, disabled, i.user,
                              materials, i.locale, user_locale)
        await i.edit_original_message(embed=embed, view=view)

    @app_commands.command(name='weapon武器', description='計算武器所需的素材')
    @app_commands.rename(types='武器類別', rarities='稀有度')
    @app_commands.describe(types='要計算的武器的類別', rarities='武器的稀有度')
    @app_commands.choices(
        types=[
            Choice(name='單手劍', value=1),
            Choice(name='法器', value=10),
            Choice(name='大劍', value=11),
            Choice(name='弓箭', value=12),
            Choice(name='長槍', value=13)],
        rarities=[
            Choice(name='★★★★★', value=5),
            Choice(name='★★★★', value=4),
            Choice(name='★★★', value=3),
            Choice(name='★★', value=2),
            Choice(name='★', value=1)])
    async def calc_weapon(self, i: Interaction, types: int, rarities: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)

        client = get_dummy_client()
        client.lang = to_genshin_py(user_locale or i.locale)

        weapons = await client.get_calculator_weapons(types=[types], rarities=[rarities])
        view = CalcWeapon.View(
            weapons, i.user, self.bot.db, i.locale, user_locale)
        await i.response.send_message(view=view)
        await view.wait()

        valid, error_message = check_level_validity(
            view.levels, user_locale or i.locale)
        if not valid:
            await i.delete_original_message()
            return await i.followup.send(embed=error_embed(message=error_message).set_author(name=text_map.get(190, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)

        cost = await (
            client.calculator()
            .set_weapon(int(view.weapon_id), current=int(view.levels['current']), target=int(view.levels['target']))
        )

        embed = default_embed()
        embed.set_author(name=text_map.get(
            191, i.locale, user_locale), icon_url=i.user.avatar)
        embed.set_thumbnail(url=get_weapon(view.weapon_id)['icon'])
        embed.add_field(
            name=text_map.get(192, i.locale, user_locale),
            value=f'{text_map.get(200, i.locale, user_locale)} {view.levels["current"]} ▸ {view.levels["target"]}\n',
            inline=False
        )

        materials = {}
        if len(cost.weapon) == 0:
            value = text_map.get(197, i.locale, user_locale)
        else:
            value = ''
            for consumable in cost.weapon:
                value += f'{get_material(consumable.id)["emoji"]} {consumable.name}  x{consumable.amount}\n'
                if consumable.id in materials:
                    materials[consumable.id] += consumable.amount
                else:
                    materials[consumable.id] = consumable.amount
        embed.add_field(name=text_map.get(
            201, i.locale, user_locale), value=value, inline=False)

        disabled = True if len(materials) == 0 else False
        view = AddToTodo.View(self.bot.db, disabled, i.user,
                              materials, i.locale, user_locale)
        await i.edit_original_message(embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CalcCog(bot))
