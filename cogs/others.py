import importlib
import json
import sys

from discord import Interaction, app_commands
from discord.ext import commands
from apps.text_map.convert_locale import to_ambr_top_dict
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import default_embed, error_embed
from UI_elements.others import ChangeLang


class OthersCog(commands.Cog, name='others'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name='lang語言', description='更改申鶴回覆你的語言')
    async def lang(self, i: Interaction):
        user_locale = await get_user_locale(i.user.id, self.bot.db)
        embed = default_embed(message=f'{text_map.get(125, i.locale, user_locale)}\n'
                              f'{text_map.get(126, i.locale, user_locale)}\n'
                              f'{text_map.get(127, i.locale, user_locale)}')
        embed.set_author(name='更改語言', icon_url=i.user.avatar)
        await i.response.send_message(embed=embed, view=ChangeLang.View(i.locale, user_locale, self.bot.db), ephemeral=True)

    @app_commands.command(name='update更新', description='更新原神資料（管理員用）')
    async def update(self, i: Interaction):
        if i.user.id != 410036441129943050:
            return await i.response.send_message(embed=error_embed(message='你不是小雪本人').set_author(name='生物驗證失敗', icon_url=i.user.avatar), ephemeral=True)
        await i.response.send_message(embed=default_embed().set_author(name='更新資料開始', icon_url=i.user.avatar))
        things_to_update = ['avatar', 'weapon', 'material']
        for thing in things_to_update:
            dict = {}
            for lang in list(to_ambr_top_dict.values()):
                async with self.bot.session.get(f'https://api.ambr.top/v2/{lang}/{thing}') as r:
                    data = await r.json()
                for character_id, character_info in data['data']['items'].items():
                    if character_id not in dict:
                        dict[character_id] = {}
                    dict[character_id][lang] = character_info['name']
            with open(f'utility/apps/text_map/maps/{thing}.json', 'w+') as f:
                json.dump(dict, f, indent=4)

        dict = {}
        for lang in list(to_ambr_top_dict.values()):
            async with self.bot.session.get(f'https://api.ambr.top/v2/{lang}/dailyDungeon') as r:
                data = await r.json()
            for weekday, domains in data['data'].items():
                for domain, domain_info in domains.items():
                    if str(domain_info['id']) not in dict:
                        dict[str(domain_info['id'])] = {}
                    dict[str(domain_info['id'])][lang] = domain_info['name']
        with open(f'utility/apps/text_map/maps/dailyDungeon.json', 'w+') as f:
            json.dump(dict, f, indent=4)

        await i.edit_original_message(embed=default_embed().set_author(name='更新資料完畢', icon_url=i.user.avatar))

    @app_commands.command(name='reload重整', description='重整某個 module（管理員用）')
    @app_commands.rename(module_name='名稱')
    async def realod(self, i: Interaction, module_name: str):
        try:
            importlib.reload(sys.modules[module_name])
        except KeyError:
            return await i.response.send_message(embed=error_embed(message=module_name).set_author(name='查無 module', icon_url=i.user.avatar), ephemeral=True)
        else:
            return await i.response.send_message(embed=default_embed(message=module_name).set_author(name='重整成功', icon_url=i.user.avatar), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OthersCog(bot))
