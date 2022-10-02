import discord


FONTS = {
    'zh-CN': 'NotoSansSC-Regular.otf',
    'zh-TW': 'NotoSansTC-Regular.otf',
    'de': 'NotoSans-Regular.ttf',
    'en-US': 'NotoSans-Regular.ttf',
    'es-ES': 'NotoSans-Regular.ttf',
    'fr': 'NotoSans-Regular.ttf',
    'ja': 'NotoSansJP-Regular.otf',
    'ko': 'NotoSansKR-Regular.otf',
    'th': 'NotoSansThai-Regular.ttf',
    'pt-BR': 'NotoSans-Regular.ttf',
    'ru': 'NotoSans-Regular.ttf',
    'vi': 'NotoSans-Regular.ttf'
}

def get_font(locale: discord.Locale | str):
    return FONTS.get(str(locale)) or 'NotoSans-Regular.ttf'