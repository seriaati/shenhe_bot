from typing import Any

import aiosqlite
from debug import DefaultView
from discord import Interaction, Locale, SelectOption, app_commands
from discord.ext import commands
from discord.ui import Select
from utility.utils import defaultEmbed, TextMap


class OthersCog(commands.Cog, name='others'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.textMap = TextMap(self.bot.db)
        
    class LangView(DefaultView):
        def __init__(self, locale: Locale, db: aiosqlite.Connection, user_locale: str):
            super().__init__(timeout=None)
            self.db = db
            self.textMap = TextMap(self.db)
            self.add_item(OthersCog.LangSelect(locale, self.textMap, user_locale))
        
    class LangSelect(Select):
        def __init__(self, locale: Locale, textMap: TextMap, user_locale: str):
            lang_options = {
                'none': {
                    'name': textMap.get(124, locale, user_locale),
                    'emoji': '🏳️'
                },
                'zh-TW': {
                    'name': '繁體中文 | 100%',
                    'emoji': '🇹🇼'
                },
                'en-US': {
                    'name': 'English (US) | 70%',
                    'emoji': '🇺🇸'
                },
                'ja': {
                    'name': '日本語 | 5%',
                    'emoji': '🇯🇵'
                },
                'de': {
                    'name': 'deutsch | 5%',
                    'emoji': '🇩🇪'
                },
                'es-ES': {
                    'name': 'español/española | 5%',
                    'emoji': '🇪🇸'
                },
                'fr': {
                    'name': 'français/française | 5%',
                    'emoji': '🇫🇷'
                },
                'ko': {
                    'name': '한국어 | 5%',
                    'emoji': '🇰🇷'
                },
                'pt-BR': {
                    'name': 'português | 5%',
                    'emoji': '🇧🇷'
                },
                'ru': {
                    'name': 'русский | 5%',
                    'emoji': '🇷🇺'
                },
                'th': {
                    'name': 'แบบไทย | 5%',
                    'emoji': '🇹🇭'
                },
                'vi': {
                    'name': 'Tiếng Việt | 5%',
                    'emoji': '🇻🇳'
                },
                'zh-CN': {
                    'name': '简体中文 | 5%',
                    'emoji': '🇨🇳'
                }
                    
            }
            options = []
            for lang, lang_info in lang_options.items():
                options.append(SelectOption(label=lang_info['name'], value=lang, emoji=lang_info['emoji']))
            super().__init__(options=options, placeholder=textMap.get(32, locale, user_locale))
            self.locale = locale
            
        async def callback(self, i: Interaction) -> Any:
            c: aiosqlite.Cursor = await self.view.db.cursor()
            if self.values[0] == 'none':
                await c.execute('DELETE FROM user_lang WHERE user_id = ?', (i.user.id,))
            else:
                await c.execute('INSERT INTO user_lang (user_id, lang) VALUES (?, ?) ON CONFLICT (user_id) DO UPDATE SET lang = ? WHERE user_id = ?', (i.user.id, self.values[0], self.values[0], i.user.id))
            await self.view.db.commit()
            current_language = ''
            lang_flag = ''
            for option in self.options:
                if option.value == self.values[0]:
                    lang_flag = option.emoji
                    current_language = option.label
                    break
            user_locale = await self.view.textMap.getUserLocale(i.user.id)
            await i.response.edit_message(embed=defaultEmbed(message=f"{self.view.textMap.get(34, self.locale, user_locale)}: {lang_flag} {current_language}").set_author(name=(self.view.textMap.get(33, self.locale, user_locale)), icon_url=i.user.avatar), view=None)
        
    @app_commands.command(name='lang語言', description='更改申鶴回覆你的語言')
    async def lang(self, i: Interaction):
        user_locale = await self.textMap.getUserLocale(i.user.id)
        await i.response.send_message(view=OthersCog.LangView(i.locale, self.bot.db, user_locale), ephemeral=True)
    
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OthersCog(bot))