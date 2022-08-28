from typing import Any
import aiosqlite
from discord import Interaction, Locale, SelectOption
from debug import DefaultView
from discord.ui import Select
from apps.text_map.text_map_app import text_map
from apps.text_map.utils import get_user_locale
from utility.utils import default_embed
import config

class View(DefaultView):
    def __init__(self, locale: Locale, user_locale: str, db: aiosqlite.Connection):
        super().__init__(timeout=config.short_timeout)
        self.db = db
        self.add_item(LangSelect(locale, user_locale))
    
class LangSelect(Select):
    def __init__(self, locale: Locale, user_locale: str):
        lang_options = {
            'none': {
                'name': text_map.get(124, locale, user_locale),
                'emoji': '🏳️'
            },
            'zh-TW': {
                'name': '繁體中文 | 100%',
                'emoji': '🇹🇼'
            },
            'en-US': {
                'name': 'English (US) | 100%',
                'emoji': '🇺🇸'
            },
            'ja': {
                'name': '日本語 | 100%',
                'emoji': '🇯🇵'
            },
            'zh-CN': {
                'name': '简体中文 | 23%',
                'emoji': '🇨🇳'
            },
            'de': {
                'name': 'deutsch | 0%',
                'emoji': '🇩🇪'
            },
            'es-ES': {
                'name': 'español/española | 0%',
                'emoji': '🇪🇸'
            },
            'fr': {
                'name': 'français/française | 0%',
                'emoji': '🇫🇷'
            },
            'ko': {
                'name': '한국어 | 0%',
                'emoji': '🇰🇷'
            },
            'pt-BR': {
                'name': 'português | 0%',
                'emoji': '🇧🇷'
            },
            'ru': {
                'name': 'русский | 0%',
                'emoji': '🇷🇺'
            },
            'th': {
                'name': 'แบบไทย | 5%',
                'emoji': '🇹🇭'
            },
            'vi': {
                'name': 'Tiếng Việt | 0%',
                'emoji': '🇻🇳'
            }
                
        }
        options = []
        for lang, lang_info in lang_options.items():
            options.append(SelectOption(label=lang_info['name'], value=lang, emoji=lang_info['emoji']))
        super().__init__(options=options, placeholder=text_map.get(32, locale, user_locale))
        self.locale = locale
        
    async def callback(self, i: Interaction) -> Any:
        self.view: View
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
        user_locale = await get_user_locale(i.user.id, self.view.db)
        await i.response.edit_message(embed=default_embed(message=f"{text_map.get(34, self.locale, user_locale)}: {lang_flag} {current_language}").set_author(name=(text_map.get(33, self.locale, user_locale)), icon_url=i.user.display_avatar.url), view=None)