from datetime import datetime
from pprint import pprint

import aiosqlite
import GGanalysislib
from apps.genshin.genshin_app import GenshinApp
from apps.genshin.utils import calculate_artifact_score, get_artifact, get_character, get_farm_dict, get_fight_prop, get_material, get_weapon
from apps.text_map.convert_locale import to_ambr_top, to_enka
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale, get_weekday_name
from data.game.elements import elements
from data.game.equip_types import equip_types
from data.game.fight_prop import fight_prop
from discord import Interaction, Member, SelectOption, User, app_commands
from discord.app_commands import Choice
from discord.ext import commands
from enkanetwork import EnkaNetworkResponse, UIDNotFounded, VaildateUIDError
from enkanetwork.enum import DigitType, EquipmentsType
from UI_elements.genshin import (Abyss, AccountRegister, ArtifactLeaderboard,
                                 Build, CharacterWiki, Diary, EnkaProfile,
                                 ResinNotification, ShowAllCharacters,
                                 TalentNotification)
from utility.paginator import GeneralPaginator
from utility.utils import (default_embed, divide_chunks, error_embed,
                           parse_HTML, rank_user)

from cogs.wish import WishCog


class GenshinCog(commands.Cog, name='genshin'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.genshin_app = GenshinApp(self.bot.db, self.bot)
        self.debug = self.bot.debug

        # Right click commands
        self.search_uid_context_menu = app_commands.ContextMenu(
            name='查看 UID',
            callback=self.search_uid_ctx_menu
        )
        self.profile_context_menu = app_commands.ContextMenu(
            name='查看 profile',
            callback=self.profile_ctx_menu
        )
        self.characters_context_menu = app_commands.ContextMenu(
            name='查看所有角色',
            callback=self.characters_ctx_menu
        )
        self.stats_context_menu = app_commands.ContextMenu(
            name='原神數據',
            callback=self.stats_ctx_menu
        )
        self.check_context_menu = app_commands.ContextMenu(
            name='即時便籤',
            callback=self.check_ctx_menu
        )
        self.bot.tree.add_command(self.search_uid_context_menu)
        self.bot.tree.add_command(self.profile_context_menu)
        self.bot.tree.add_command(self.characters_context_menu)
        self.bot.tree.add_command(self.stats_context_menu)
        self.bot.tree.add_command(self.check_context_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.search_uid_context_menu.name, type=self.search_uid_context_menu.type)
        self.bot.tree.remove_command(
            self.profile_context_menu.name, type=self.profile_context_menu.type)
        self.bot.tree.remove_command(
            self.characters_context_menu.name, type=self.characters_context_menu.type)
        self.bot.tree.remove_command(
            self.stats_context_menu.name, type=self.stats_context_menu.type)
        self.bot.tree.remove_command(
            self.check_context_menu.name, type=self.check_context_menu.type)

    @app_commands.command(
        name='register註冊',
        description='註冊你的原神帳號')
    @app_commands.rename(option='選項')
    @app_commands.choices(option=[
        Choice(name='註冊教學', value=0),
        Choice(name='提交 cookie', value=1)])
    async def slash_cookie(self, i: Interaction, option: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if option == 0:
            embed = default_embed(
                text_map.get(137, i.locale, user_locale), text_map.get(138, i.locale, user_locale))
            embed.set_image(url="https://i.imgur.com/OQ8arx0.gif")
            code_msg = f"```script:d=document.cookie; c=d.includes('account_id') || alert('{text_map.get(139, i.locale, user_locale)}'); c && document.write(d)```"
            await i.response.send_message(embed=embed, ephemeral=True)
            await i.followup.send(content=code_msg, ephemeral=True)
        elif option == 1:
            await i.response.send_modal(AccountRegister.Modal(self.genshin_app, i.locale, user_locale))

    @app_commands.command(
        name='check即時便籤',
        description='查看即時便籤: 目前樹脂、洞天寶錢、探索派遣 (需註冊)'
    )
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def check(self, i: Interaction, member: User = None):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        exists = await self.genshin_app.check_user_data(member.id)
        if not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=member.avatar), ephemeral=True)
        result, success = await self.genshin_app.get_real_time_notes(member.id, i.locale)
        await i.response.send_message(embed=result, ephemeral=not success)

    async def check_ctx_menu(self, i: Interaction, member: User):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        exists = await self.genshin_app.check_user_data(member.id)
        if not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=member.avatar), ephemeral=True)
        result, success = await self.genshin_app.get_real_time_notes(member.id, i.locale)
        await i.response.send_message(embed=result, ephemeral=True)

    @app_commands.command(name='stats數據', description='查看原神資料, 如活躍時間、神瞳數量、寶箱數量 (需註冊)')
    @app_commands.rename(member='其他人', custom_uid='uid')
    @app_commands.describe(member='查看其他群友的資料', custom_uid='欲查詢玩家的 UID，如果已註冊過則不用填')
    async def stats(self, i: Interaction, member: User = None, custom_uid: int = None):
        member = member or i.user
        result, success = await self.genshin_app.get_stats(member.id, custom_uid, i.locale)
        await i.response.send_message(embed=result, ephemeral=not success)

    async def stats_ctx_menu(self, i: Interaction, member: User):
        result, success = await self.genshin_app.get_stats(member.id, None, i.locale)
        await i.response.send_message(embed=result, ephemeral=True)

    @app_commands.command(name='area探索度', description='查看區域探索度 (需註冊)')
    @app_commands.rename(member='其他人', custom_uid='uid')
    @app_commands.describe(member='查看其他群友的資料', custom_uid='欲查詢玩家的 UID，如果已註冊過則不用填')
    async def area(self, i: Interaction, member: User = None, custom_uid: int = None):
        member = member or i.user
        result, success = await self.genshin_app.get_area(member.id, custom_uid, i.locale)
        await i.response.send_message(embed=result, ephemeral=not success)

    @app_commands.command(name='claim登入獎勵', description='領取hoyolab網頁登入獎勵 (需註冊)')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def claim(self, i: Interaction, member: User = None):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        exists = await self.genshin_app.check_user_data(member.id)
        if not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=member.avatar), ephemeral=True)
        result, success = await self.genshin_app.claim_daily_reward(member.id, i.locale)
        await i.response.send_message(embed=result, ephemeral=not success)

    @app_commands.command(name='characters所有角色', description='展示自己擁有的所有角色')
    @app_commands.rename(member='其他人')
    @app_commands.describe(member='查看其他群友的資料')
    async def characters(self, i: Interaction, member: User = None):
        await self.characters_comamnd(i, member, False)

    async def characters_ctx_menu(self, i: Interaction, member: User):
        await self.characters_comamnd(i, member)

    async def characters_comamnd(self, i: Interaction, member: User = None, ephemeral: bool = True):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        exists = await self.genshin_app.check_user_data(member.id)
        if not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=member.avatar), ephemeral=True)
        result, success = await self.genshin_app.get_all_characters(member.id, i.locale)
        if not success:
            return await i.response.send_message(embed=result, ephemeral=True)
        placeholder = text_map.get(142, i.locale, user_locale)
        await GeneralPaginator(i, result['embeds'], [ShowAllCharacters.ElementSelect(result['options'], placeholder)]).start(embeded=True, check=False, ephemeral=ephemeral)

    @app_commands.command(name='diary旅行者日記', description='查看旅行者日記 (需註冊)')
    @app_commands.rename(month='月份', member='其他人')
    @app_commands.describe(month='要查詢的月份', member='查看其他群友的資料')
    @app_commands.choices(month=[
        app_commands.Choice(name='這個月', value=0),
        app_commands.Choice(name='上個月', value=-1),
        app_commands.Choice(name='上上個月', value=-2)])
    async def diary(self, i: Interaction, month: int = 0, member: User = None):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        exists = await self.genshin_app.check_user_data(member.id)
        if not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=member.avatar), ephemeral=True)
        month = datetime.now().month + month
        month = month + 12 if month < 1 else month
        result, success = await self.genshin_app.get_diary(member.id, month, i.locale)
        if not success:
            await i.response.send_message(embed=result, ephemeral=not success)
        else:
            await i.response.send_message(embed=result, view=Diary.View(i.user, member, self.genshin_app, i.locale, user_locale))

    @app_commands.command(name='abyss深淵', description='深淵資料查詢 (需註冊)')
    @app_commands.rename(overview='類別', previous='期別', member='其他人')
    @app_commands.describe(overview='想要查看的資料類別',
                           previous='這期還是上期?', member='查看其他群友的資料')
    @app_commands.choices(
        overview=[Choice(name='詳細', value=0),
                  Choice(name='總覽', value=1)],
        previous=[Choice(name='本期紀錄', value=0),
                  Choice(name='上期紀錄', value=1)]
    )
    async def abyss(self, i: Interaction, overview: int = 1, previous: int = 0, member: User = None):
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        exists = await self.genshin_app.check_user_data(member.id)
        if not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=member.avatar), ephemeral=True)
        previous = True if previous == 1 else False
        overview = True if overview == 1 else False
        result, success = await self.genshin_app.get_abyss(member.id, previous, overview, i.locale)
        if not success:
            return await i.response.send_message(embed=result, ephemeral=True)
        if overview:
            return await i.response.send_message(embed=result)
        else:
            await i.response.send_message(embed=result[0], view=Abyss.View(i.user, result, i.locale, user_locale, self.bot.db))

    @app_commands.command(name='stuck找不到資料', description='註冊了, 但是找不到資料嗎?')
    async def stuck(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        embed = default_embed(
            text_map.get(149, i.locale, user_locale),
            text_map.get(150, i.locale, user_locale))
        embed.set_image(url='https://i.imgur.com/w6Q7WwJ.gif')
        await i.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='remind提醒', description='設置提醒功能 (樹脂提醒需要註冊, 天賦不需要)')
    @app_commands.rename(function='功能', toggle='開關')
    @app_commands.describe(function='提醒功能', toggle='要開啟或關閉該提醒功能')
    @app_commands.choices(function=[Choice(name='樹脂提醒 (需註冊)', value=0), Choice(name='天賦素材提醒', value=1), Choice(name='啟用提醒功能前請先確認隱私設定', value=2)],
                          toggle=[Choice(name='開 (調整設定)', value=1), Choice(name='關', value=0)])
    async def remind(self, i: Interaction, function: int, toggle: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if function == 0:
            if toggle == 0:
                exists = await self.genshin_app.check_user_data(i.user.id)
                if not exists:
                    return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=i.user.avatar))
                result, success = await self.genshin_app.set_resin_notification(i.user.id, 0, None, None, i.locale)
                await i.response.send_message(embed=result, ephemeral=not success)
            else:
                modal = ResinNotification.Modal(i.locale, user_locale)
                await i.response.send_modal(modal)
                await modal.wait()
                result, success = await self.genshin_app.set_resin_notification(i.user.id, toggle, modal.resin_threshold.value, modal.max_notif.value, i.locale)
                await i.followup.send(embed=result, ephemeral=not success)

        elif function == 1:
            c: aiosqlite.Cursor = await self.bot.db.cursor()
            if toggle == 0:
                await c.execute('UPDATE genshin_accounts SET talent_notif_toggle = 0 WHERE user_id = ?', (i.user.id,))
                await self.bot.db.commit()
                embed = default_embed()
                embed.set_author(name=text_map.get(
                    307, i.locale, user_locale), icon_url=i.user.avatar)
                await i.response.send_message(embed=embed)
            else:
                await c.execute('UPDATE genshin_accounts SET talent_notif_toggle = 1 WHERE user_id = ?', (i.user.id,))
                await self.bot.db.commit()
                embed = default_embed(message=text_map.get(
                    156, i.locale, user_locale))
                embed.set_author(name=text_map.get(
                    157, i.locale, user_locale), icon_url=i.user.avatar)
                value = await self.genshin_app.get_user_talent_notification_enabled_str(i.user.id, i.locale)
                embed.add_field(name=text_map.get(
                    159, i.locale, user_locale), value=value)
                await i.response.send_message(embed=embed, view=TalentNotification.View(i.user, i.locale, user_locale, self.bot.db, self.genshin_app, self.bot.session))

        elif function == 2:
            embed = default_embed(
                message=f'1. {text_map.get(308, i.locale, user_locale)}\n'
                f'2. {text_map.get(309, i.locale, user_locale)}\n'
                f'3. {text_map.get(310, i.locale, user_locale)}')
            embed.set_author(name=text_map.get(
                311, i.locale, user_locale), icon_url=i.user.avatar)
            embed.set_image(url='https://i.imgur.com/sYg4SpD.gif')
            await i.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='farm刷素材', description='查看原神今日可刷素材')
    async def farm(self, i: Interaction):
        await i.response.defer()
        embeds = []
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        user_locale = user_locale or i.locale
        farm_dict, daily_dungeon = await get_farm_dict(self.bot.session, user_locale)
        today_farmable = {}

        for dungeon, dungeon_info in daily_dungeon[get_weekday_name(datetime.today().weekday(), 'en-US', None, True)].items():
            if dungeon_info['id'] not in today_farmable:
                today_farmable[dungeon_info['id']] = []
            for character_id, character_items in farm_dict['avatar'].items():
                for item_id in list(character_items.keys()):
                    if int(item_id) in dungeon_info['reward'] and character_id not in today_farmable[dungeon_info['id']]:
                        today_farmable[dungeon_info['id']].append(character_id)
            for weapon_id, weapon_items in farm_dict['weapon'].items():
                for item_id in list(weapon_items.keys()):
                    if int(item_id) in dungeon_info['reward'] and weapon_id not in today_farmable[dungeon_info['id']]:
                        today_farmable[dungeon_info['id']].append(weapon_id)

        # pprint(today_farmable)

        for domain_id, farmable_list in today_farmable.items():
            embed = default_embed(
                f'{text_map.get(2, i.locale, user_locale)} ({get_weekday_name(datetime.today().weekday(), i.locale, user_locale)}) {text_map.get(250, i.locale, user_locale)}')
            value = ''
            for farmable in farmable_list:
                emoji = get_weapon(farmable)['emoji'] if len(
                    farmable) == 5 else get_character(farmable)['emoji']
                name = text_map.get_weapon_name(farmable, i.locale, user_locale) if len(
                    farmable) == 5 else text_map.get_character_name(farmable, i.locale, user_locale)
                value += f'{emoji} {name}\n'
            embed.add_field(name=text_map.get_domain_name(
                domain_id, i.locale, user_locale), value=value)
            embeds.append(embed)

        await GeneralPaginator(i, embeds).start(embeded=True, follow_up=True)

    @app_commands.command(name='build角色配置', description='查看角色推薦主詞條、畢業面板、不同配置、聖遺物思路等')
    async def build(self, i: Interaction):
        await i.response.send_message(view=Build.View(i.user, self.bot.db))

    @app_commands.command(name='uid查詢', description='查詢特定使用者的原神UID')
    @app_commands.rename(player='使用者')
    @app_commands.describe(player='選擇想要查詢的使用者')
    async def search_uid(self, i: Interaction, player: Member):
        await self.search_uid_command(i, player, False)

    async def search_uid_ctx_menu(self, i: Interaction, player: Member):
        await self.search_uid_command(i, player)

    async def search_uid_command(self, i: Interaction, player: Member, ephemeral: bool = True):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if i.guild.id == 916838066117824553:
            c = await self.bot.main_db.cursor()
        else:
            c = await self.bot.db.cursor()
        c: aiosqlite.Cursor
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (player.id,))
        uid = await c.fetchone()
        if uid is None:
            return await i.response.send_message(embed=error_embed(message=text_map.get(165, i.locale, user_locale)).set_author(name=text_map.get(166, i.locale, user_locale), icon_url=player.avatar), ephemeral=True)
        uid = uid[0]
        embed = default_embed(uid)
        embed.set_author(
            name=f'{player.display_name}{text_map.get(167, i.locale, user_locale)}', icon_url=player.avatar)
        await i.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(name='profile角色展示', description='查看原神角色聖遺物、屬性、進行傷害計算')
    @app_commands.rename(member='其他人', custom_uid='uid')
    @app_commands.describe(member='查看其他人的資料', custom_uid='欲查詢玩家的 UID，如果已註冊過則不用填')
    async def profile(self, i: Interaction, member: User = None, custom_uid: int = None):
        await self.profile_command(i, member, custom_uid, False)

    async def profile_ctx_menu(self, i: Interaction, member: User):
        await self.profile_command(i, member)

    async def profile_command(self, i: Interaction, member: User = None, custom_uid: int = None, ephemeral: bool = True):
        await i.response.defer(ephemeral=ephemeral)
        member = member or i.user
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        if custom_uid is None:
            if i.guild.id == 916838066117824553:
                c: aiosqlite.Cursor = await self.bot.main_db.cursor()
                await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (member.id,))
                uid = await c.fetchone()
                if uid is None:
                    return await i.followup.send(embed=error_embed(message='請先至 <#978871680019628032> 設置 UID!').set_author(name='找不到 UID!', icon_url=member.avatar), ephemeral=True)
            else:
                c: aiosqlite.Cursor = await self.bot.db.cursor()
                exists = await self.genshin_app.check_user_data(member.id)
                if not exists:
                    return await i.followup.send(embed=error_embed(message=f'{text_map.get(140, i.locale, user_locale)}\n{text_map.get(283, i.locale, user_locale)}').set_author(name=text_map.get(141, i.locale, user_locale), icon_url=member.avatar), ephemeral=True)
                await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (member.id,))
                uid = await c.fetchone()
        uid = custom_uid or uid[0]
        enka_locale = to_enka(user_locale or i.locale)
        await self.bot.enka_client.set_language(enka_locale)
        try:
            data: EnkaNetworkResponse = await self.bot.enka_client.fetch_user(uid)
        except KeyError:
            return await i.followup.send(embed=error_embed(message=text_map.get(285, i.locale, user_locale)).set_author(name=text_map.get(284, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        except UIDNotFounded:
            return await i.followup.send(embed=error_embed().set_author(name=text_map.get(286, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        except VaildateUIDError:
            return await i.followup.send(embed=error_embed().set_author(name=text_map.get(286, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)
        if data.characters is None:
            embed = default_embed(message=text_map.get(287, i.locale, user_locale)).set_author(
                name=text_map.get(141, i.locale, user_locale), icon_url=i.user.avatar).set_image(url='https://i.imgur.com/frMsGHO.gif')
            return await i.followup.send(embed=embed, ephemeral=True)
        await self.bot.enka_client.set_language('en')
        eng_data = await self.bot.enka_client.fetch_user(uid)
        embeds = {}
        sig = f'「{data.player.signature}」\n' if data.player.signature != '' else ''
        overview = default_embed(
            f'{data.player.nickname}',
            f"{sig}"
            f"{text_map.get(288, i.locale, user_locale)}: Lvl. {data.player.level}\n"
            f"{text_map.get(289, i.locale, user_locale)}: W{data.player.world_level}\n"
            f"{text_map.get(290, i.locale, user_locale)}: {data.player.achievement}\n"
            f"{text_map.get(291, i.locale, user_locale)}: {data.player.abyss_floor}-{data.player.abyss_room}")
        overview.set_author(name=member.display_name, icon_url=member.avatar)
        overview.set_image(url=data.player.namecard.banner)
        embeds['0'] = overview
        options = [SelectOption(label=text_map.get(43, i.locale, user_locale), value=0,
                                emoji='<:SCORE:983948729293897779>')]
        artifact_embeds = {}
        for character in data.characters:
            options.append(SelectOption(label=f'{character.name} | Lvl. {character.level}',
                           value=character.id, emoji=get_character(character.id)['emoji']))
            embed = default_embed(
                f'{character.name} C{character.constellations_unlocked}R{character.equipments[-1].refinement} | Lvl. {character.level}/{character.max_level}'
            )
            embed.add_field(
                name=text_map.get(301, i.locale, user_locale),
                value=f'<:HP:982068466410463272> {text_map.get(292, i.locale, user_locale)} - {character.stats.FIGHT_PROP_MAX_HP.to_rounded()}\n'
                f"<:ATTACK:982138214305390632> {text_map.get(293, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CUR_ATTACK.to_rounded()}\n"
                f"<:DEFENSE:982068463566721064> {text_map.get(294, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CUR_DEFENSE.to_rounded()}\n"
                f"<:ELEMENT_MASTERY:982068464938270730> {text_map.get(295, i.locale, user_locale)} - {character.stats.FIGHT_PROP_ELEMENT_MASTERY.to_rounded()}\n"
                f"<:CRITICAL:982068460731392040> {text_map.get(296, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CRITICAL.to_percentage_symbol()}\n"
                f"<:CRITICAL_HURT:982068462081933352> {text_map.get(297, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CRITICAL_HURT.to_percentage_symbol()}\n"
                f"<:CHARGE_EFFICIENCY:982068459179503646> {text_map.get(298, i.locale, user_locale)} - {character.stats.FIGHT_PROP_CHARGE_EFFICIENCY.to_percentage_symbol()}\n"
                f"<:FRIENDSHIP:982843487697379391> {text_map.get(299, i.locale, user_locale)} - {character.friendship_level}\n",
                inline=False
            )

            # talents
            value = ''
            for skill in character.skills:
                value += f'{skill.name} | Lvl. {skill.level}\n'
            embed.add_field(
                name=text_map.get(94, i.locale, user_locale),
                value=value
            )

            # weapon
            weapon = character.equipments[-1]
            weapon_sub_stats = ''
            for substat in weapon.detail.substats:
                weapon_sub_stats += f"{get_fight_prop(substat.prop_id)['emoji']} {text_map.get(fight_prop.get(substat.prop_id)['text_map_hash'], i.locale, user_locale)} {substat.value}{'%' if substat.type == DigitType.PERCENT else ''}\n"
            embed.add_field(
                name=text_map.get(91, i.locale, user_locale),
                value=f'{get_weapon(weapon.id)["emoji"]} {weapon.detail.name} | Lvl. {weapon.level}\n'
                f"{get_fight_prop(weapon.detail.mainstats.prop_id)['emoji']} {weapon.detail.mainstats.name} {weapon.detail.mainstats.value}{'%' if weapon.detail.mainstats.type == DigitType.PERCENT else ''}\n"
                f'{weapon_sub_stats}',
                inline=False
            )
            embed.set_thumbnail(url=character.image.icon)
            embed.set_author(name=member.display_name, icon_url=member.avatar)
            embeds[str(character.id)] = embed

            # artifacts
            artifact_embed = default_embed(
                f'{character.name} | {text_map.get(92, i.locale, user_locale)}')
            index = 0
            for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
                artifact_sub_stats = f'**__{get_fight_prop(artifact.detail.mainstats.prop_id)["emoji"]} {text_map.get(fight_prop.get(artifact.detail.mainstats.prop_id)["text_map_hash"], i.locale, user_locale)}+{artifact.detail.mainstats.value}__**\n'
                artifact_sub_stat_dict = {}
                for substat in artifact.detail.substats:
                    artifact_sub_stat_dict[substat.prop_id] = substat.value
                    artifact_sub_stats += f'{get_fight_prop(substat.prop_id)["emoji"]} {text_map.get(fight_prop.get(substat.prop_id)["text_map_hash"], i.locale, user_locale)}+{substat.value}{"%" if substat.type == DigitType.PERCENT else ""}\n'
                if artifact.level == 20:
                    artifact_sub_stats += f'<:SCORE:983948729293897779> {int(calculate_artifact_score(artifact_sub_stat_dict))}'
                artifact_embed.add_field(
                    name=f'{list(equip_types.values())[index]}{artifact.detail.name} +{artifact.level}',
                    value=artifact_sub_stats
                )
                artifact_embed.set_thumbnail(url=character.image.icon)
                artifact_embed.set_author(
                    name=member.display_name, icon_url=member.avatar)
                artifact_embed.set_footer(
                    text=text_map.get(300, i.locale, user_locale))
                index += 1
            artifact_embeds[str(character.id)] = artifact_embed

        view = EnkaProfile.View(embeds, artifact_embeds, options,
                                data, self.bot.browser, eng_data, i.user, self.bot.db, i.locale, user_locale)
        await i.followup.send(embed=embeds['0'], view=view, ephemeral=ephemeral)

    @app_commands.command(name='redeem兌換', description='兌換禮物碼 (需註冊)')
    @app_commands.rename(code='兌換碼')
    async def redeem(self, i: Interaction, code: str):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        exists = await self.genshin_app.check_user_data(i.user.id)
        if not exists:
            return await i.response.send_message(embed=error_embed(message=text_map.get(140, i.locale, user_locale)).set_author(name=text_map.get(141, i.locale, user_locale), icon_url=i.user.avatar))
        result, success = await self.genshin_app.redeem_code(i.user.id, code, i.locale)
        await i.response.send_message(embed=result, ephemeral=not success)

    @app_commands.command(name='events活動', description='查看原神近期的活動')
    async def events(self, i: Interaction):
        await i.response.defer(ephemeral=True)
        async with self.bot.session.get(f'https://api.ambr.top/assets/data/event.json') as r:
            events = await r.json()
        embeds = []
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        user_locale = user_locale or i.locale
        ambr_top_locale = to_ambr_top(user_locale).upper()
        for event_id, event in events.items():
            value = parse_HTML(
                event['description'][ambr_top_locale])
            embed = default_embed(
                event['name'][ambr_top_locale], event['nameFull'][ambr_top_locale])
            embed.add_field(
                name='<:placeholder:982425507503165470>', value=value[:1021]+'...', inline=False)
            embed.set_image(url=event['banner'][ambr_top_locale])
            embeds.append(embed)
        await GeneralPaginator(i, embeds).start(embeded=True, ephemeral=True, follow_up=True)

    @app_commands.command(name='leaderboard排行榜', description='查看排行榜')
    @app_commands.rename(type='分類')
    @app_commands.describe(type='選擇要查看的排行榜分類')
    @app_commands.choices(type=[Choice(name='成就榜', value=0), Choice(name='聖遺物副詞條榜', value=1), Choice(name='歐氣榜', value=2)])
    async def leaderboard(self, i: Interaction, type: int):
        await i.response.defer()
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        c: aiosqlite.Cursor = await self.bot.db.cursor()
        await c.execute('SELECT uid FROM genshin_accounts WHERE user_id = ?', (i.user.id,))
        uid = await c.fetchone()
        if uid is not None:
            try:
                await self.bot.enka_client.set_language('cht')
                data: EnkaNetworkResponse = await self.bot.enka_client.fetch_user(uid[0])
            except:
                pass
            else:
                achievement = data.player.achievement
                await c.execute('INSERT INTO leaderboard (user_id, achievements) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET user_id = ?, achievements = ?', (i.user.id, achievement, i.user.id, achievement))
                if data.characters is not None:
                    for character in data.characters:
                        for artifact in filter(lambda x: x.type == EquipmentsType.ARTIFACT, character.equipments):
                            for substat in artifact.detail.substats:
                                await c.execute('SELECT sub_stat_value FROM substat_leaderboard WHERE sub_stat = ? AND user_id = ?', (substat.prop_id, i.user.id))
                                sub_stat_value = await c.fetchone()
                                if sub_stat_value is None or float(str(sub_stat_value[0]).replace('%', '')) < substat.value:
                                    await c.execute('INSERT INTO substat_leaderboard (user_id, avatar_id, artifact_name, equip_type, sub_stat, sub_stat_value) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (user_id, sub_stat) DO UPDATE SET avatar_id = ?, artifact_name = ?, equip_type = ?, sub_stat_value = ? WHERE user_id = ? AND sub_stat = ?', (i.user.id, character.id, artifact.detail.name, artifact.detail.artifact_type, substat.prop_id, f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}", character.id, artifact.detail.name, artifact.detail.artifact_type, f"{substat.value}{'%' if substat.type == DigitType.PERCENT else ''}", i.user.id, substat.prop_id))

        if type == 0:
            await c.execute('SELECT user_id, achievements FROM leaderboard')
            leaderboard = await c.fetchall()
            leaderboard.sort(key=lambda index: index[1], reverse=True)
            user_rank = rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            embeds = []
            rank = 1
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    member = i.guild.get_member(tuple[0])
                    if member is None:
                        continue
                    message += f'{rank}. {member.display_name} - {tuple[1]}\n'
                    rank += 1
                embed = default_embed(
                    f'🏆 {text_map.get(251, i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: #{user_rank or text_map.get(253, i.locale, user_locale)})', message)
                embeds.append(embed)
            try:
                await GeneralPaginator(i, embeds).start(embeded=True, follow_up=True)
            except ValueError:
                await i.followup.send(embed=error_embed().set_author(name=text_map.get(254, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)

        elif type == 1:
            view = ArtifactLeaderboard.View(
                i.user, self.bot.db, i.locale, user_locale)
            await i.followup.send(embed=default_embed().set_author(name=text_map.get(255, i.locale, user_locale), icon_url=i.user.avatar), view=view)
            await view.wait()
            await c.execute('SELECT * FROM substat_leaderboard WHERE sub_stat = ?', (view.sub_stat,))
            leaderboard = await c.fetchall()
            leaderboard.sort(key=lambda index: float(
                str(index[5]).replace('%', '')), reverse=True)
            user_rank = rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            rank = 1
            embeds = []
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    user_id = tuple[0]
                    avatar_id = tuple[1]
                    artifact_name = tuple[2]
                    equip_type = tuple[3]
                    sub_stat_value = tuple[5]
                    member = i.guild.get_member(user_id)
                    if member is None:
                        continue
                    message += f'{rank}. {get_character(avatar_id)["emoji"]} {get_artifact(name=artifact_name)["emoji"]} {equip_types.get(equip_type)} {member.display_name} • {sub_stat_value}\n\n'
                    rank += 1
                embed = default_embed(
                    f'🏆 {text_map.get(256, i.locale, user_locale)} - {text_map.get(fight_prop.get(view.sub_stat)["text_map_hash"], i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: #{user_rank})', message)
                embeds.append(embed)
            try:
                await GeneralPaginator(i, embeds, [ArtifactLeaderboard.GoBack(c, text_map.get(282, i.locale, user_locale), self.bot.db)]).start(embeded=True, edit_original_message=True)
            except ValueError:
                await i.followup.send(embed=error_embed().set_author(name=text_map.get(254, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)

        elif type == 2:
            player = GGanalysislib.PityGacha()
            await c.execute('SELECT DISTINCT user_id FROM wish_history')
            result = await c.fetchall()
            data = {}
            for index, tuple in enumerate(result):
                get_num, use_pull, left_pull, up_guarantee = await WishCog.char_banner_calc(self, tuple[0], True)
                if tuple[0] in data:
                    continue
                data[tuple[0]] = 100*player.luck_evaluate(
                    get_num=get_num, use_pull=use_pull, left_pull=left_pull)
            leaderboard = list(
                sorted(data.items(), key=lambda item: item[1], reverse=True))
            user_rank = rank_user(i.user.id, leaderboard)
            leaderboard = divide_chunks(leaderboard, 10)
            embeds = []
            rank = 1
            for small_leaderboard in leaderboard:
                message = ''
                for index, tuple in enumerate(small_leaderboard):
                    member = i.guild.get_member(tuple[0])
                    if member is None:
                        continue
                    message += f'{rank}. {member.display_name} - {round(tuple[1], 2)}%\n'
                    rank += 1
                embed = default_embed(
                    f'🏆 {text_map.get(257, i.locale, user_locale)} ({text_map.get(252, i.locale, user_locale)}: #{user_rank})', message)
                embeds.append(embed)
            try:
                await GeneralPaginator(i, embeds).start(embeded=True, follow_up=True)
            except ValueError:
                await i.followup.send(embed=error_embed().set_author(name=text_map.get(254, i.locale, user_locale), icon_url=i.user.avatar), ephemeral=True)

    @app_commands.command(name='wiki原神百科', description='原神百科')
    @app_commands.rename(type='分類')
    @app_commands.describe(type='選擇要查看的維基百科分類')
    @app_commands.choices(type=[Choice(name='角色', value=0)])
    async def wiki(self, i: Interaction, type: int):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        user_locale = user_locale or i.locale
        ambr_top_locale = to_ambr_top(user_locale)
        if type == 0:
            async with self.bot.session.get(f'https://api.ambr.top/v2/{ambr_top_locale}/avatar') as resp:
                data = await resp.json()
            view = CharacterWiki.View(data, i.user, self.bot.db)
            await i.response.send_message(view=view)
            await view.wait()
            async with self.bot.session.get(f'https://api.ambr.top/v2/{ambr_top_locale}/avatar/{view.avatar_id}') as resp:
                avatar = await resp.json()
            avatar_data = avatar["data"]
            embeds = []
            options = []
            embed = default_embed(
                f"{elements.get(avatar['data']['element'])} {avatar['data']['name']}")
            embed.add_field(
                name=text_map.get(315, i.locale, user_locale),
                value=f'{text_map.get(316, i.locale, user_locale)}: {avatar_data["birthday"][0]}/{avatar_data["birthday"][1]}\n'
                f'{text_map.get(317, i.locale, user_locale)}: {avatar_data["fetter"]["title"]}\n'
                f'*{avatar_data["fetter"]["detail"]}*\n'
                f'{text_map.get(318, i.locale, user_locale)}: {avatar_data["fetter"]["constellation"]}\n'
                f'{text_map.get(319, i.locale, user_locale)}: {avatar_data["other"]["nameCard"]["name"] if "name" in avatar_data["other"]["nameCard"]else "???"}\n'
            )
            embed.set_image(
                url=f'https://api.ambr.top/assets/UI/namecard/{avatar_data["other"]["nameCard"]["icon"].replace("Icon", "Pic")}_P.png')
            embed.set_thumbnail(
                url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'))
            embeds.append(embed)
            options.append(SelectOption(label=embed.fields[0].name, value=0))
            embed = default_embed().set_author(
                name=text_map.get(310, i.locale, user_locale), icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'))
            for promoteLevel in avatar_data['upgrade']['promote'][1:]:
                value = ''
                for item_id, item_count in promoteLevel['costItems'].items():
                    value += f'{(get_material(id=item_id))["emoji"]} x{item_count}\n'
                value += f'<:202:991561579218878515> x{promoteLevel["coinCost"]}\n'
                embed.add_field(
                    name=f'{text_map.get(311, i.locale, user_locale)} lvl.{promoteLevel["unlockMaxLevel"]}',
                    value=value,
                    inline=True
                )
            embeds.append(embed)
            options.append(SelectOption(label=text_map.get(
                310, i.locale, user_locale), value=1))
            for talent_id, talent_info in avatar_data["talent"].items():
                max = 3
                if view.avatar_id == '10000002' or view.avatar_id == '10000041':
                    max = 4
                if int(talent_id) <= max:
                    embed = default_embed().set_author(
                        name=text_map.get(94, i.locale, user_locale), icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'))
                    embed.add_field(
                        name=talent_info['name'],
                        value=parse_HTML(
                            talent_info["description"]),
                        inline=False
                    )
                    material_embed = default_embed().set_author(
                        name=text_map.get(312, i.locale, user_locale), icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'))
                    for level, promote_info in talent_info['promote'].items():
                        if level == '1' or int(level) > 10:
                            continue
                        value = ''
                        for item_id, item_count in promote_info['costItems'].items():
                            value += f'{(get_material(id=item_id))["emoji"]} x{item_count}\n'
                        value += f'<:202:991561579218878515> x{promote_info["coinCost"]}\n'
                        material_embed.add_field(
                            name=f'{text_map.get(314, i.locale, user_locale)} lvl.{level}',
                            value=value,
                            inline=True
                        )
                    embed.set_thumbnail(
                        url=f'https://api.ambr.top/assets/UI/{talent_info["icon"]}.png')
                    embeds.append(embed)
                else:
                    embed = default_embed().set_author(
                        name=text_map.get(313, i.locale, user_locale), icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'))
                    embed.add_field(
                        name=talent_info['name'],
                        value=parse_HTML(
                            talent_info["description"]),
                        inline=False
                    )
                    embed.set_thumbnail(
                        url=f'https://api.ambr.top/assets/UI/{talent_info["icon"]}.png')
                    embeds.append(embed)
            options.append(SelectOption(label=text_map.get(
                94, i.locale, user_locale), value=2))
            options.append(SelectOption(
                label=text_map.get(313, i.locale, user_locale), value=5 if max == 3 else 6))
            const_count = 1
            for const_id, const_info in avatar_data['constellation'].items():
                embed = default_embed().set_author(
                    name=f'{text_map.get(318, i.locale, user_locale)} {const_count}', icon_url=(f'https://api.ambr.top/assets/UI/{avatar_data["icon"]}.png'))
                embed.add_field(
                    name=const_info['name'],
                    value=parse_HTML(
                        const_info['description'])
                )
                embed.set_thumbnail(
                    url=f'https://api.ambr.top/assets/UI/{const_info["icon"]}.png')
                embeds.append(embed)
                const_count += 1
            options.append(SelectOption(
                label=text_map.get(318, i.locale, user_locale), value=8 if max == 3 else 9))
            await GeneralPaginator(i, embeds, [CharacterWiki.ShowTalentMaterials(material_embed, text_map.get(312, i.locale, user_locale)), CharacterWiki.QuickNavigation(options, text_map.get(315, i.locale, user_locale))]).start(embeded=True, edit_original_message=True)

    @app_commands.command(name='activity歷來活動', description='查看原神歷來活動數據')
    @app_commands.rename(member='其他人', custom_uid='uid')
    @app_commands.describe(member='查看其他群友的資料', custom_uid='欲查詢玩家的 UID，如果已註冊過則不用填')
    async def activity(self, i: Interaction, member: User = None, custom_uid: int = None):
        member = member or i.user
        result, success = await self.genshin_app.get_activities(member.id, custom_uid, i.locale)
        if not success:
            return await i.response.send_message(embed=result, ephemeral=True)
        await GeneralPaginator(i, result).start(embeded=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GenshinCog(bot))
